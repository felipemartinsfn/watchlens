from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from app.core.database import get_db
from app.models.watch import WatchReference, Collection, Brand
from app.schemas.watch import ImageSearchResponse, SimilarWatchResult
from app.services import search_service, embedding_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_BYTES = 10 * 1024 * 1024  # 10MB


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

    # Generate embedding for uploaded image
    query_embedding = embedding_service.get_image_embedding(image_bytes)

    # Load all watch embeddings (for small DB; use pgvector ANN for large scale)
    candidates = (
        db.query(WatchReference.id, WatchReference.embedding)
        .filter(WatchReference.is_published == True, WatchReference.embedding != None)
        .all()
    )

    if not candidates:
        return ImageSearchResponse(best_match=None, similar_watches=[], query_processed=True)

    similar = embedding_service.find_similar(
        query_embedding,
        [(c.id, c.embedding) for c in candidates],
        top_k=20,
        min_score=55.0,
    )

    if not similar:
        return ImageSearchResponse(best_match=None, similar_watches=[], query_processed=True)

    top_ids = [s["id"] for s in similar]
    score_map = {s["id"]: s["score"] for s in similar}

    watches = (
        db.query(WatchReference)
        .options(joinedload(WatchReference.collection).joinedload(Collection.brand))
        .filter(WatchReference.id.in_(top_ids))
        .all()
    )
    watch_map = {w.id: w for w in watches}

    results = []
    for s in similar:
        w = watch_map.get(s["id"])
        if w:
            card = search_service.build_card(w)
            card.similarity_score = s["score"]
            results.append(SimilarWatchResult(watch=card, score=s["score"]))

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
