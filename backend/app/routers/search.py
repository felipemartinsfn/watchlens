from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from app.core.database import get_db
from app.models.watch import WatchReference, Collection, Brand
from app.schemas.watch import ImageSearchResponse, SimilarWatchResult
from app.services import search_service, embedding_service
from app.services import watch_features_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_BYTES = 10 * 1024 * 1024  # 10MB

# How many CLIP candidates to pass into the re-ranker before final top_k cut
RERANK_POOL = 40


@router.post("/image", response_model=ImageSearchResponse)
async def search_by_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Use JPEG, PNG or WebP."
        )

    image_bytes = await file.read()
    if len(image_bytes) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="File too large. Maximum 10MB.")

    # 1. Generate CLIP embedding for uploaded image
    query_embedding = embedding_service.get_image_embedding(image_bytes)

    # 2. Load all published watch embeddings (CLIP pass)
    candidates = (
        db.query(WatchReference.id, WatchReference.embedding)
        .filter(WatchReference.is_published == True, WatchReference.embedding != None)
        .all()
    )

    if not candidates:
        return ImageSearchResponse(best_match=None, similar_watches=[], query_processed=True)

    # 3. CLIP similarity — get a wider pool for re-ranking
    clip_results = embedding_service.find_similar(
        query_embedding,
        [(c.id, c.embedding) for c in candidates],
        top_k=RERANK_POOL,
        min_score=50.0,  # Lower threshold here; re-ranker will filter/reorder
    )

    if not clip_results:
        return ImageSearchResponse(best_match=None, similar_watches=[], query_processed=True)

    pool_ids = [r["id"] for r in clip_results]

    # 4. Load full watch data for the pool (for structural features)
    pool_watches = (
        db.query(WatchReference)
        .options(joinedload(WatchReference.collection).joinedload(Collection.brand))
        .filter(WatchReference.id.in_(pool_ids))
        .all()
    )
    watch_map = {w.id: w for w in pool_watches}

    # 5. Pre-compute structural feature vectors for pool candidates
    candidate_features = {}
    for wid in pool_ids:
        w = watch_map.get(wid)
        if w:
            candidate_features[wid] = watch_features_service.compute_candidate_features(w)

    # 6. Hybrid re-ranking: CLIP score × structural feature score
    reranked = watch_features_service.rerank(
        query_embedding=query_embedding,
        clip_results=clip_results,
        candidate_features=candidate_features,
    )

    # 7. Take top 20 with minimum hybrid score of 40
    final = [r for r in reranked if r["score"] >= 40.0][:20]

    if not final:
        return ImageSearchResponse(best_match=None, similar_watches=[], query_processed=True)

    # 8. Build response
    results = []
    for item in final:
        w = watch_map.get(item["id"])
        if w:
            card = search_service.build_card(w)
            card.similarity_score = item["score"]
            results.append(SimilarWatchResult(watch=card, score=item["score"]))
            logger.debug(
                f"  {w.name}: hybrid={item['score']} "
                f"clip={item['clip_score']} feat={item['feature_score']}"
            )

    best_match = results[0] if results else None
    similar_watches = results[1:] if len(results) > 1 else []

    return ImageSearchResponse(
        best_match=best_match,
        similar_watches=similar_watches,
        query_processed=True,
    )


@router.get("/autocomplete")
def autocomplete(
    q: str = Query(..., min_length=1),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Returns autocomplete suggestions for brands, collections and references."""
    q_lower = f"%{q.lower()}%"

    brands = (
        db.query(Brand.id, Brand.name, Brand.slug)
        .filter(Brand.name.ilike(q_lower))
        .limit(4)
        .all()
    )
    collections = (
        db.query(Collection.id, Collection.name, Collection.slug, Brand.name.label("brand_name"))
        .join(Brand, Collection.brand_id == Brand.id)
        .filter(Collection.name.ilike(q_lower))
        .limit(4)
        .all()
    )
    references = (
        db.query(
            WatchReference.id, WatchReference.name, WatchReference.slug,
            WatchReference.reference_number,
            Brand.name.label("brand_name")
        )
        .join(Collection, WatchReference.collection_id == Collection.id)
        .join(Brand, Collection.brand_id == Brand.id)
        .filter(
            WatchReference.is_published == True,
            (WatchReference.name.ilike(q_lower)) | (WatchReference.reference_number.ilike(q_lower))
        )
        .limit(6)
        .all()
    )

    suggestions = []
    for b in brands:
        suggestions.append({"type": "brand", "id": b.id, "label": b.name, "slug": b.slug})
    for c in collections:
        suggestions.append({
            "type": "collection", "id": c.id,
            "label": f"{c.brand_name} {c.name}", "slug": c.slug
        })
    for r in references:
        label = f"{r.brand_name} {r.name}"
        if r.reference_number:
            label += f" ({r.reference_number})"
        suggestions.append({"type": "watch", "id": r.id, "label": label, "slug": r.slug})

    return {"suggestions": suggestions[:limit]}
