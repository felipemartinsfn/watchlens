from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.watch import Brand, Collection
from app.schemas.watch import BrandOut, CollectionOut

router = APIRouter(prefix="/brands", tags=["brands"])


@router.get("/", response_model=List[BrandOut])
def list_brands(db: Session = Depends(get_db)):
    return db.query(Brand).order_by(Brand.name).all()


@router.get("/{slug}", response_model=BrandOut)
def get_brand(slug: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.slug == slug).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.get("/{slug}/collections", response_model=List[CollectionOut])
def get_brand_collections(slug: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.slug == slug).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return (
        db.query(Collection)
        .filter(Collection.brand_id == brand.id)
        .order_by(Collection.name)
        .all()
    )
