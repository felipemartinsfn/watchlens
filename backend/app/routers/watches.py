from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from app.core.database import get_db
from app.models.watch import WatchReference, Collection, Brand
from app.schemas.watch import WatchReferenceOut, SearchFilters, SearchResponse, SimilarWatchResult
from app.services import search_service

router = APIRouter(prefix="/watches", tags=["watches"])


@router.get("/", response_model=SearchResponse)
def list_watches(
    q: Optional[str] = Query(None, description="Text search"),
    brand_ids: Optional[str] = Query(None, description="Comma-separated brand IDs"),
    watch_styles: Optional[str] = Query(None),
    eras: Optional[str] = Query(None),
    case_materials: Optional[str] = Query(None),
    dial_colors: Optional[str] = Query(None),
    bezel_types: Optional[str] = Query(None),
    movement_types: Optional[str] = Query(None),
    diameter_min: Optional[float] = Query(None),
    diameter_max: Optional[float] = Query(None),
    year_start: Optional[int] = Query(None),
    year_end: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
):
    def split_ids(s):
        if not s:
            return None
        try:
            return [int(x.strip()) for x in s.split(",") if x.strip()]
        except ValueError:
            return None

    def split_str(s):
        if not s:
            return None
        return [x.strip() for x in s.split(",") if x.strip()]

    filters = SearchFilters(
        query=q,
        brand_ids=split_ids(brand_ids),
        watch_styles=split_str(watch_styles),
        eras=split_str(eras),
        case_materials=split_str(case_materials),
        dial_colors=split_str(dial_colors),
        bezel_types=split_str(bezel_types),
        movement_types=split_str(movement_types),
        diameter_min=diameter_min,
        diameter_max=diameter_max,
        year_start=year_start,
        year_end=year_end,
        page=page,
        per_page=per_page,
    )
    result = search_service.search_watches(db, filters)
    return SearchResponse(**result)


@router.get("/featured", response_model=List)
def get_featured_watches(
    limit: int = Query(12, ge=1, le=48),
    db: Session = Depends(get_db),
):
    """Returns the most-viewed watches for the homepage."""
    rows = (
        db.query(WatchReference.id)
        .filter(WatchReference.is_published == True)
        .order_by(WatchReference.view_count.desc(), WatchReference.id.asc())
        .limit(limit)
        .all()
    )
    ids = [r.id for r in rows]
    ref_map = search_service._load_with_relations(db, ids)
    refs = [ref_map[i] for i in ids if i in ref_map]
    return [search_service.build_card(r) for r in refs]


@router.get("/trending", response_model=List)
def get_trending_watches(
    era: Optional[str] = Query(None),
    style: Optional[str] = Query(None),
    limit: int = Query(8, ge=1, le=24),
    db: Session = Depends(get_db),
):
    q = (
        db.query(WatchReference.id)
        .filter(WatchReference.is_published == True)
    )
    if era:
        q = q.filter(WatchReference.era == era)
    if style:
        q = q.filter(WatchReference.watch_style == style)
    rows = q.order_by(WatchReference.view_count.desc(), WatchReference.id.asc()).limit(limit).all()
    ids = [r.id for r in rows]
    ref_map = search_service._load_with_relations(db, ids)
    refs = [ref_map[i] for i in ids if i in ref_map]
    return [search_service.build_card(r) for r in refs]


@router.get("/{slug}", response_model=WatchReferenceOut)
def get_watch(slug: str, db: Session = Depends(get_db)):
    ref = (
        db.query(WatchReference)
        .options(
            joinedload(WatchReference.collection).joinedload(Collection.brand),
            joinedload(WatchReference.images),
            joinedload(WatchReference.tags),
        )
        .filter(WatchReference.slug == slug, WatchReference.is_published == True)
        .first()
    )
    if not ref:
        raise HTTPException(status_code=404, detail="Watch not found")
    # increment view count
    ref.view_count = (ref.view_count or 0) + 1
    db.commit()
    db.refresh(ref)
    return ref


@router.get("/{slug}/similar", response_model=List[SimilarWatchResult])
def get_similar(
    slug: str,
    limit: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db),
):
    ref = db.query(WatchReference).filter(WatchReference.slug == slug).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Watch not found")
    results = search_service.get_similar_watches(db, ref.id, top_k=limit)
    return [SimilarWatchResult(watch=r["watch"], score=r["score"]) for r in results]
