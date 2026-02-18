from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import distinct, func
from app.core.database import get_db
from app.models.watch import WatchReference, Brand, Collection

router = APIRouter(prefix="/filters", tags=["filters"])


@router.get("/options")
def get_filter_options(db: Session = Depends(get_db)):
    """Returns all available filter values for the UI."""

    def get_distinct(col):
        rows = db.query(distinct(col)).filter(col != None, col != "").all()
        return sorted([r[0] for r in rows if r[0]])

    brands = db.query(Brand.id, Brand.name).order_by(Brand.name).all()

    return {
        "brands": [{"id": b.id, "name": b.name} for b in brands],
        "watch_styles": get_distinct(WatchReference.watch_style),
        "eras": get_distinct(WatchReference.era),
        "case_materials": get_distinct(WatchReference.case_material),
        "dial_colors": get_distinct(WatchReference.dial_color),
        "bezel_types": get_distinct(WatchReference.bezel_type),
        "hand_styles": get_distinct(WatchReference.hand_style),
        "bracelet_types": get_distinct(WatchReference.bracelet_type),
        "movement_types": get_distinct(WatchReference.movement_type),
        "genders": get_distinct(WatchReference.gender),
        "diameter_range": {
            "min": db.query(func.min(WatchReference.case_diameter_mm)).scalar() or 28,
            "max": db.query(func.max(WatchReference.case_diameter_mm)).scalar() or 48,
        },
        "year_range": {
            "min": db.query(func.min(WatchReference.production_year_start)).scalar() or 1950,
            "max": db.query(func.max(WatchReference.production_year_start)).scalar() or 2025,
        },
    }
