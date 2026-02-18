from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime


class BrandBase(BaseModel):
    name: str
    slug: str
    country: Optional[str] = None
    founded_year: Optional[int] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None


class BrandOut(BrandBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
    class Config_REMOVED:
        from_attributes = True


class CollectionBase(BaseModel):
    brand_id: int
    name: str
    slug: str
    description: Optional[str] = None
    intro_year: Optional[int] = None


class CollectionOut(CollectionBase):
    id: int
    brand: Optional[BrandOut] = None

    model_config = ConfigDict(from_attributes=True)
    class Config_REMOVED:
        from_attributes = True


class WatchImageOut(BaseModel):
    id: int
    url: str
    angle: Optional[str] = None
    is_primary: bool

    model_config = ConfigDict(from_attributes=True)
    class Config_REMOVED:
        from_attributes = True


class WatchTagOut(BaseModel):
    id: int
    tag: str
    confidence: float

    model_config = ConfigDict(from_attributes=True)
    class Config_REMOVED:
        from_attributes = True


class WatchReferenceBase(BaseModel):
    reference_number: Optional[str] = None
    name: str
    description: Optional[str] = None
    production_year_start: Optional[int] = None
    production_year_end: Optional[int] = None
    is_limited_edition: bool = False
    limited_edition_count: Optional[int] = None
    case_material: Optional[str] = None
    case_shape: Optional[str] = None
    case_diameter_mm: Optional[float] = None
    case_thickness_mm: Optional[float] = None
    lug_width_mm: Optional[float] = None
    water_resistance_m: Optional[int] = None
    dial_color: Optional[str] = None
    dial_style: Optional[str] = None
    dial_indices: Optional[str] = None
    dial_complications: Optional[List[str]] = None
    bezel_type: Optional[str] = None
    bezel_material: Optional[str] = None
    bezel_style: Optional[str] = None
    bezel_insert_color: Optional[str] = None
    hand_style: Optional[str] = None
    hand_lume: bool = False
    movement_type: Optional[str] = None
    movement_caliber: Optional[str] = None
    movement_jewels: Optional[int] = None
    power_reserve_hours: Optional[int] = None
    frequency_bph: Optional[int] = None
    bracelet_type: Optional[str] = None
    bracelet_material: Optional[str] = None
    clasp_type: Optional[str] = None
    gender: Optional[str] = None
    watch_style: Optional[str] = None
    era: Optional[str] = None
    primary_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class WatchReferenceOut(WatchReferenceBase):
    id: int
    slug: str
    collection_id: int
    collection: Optional[CollectionOut] = None
    images: List[WatchImageOut] = []
    tags: List[WatchTagOut] = []
    view_count: int = 0
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
    class Config_REMOVED:
        from_attributes = True


class WatchReferenceCard(BaseModel):
    """Lightweight card for grids and search results"""
    id: int
    slug: str
    name: str
    reference_number: Optional[str] = None
    brand_name: Optional[str] = None
    collection_name: Optional[str] = None
    primary_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    case_diameter_mm: Optional[float] = None
    case_material: Optional[str] = None
    dial_color: Optional[str] = None
    watch_style: Optional[str] = None
    era: Optional[str] = None
    production_year_start: Optional[int] = None
    production_year_end: Optional[int] = None
    movement_type: Optional[str] = None
    similarity_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
    class Config_REMOVED:
        from_attributes = True


class SimilarWatchResult(BaseModel):
    watch: WatchReferenceCard
    score: float = Field(..., ge=0, le=100, description="Similarity score 0-100")


class SearchFilters(BaseModel):
    query: Optional[str] = None
    brand_ids: Optional[List[int]] = None
    collection_ids: Optional[List[int]] = None
    watch_styles: Optional[List[str]] = None
    eras: Optional[List[str]] = None
    genders: Optional[List[str]] = None
    case_materials: Optional[List[str]] = None
    dial_colors: Optional[List[str]] = None
    bezel_types: Optional[List[str]] = None
    hand_styles: Optional[List[str]] = None
    bracelet_types: Optional[List[str]] = None
    movement_types: Optional[List[str]] = None
    complications: Optional[List[str]] = None
    diameter_min: Optional[float] = None
    diameter_max: Optional[float] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    is_limited_edition: Optional[bool] = None
    page: int = 1
    per_page: int = 24


class SearchResponse(BaseModel):
    results: List[WatchReferenceCard]
    total: int
    page: int
    per_page: int
    total_pages: int


class ImageSearchResponse(BaseModel):
    best_match: Optional[SimilarWatchResult] = None
    similar_watches: List[SimilarWatchResult]
    query_processed: bool = True
