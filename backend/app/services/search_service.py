"""
Search service: text search + filter + visual similarity.
"""
from sqlalchemy.orm import Session, joinedload, lazyload
from sqlalchemy import or_, func
from typing import List
from app.models.watch import WatchReference, Collection, Brand
from app.schemas.watch import SearchFilters, WatchReferenceCard
import math


def _load_with_relations(db: Session, ids: list) -> dict:
    """Load WatchReferences with their relations for a list of IDs."""
    if not ids:
        return {}
    refs = (
        db.query(WatchReference)
        .options(joinedload(WatchReference.collection).joinedload(Collection.brand))
        .filter(WatchReference.id.in_(ids))
        .all()
    )
    return {r.id: r for r in refs}


def build_card(ref: WatchReference) -> WatchReferenceCard:
    brand_name = None
    collection_name = None
    if ref.collection:
        collection_name = ref.collection.name
        if ref.collection.brand:
            brand_name = ref.collection.brand.name
    return WatchReferenceCard(
        id=ref.id,
        slug=ref.slug,
        name=ref.name,
        reference_number=ref.reference_number,
        brand_name=brand_name,
        collection_name=collection_name,
        primary_image_url=ref.primary_image_url,
        thumbnail_url=ref.thumbnail_url,
        case_diameter_mm=ref.case_diameter_mm,
        case_material=ref.case_material,
        dial_color=ref.dial_color,
        watch_style=ref.watch_style,
        era=ref.era,
        production_year_start=ref.production_year_start,
        production_year_end=ref.production_year_end,
        movement_type=ref.movement_type,
    )


def search_watches(db: Session, filters: SearchFilters):
    # Base query — only select IDs + sort field to avoid subquery issues
    id_query = (
        db.query(WatchReference.id, WatchReference.view_count)
        .join(Collection, WatchReference.collection_id == Collection.id)
        .join(Brand, Collection.brand_id == Brand.id)
        .filter(WatchReference.is_published == True)
    )

    if filters.query:
        q = f"%{filters.query.lower()}%"
        id_query = id_query.filter(
            or_(
                func.lower(WatchReference.name).like(q),
                func.lower(WatchReference.reference_number).like(q),
                func.lower(Brand.name).like(q),
                func.lower(Collection.name).like(q),
            )
        )

    if filters.brand_ids:
        id_query = id_query.filter(Brand.id.in_(filters.brand_ids))
    if filters.collection_ids:
        id_query = id_query.filter(WatchReference.collection_id.in_(filters.collection_ids))
    if filters.watch_styles:
        id_query = id_query.filter(WatchReference.watch_style.in_(filters.watch_styles))
    if filters.eras:
        id_query = id_query.filter(WatchReference.era.in_(filters.eras))
    if filters.genders:
        id_query = id_query.filter(WatchReference.gender.in_(filters.genders))
    if filters.case_materials:
        id_query = id_query.filter(WatchReference.case_material.in_(filters.case_materials))
    if filters.dial_colors:
        id_query = id_query.filter(WatchReference.dial_color.in_(filters.dial_colors))
    if filters.bezel_types:
        id_query = id_query.filter(WatchReference.bezel_type.in_(filters.bezel_types))
    if filters.hand_styles:
        id_query = id_query.filter(WatchReference.hand_style.in_(filters.hand_styles))
    if filters.bracelet_types:
        id_query = id_query.filter(WatchReference.bracelet_type.in_(filters.bracelet_types))
    if filters.movement_types:
        id_query = id_query.filter(WatchReference.movement_type.in_(filters.movement_types))
    if filters.diameter_min is not None:
        id_query = id_query.filter(WatchReference.case_diameter_mm >= filters.diameter_min)
    if filters.diameter_max is not None:
        id_query = id_query.filter(WatchReference.case_diameter_mm <= filters.diameter_max)
    if filters.year_start is not None:
        id_query = id_query.filter(WatchReference.production_year_start >= filters.year_start)
    if filters.year_end is not None:
        id_query = id_query.filter(WatchReference.production_year_start <= filters.year_end)
    if filters.is_limited_edition is not None:
        id_query = id_query.filter(WatchReference.is_limited_edition == filters.is_limited_edition)
    if filters.complications:
        for comp in filters.complications:
            id_query = id_query.filter(
                WatchReference.dial_complications.like(f'%"{comp}"%')
            )

    total = id_query.count()
    offset = (filters.page - 1) * filters.per_page

    # Get paginated IDs ordered by view_count
    rows = (
        id_query
        .order_by(WatchReference.view_count.desc(), WatchReference.id.asc())
        .offset(offset)
        .limit(filters.per_page)
        .all()
    )
    ids_ordered = [r.id for r in rows]

    # Load full objects with relations (no limit/offset = no subquery issue)
    ref_map = _load_with_relations(db, ids_ordered)
    # Preserve order
    refs = [ref_map[i] for i in ids_ordered if i in ref_map]

    return {
        "results": [build_card(r) for r in refs],
        "total": total,
        "page": filters.page,
        "per_page": filters.per_page,
        "total_pages": math.ceil(total / filters.per_page) if total else 0,
    }


def get_similar_watches(
    db: Session,
    watch_id: int,
    top_k: int = 12,
    min_score: float = 55.0
) -> List[dict]:
    """Find similar watches based on visual embedding + structured attributes."""
    from app.services.embedding_service import cosine_similarity, similarity_to_score

    target = (
        db.query(WatchReference)
        .filter(WatchReference.id == watch_id, WatchReference.is_published == True)
        .first()
    )
    if not target:
        return []

    candidates = (
        db.query(
            WatchReference.id, WatchReference.embedding,
            WatchReference.watch_style, WatchReference.case_diameter_mm,
            WatchReference.dial_color, WatchReference.bezel_type
        )
        .filter(WatchReference.id != watch_id, WatchReference.is_published == True)
        .all()
    )

    results = []
    for c in candidates:
        score = 0.0
        weight_total = 0.0

        # Visual embedding similarity (weight: 70%)
        if target.embedding and c.embedding:
            sim = cosine_similarity(target.embedding, c.embedding)
            emb_score = similarity_to_score(sim)
            score += emb_score * 0.7
            weight_total += 0.7

        # Structured attribute score (weight: 30%)
        attr_score = 0.0
        attr_count = 0

        if target.watch_style and c.watch_style:
            attr_score += 100.0 if target.watch_style == c.watch_style else 0.0
            attr_count += 1
        if target.dial_color and c.dial_color:
            attr_score += 100.0 if target.dial_color == c.dial_color else 30.0
            attr_count += 1
        if target.bezel_type and c.bezel_type:
            attr_score += 100.0 if target.bezel_type == c.bezel_type else 20.0
            attr_count += 1
        if target.case_diameter_mm and c.case_diameter_mm:
            diff = abs(target.case_diameter_mm - c.case_diameter_mm)
            attr_score += max(0, 100 - diff * 10)
            attr_count += 1

        if attr_count > 0:
            attr_avg = attr_score / attr_count
            score += attr_avg * 0.3
            weight_total += 0.3

        final_score = score if weight_total > 0 else 0.0

        if final_score >= min_score:
            results.append({"id": c.id, "score": round(final_score, 1)})

    results.sort(key=lambda x: x["score"], reverse=True)
    top_results = results[:top_k]

    if not top_results:
        return []

    top_ids = [r["id"] for r in top_results]
    score_map = {r["id"]: r["score"] for r in top_results}

    ref_map = _load_with_relations(db, top_ids)

    output = []
    for wid in top_ids:
        w = ref_map.get(wid)
        if w:
            card = build_card(w)
            card.similarity_score = score_map.get(w.id)
            output.append({"watch": card, "score": score_map.get(w.id, 0)})

    output.sort(key=lambda x: x["score"], reverse=True)
    return output
