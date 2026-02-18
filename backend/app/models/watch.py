from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, JSON,
    ForeignKey, DateTime, func
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    country = Column(String(100))
    founded_year = Column(Integer)
    logo_url = Column(String(500))
    description = Column(Text)

    collections = relationship("Collection", back_populates="brand")
    created_at = Column(DateTime, server_default=func.now())


class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(220), nullable=False, index=True)
    description = Column(Text)
    intro_year = Column(Integer)

    brand = relationship("Brand", back_populates="collections")
    references = relationship("WatchReference", back_populates="collection")
    created_at = Column(DateTime, server_default=func.now())


class WatchReference(Base):
    __tablename__ = "watch_references"

    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False)

    reference_number = Column(String(100), index=True)
    name = Column(String(300), nullable=False)
    slug = Column(String(350), unique=True, nullable=False, index=True)
    description = Column(Text)

    # Production years
    production_year_start = Column(Integer, index=True)
    production_year_end = Column(Integer)  # null = still in production
    is_limited_edition = Column(Boolean, default=False)
    limited_edition_count = Column(Integer)

    # Case
    case_material = Column(String(100), index=True)
    case_shape = Column(String(50), index=True)   # round, rectangular, cushion, tonneau, octagonal
    case_diameter_mm = Column(Float, index=True)
    case_thickness_mm = Column(Float)
    lug_width_mm = Column(Float)
    water_resistance_m = Column(Integer)

    # Dial
    dial_color = Column(String(100), index=True)
    dial_style = Column(String(100))             # sunburst, matte, guilloché, lacquered, fumé
    dial_indices = Column(String(100))           # hour markers, roman, arabic, baton
    dial_complications = Column(JSON)            # ["date", "chronograph", "gmt", ...]

    # Bezel
    bezel_type = Column(String(100), index=True) # fixed, rotating_uni, rotating_bi, none
    bezel_material = Column(String(100))
    bezel_style = Column(String(100))            # smooth, fluted, coin-edge, ceramic
    bezel_insert_color = Column(String(100))

    # Hands
    hand_style = Column(String(100), index=True) # sword, dauphine, baton, cathedral, mercedes, pencil
    hand_lume = Column(Boolean, default=False)

    # Movement
    movement_type = Column(String(50), index=True)  # automatic, manual, quartz, solar
    movement_caliber = Column(String(100))
    movement_jewels = Column(Integer)
    power_reserve_hours = Column(Integer)
    frequency_bph = Column(Integer)

    # Bracelet / Strap
    bracelet_type = Column(String(100), index=True)  # oyster, jubilee, integrated, rubber, leather, nato
    bracelet_material = Column(String(100))
    clasp_type = Column(String(100))

    # Classification
    gender = Column(String(20), index=True)     # mens, ladies, unisex
    watch_style = Column(String(50), index=True) # dress, sport, diver, pilot, field, racing, military, gmt
    era = Column(String(30), index=True)         # vintage, transitional, modern

    # Media
    primary_image_url = Column(String(500))
    thumbnail_url = Column(String(500))

    # Embedding stored as JSON array (for SQLite compat; use pgvector in prod)
    embedding = Column(JSON)  # list of floats

    # Metadata
    is_published = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    collection = relationship("Collection", back_populates="references")
    images = relationship("WatchImage", back_populates="reference", cascade="all, delete-orphan")
    tags = relationship("WatchTag", back_populates="reference", cascade="all, delete-orphan")


class WatchImage(Base):
    __tablename__ = "watch_images"

    id = Column(Integer, primary_key=True, index=True)
    reference_id = Column(Integer, ForeignKey("watch_references.id"), nullable=False)
    url = Column(String(500), nullable=False)
    angle = Column(String(50))  # front, side, back, dial, caseback, wrist
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    reference = relationship("WatchReference", back_populates="images")


class WatchTag(Base):
    __tablename__ = "watch_tags"

    id = Column(Integer, primary_key=True, index=True)
    reference_id = Column(Integer, ForeignKey("watch_references.id"), nullable=False)
    tag = Column(String(200), nullable=False, index=True)
    confidence = Column(Float, default=1.0)

    reference = relationship("WatchReference", back_populates="tags")
