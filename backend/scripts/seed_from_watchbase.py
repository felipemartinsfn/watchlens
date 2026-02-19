"""
Seeds the database from watchbase_catalog.json (output of scrape_watchbase.py).
Clears existing data and rebuilds from scratch.

Run: python scripts/seed_from_watchbase.py
"""
import sys, os, re, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal, engine, Base
from app.models.watch import Brand, Collection, WatchReference, WatchImage, WatchTag


# ─── Brand metadata ────────────────────────────────────────────────────────────
BRAND_META = {
    "rolex":               {"name": "Rolex",               "country": "Switzerland", "founded_year": 1905},
    "omega":               {"name": "Omega",               "country": "Switzerland", "founded_year": 1848},
    "patek-philippe":      {"name": "Patek Philippe",      "country": "Switzerland", "founded_year": 1839},
    "audemars-piguet":     {"name": "Audemars Piguet",     "country": "Switzerland", "founded_year": 1875},
    "tudor":               {"name": "Tudor",               "country": "Switzerland", "founded_year": 1926},
    "seiko":               {"name": "Seiko",               "country": "Japan",       "founded_year": 1881},
    "grand-seiko":         {"name": "Grand Seiko",         "country": "Japan",       "founded_year": 1960},
    "iwc":                 {"name": "IWC Schaffhausen",    "country": "Switzerland", "founded_year": 1868},
    "cartier":             {"name": "Cartier",             "country": "France",      "founded_year": 1847},
    "tag-heuer":           {"name": "TAG Heuer",           "country": "Switzerland", "founded_year": 1860},
    "longines":            {"name": "Longines",            "country": "Switzerland", "founded_year": 1832},
    "breitling":           {"name": "Breitling",           "country": "Switzerland", "founded_year": 1884},
    "panerai":             {"name": "Panerai",             "country": "Italy",       "founded_year": 1860},
    "jaeger-lecoultre":    {"name": "Jaeger-LeCoultre",    "country": "Switzerland", "founded_year": 1833},
    "a-lange-sohne":       {"name": "A. Lange & Söhne",   "country": "Germany",     "founded_year": 1845},
    "nomos-glashutte":     {"name": "Nomos Glashütte",     "country": "Germany",     "founded_year": 1990},
    "vacheron-constantin": {"name": "Vacheron Constantin", "country": "Switzerland", "founded_year": 1755},
    "zenith":              {"name": "Zenith",              "country": "Switzerland", "founded_year": 1865},
    "hublot":              {"name": "Hublot",              "country": "Switzerland", "founded_year": 1980},
}


# ─── Spec parsers ──────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def parse_float(val: str | None) -> float | None:
    if not val:
        return None
    m = re.search(r"[\d.]+", val.replace(",", "."))
    return float(m.group()) if m else None


def parse_int(val: str | None) -> int | None:
    if not val:
        return None
    m = re.search(r"\d+", val)
    return int(m.group()) if m else None


def parse_year(val: str | None) -> int | None:
    if not val:
        return None
    m = re.search(r"\b(19|20)\d{2}\b", val)
    return int(m.group()) if m else None


def infer_movement_type(val: str | None) -> str | None:
    if not val:
        return None
    v = val.lower()
    if "quartz" in v:
        return "quartz"
    if "manual" in v or "hand" in v:
        return "manual"
    if "automatic" in v or "self" in v:
        return "automatic"
    if "solar" in v:
        return "solar"
    return "automatic"


def infer_watch_style(specs: dict, collection_slug: str) -> str:
    coll = collection_slug.lower()
    wr = parse_int(specs.get("W/R", ""))
    bezel = specs.get("Bezel", "").lower()
    movement = specs.get("Movement", "").lower()

    if wr and wr >= 200:
        return "diver"
    if any(x in coll for x in ["pilot", "flieger", "aviator", "mark"]):
        return "pilot"
    if "dive" in bezel or "0-60" in bezel:
        return "diver"
    if any(x in coll for x in ["daytona", "carrera", "monaco", "chrono"]):
        return "racing"
    if any(x in coll for x in ["explorer", "pelagos", "blackbay", "black-bay"]):
        return "sport"
    if any(x in coll for x in ["gmt", "worldtimer"]):
        return "gmt"
    if any(x in coll for x in ["calatrava", "reverso", "tank", "lange", "tangente", "master"]):
        return "dress"
    if "chronograph" in movement or "chrono" in coll:
        return "racing"
    return "sport"


def infer_complications(specs: dict) -> list:
    comps = []
    movement = specs.get("Movement", "").lower()
    name = specs.get("Name", "").lower()
    for key in [movement, name]:
        if "chronograph" in key:
            comps.append("chronograph")
        if "date" in key:
            comps.append("date")
        if "gmt" in key:
            comps.append("gmt")
        if "day" in key and "daytona" not in key:
            comps.append("day")
        if "moon" in key:
            comps.append("moonphase")
        if "power" in key:
            comps.append("power reserve")
        if "tourbillon" in key:
            comps.append("tourbillon")
        if "minute repeater" in key or "repeater" in key:
            comps.append("minute repeater")
    return list(dict.fromkeys(comps))


def infer_bezel_type(bezel_val: str | None) -> str | None:
    if not bezel_val:
        return None
    v = bezel_val.lower()
    if "rotating" in v and "bi" in v:
        return "rotating_bi"
    if "rotating" in v:
        return "rotating_uni"
    if "fixed" in v or not v:
        return "fixed"
    return "fixed"


def infer_gender(specs: dict, name: str = "") -> str:
    gender_val = specs.get("Gender", "").lower()
    diameter = parse_float(specs.get("Diameter"))
    if "ladies" in gender_val or "women" in gender_val or "lady" in gender_val:
        return "ladies"
    if "men" in gender_val or "gents" in gender_val:
        return "mens"
    if diameter and diameter <= 34:
        return "ladies"
    if diameter and diameter >= 40:
        return "mens"
    return "unisex"


def infer_era(year: int | None) -> str:
    if not year:
        return "modern"
    if year < 1980:
        return "vintage"
    if year < 2000:
        return "transitional"
    return "modern"


def infer_case_shape(shape_val: str | None, collection_slug: str) -> str:
    if shape_val:
        v = shape_val.lower()
        if "round" in v or "circular" in v:
            return "round"
        if "rect" in v or "square" in v:
            return "rectangular"
        if "cushion" in v:
            return "cushion"
        if "tonneau" in v:
            return "tonneau"
        if "octag" in v or "royal oak" in collection_slug:
            return "octagonal"
        if "tank" in collection_slug or "reverso" in collection_slug or "santos" in collection_slug:
            return "rectangular"
    coll = collection_slug.lower()
    if "tank" in coll or "reverso" in coll:
        return "rectangular"
    return "round"


def collection_display_name(slug: str) -> str:
    """Convert watchbase collection slug to display name."""
    return slug.replace("-", " ").title()


def build_watch_name(specs: dict, collection_slug: str, ref_slug: str) -> str:
    name = specs.get("Name", "")
    if name:
        return name
    family = specs.get("Family", "")
    if family:
        return family
    return collection_display_name(collection_slug)


# ─── Main seed ─────────────────────────────────────────────────────────────────

def seed():
    catalog_path = os.path.join(os.path.dirname(__file__), "watchbase_catalog.json")
    if not os.path.exists(catalog_path):
        print("❌ watchbase_catalog.json not found. Run scrape_watchbase.py first.")
        sys.exit(1)

    with open(catalog_path) as f:
        catalog = json.load(f)

    print(f"📂 Loaded {len(catalog)} watches from watchbase_catalog.json")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # ── Clear existing data ──────────────────────────────────────────────
        print("🗑️  Clearing existing catalog data...")
        db.query(WatchTag).delete()
        db.query(WatchImage).delete()
        db.query(WatchReference).delete()
        db.query(Collection).delete()
        db.query(Brand).delete()
        db.commit()

        # ── Insert brands ────────────────────────────────────────────────────
        brand_map = {}  # brand_slug → Brand ORM object
        for brand_slug, meta in BRAND_META.items():
            brand = Brand(
                name=meta["name"],
                slug=slugify(meta["name"]),
                country=meta["country"],
                founded_year=meta["founded_year"],
            )
            db.add(brand)
            db.flush()
            brand_map[brand_slug] = brand
        db.flush()

        # ── Insert collections and references ────────────────────────────────
        collection_map = {}  # (brand_slug, coll_slug) → Collection ORM
        slug_set = set()
        inserted = 0
        skipped = 0

        for entry_slug, entry in catalog.items():
            brand_slug = entry.get("brand_slug", "")
            coll_slug = entry.get("collection_slug", "")
            specs = entry.get("specs", {})

            brand = brand_map.get(brand_slug)
            if not brand:
                skipped += 1
                continue

            # Get or create collection
            coll_key = (brand_slug, coll_slug)
            if coll_key not in collection_map:
                coll = Collection(
                    brand_id=brand.id,
                    name=collection_display_name(coll_slug),
                    slug=slugify(f"{brand.slug}-{coll_slug}"),
                )
                db.add(coll)
                db.flush()
                collection_map[coll_key] = coll
            coll = collection_map[coll_key]

            # Build slug — prefer watchbase URL-based slug
            ref_part = entry_slug.split("-")[-1] if "-" in entry_slug else entry_slug
            base_slug = slugify(f"{brand.slug}-{coll_slug}-{ref_part}")
            # Ensure uniqueness
            unique_slug = base_slug
            counter = 2
            while unique_slug in slug_set:
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            slug_set.add(unique_slug)

            # Parse specs
            year_start = parse_year(specs.get("Produced", ""))
            diameter = parse_float(specs.get("Diameter", ""))
            thickness = parse_float(specs.get("Thickness", "") or specs.get("Height", ""))
            lug_width = parse_float(specs.get("Lug Width", "") or specs.get("Lug width", ""))
            water_resistance_str = specs.get("W/R", "") or specs.get("Water Resistance", "")
            water_resistance = parse_int(water_resistance_str)
            caliber = specs.get("Caliber", "") or specs.get("Movement Caliber", "")
            jewels = parse_int(specs.get("Jewels", ""))
            power_reserve = parse_int(specs.get("Power Reserve", ""))
            freq_str = specs.get("Frequency", "") or specs.get("Beat Rate", "")
            frequency = parse_int(freq_str)
            if frequency and frequency < 10000:
                frequency = frequency * 3600  # convert Hz to bph if needed

            movement_raw = specs.get("Movement", "") or specs.get("Caliber", "")
            movement_type = infer_movement_type(movement_raw)

            bezel_val = specs.get("Bezel", "")
            bezel_type = infer_bezel_type(bezel_val)

            shape_val = specs.get("Shape", "")
            case_shape = infer_case_shape(shape_val, coll_slug)

            # "Materials" (plural) = case/bracelet materials; "Material" (singular) = dial material
            case_material = specs.get("Materials", "") or specs.get("Case Material", "")
            dial_color = specs.get("Color", "") or specs.get("Dial Color", "")
            dial_finish = specs.get("Finish", "") or specs.get("Dial Finish", "")
            dial_indices = specs.get("Indexes", "") or specs.get("Indices", "")
            hand_style_raw = specs.get("Hands", "")
            # Normalize hand style
            hand_style = hand_style_raw.lower().split(",")[0].strip() if hand_style_raw else None

            year_start_val = year_start
            era = infer_era(year_start_val)
            gender = infer_gender(specs)
            watch_style = infer_watch_style(specs, coll_slug)
            complications = infer_complications(specs)

            watch_name = build_watch_name(specs, coll_slug, entry_slug)
            reference_number = specs.get("Reference", "") or ""
            # Clean reference number (remove "aka" suffix)
            reference_number = reference_number.split("(")[0].strip()

            primary_img = entry.get("primary_image")
            all_imgs = entry.get("all_images", [])

            ref = WatchReference(
                collection_id=coll.id,
                reference_number=reference_number or None,
                name=watch_name,
                slug=unique_slug,
                production_year_start=year_start_val,
                is_limited_edition="Yes" in specs.get("Limited", "No"),
                case_material=case_material or None,
                case_shape=case_shape,
                case_diameter_mm=diameter,
                case_thickness_mm=thickness,
                lug_width_mm=lug_width,
                water_resistance_m=water_resistance,
                dial_color=dial_color or None,
                dial_style=dial_finish or None,
                dial_indices=dial_indices[:100] if dial_indices else None,
                dial_complications=complications or None,
                bezel_type=bezel_type,
                bezel_style=bezel_val[:100] if bezel_val else None,
                hand_style=hand_style,
                movement_type=movement_type,
                movement_caliber=caliber[:100] if caliber else None,
                movement_jewels=jewels,
                power_reserve_hours=power_reserve,
                frequency_bph=frequency,
                gender=gender,
                watch_style=watch_style,
                era=era,
                primary_image_url=primary_img,
                thumbnail_url=primary_img,
                is_published=True,
                view_count=0,
            )
            db.add(ref)
            db.flush()

            # Images
            for i, img_url in enumerate(all_imgs[:4]):
                db.add(WatchImage(
                    reference_id=ref.id,
                    url=img_url,
                    angle="front" if i == 0 else "detail",
                    is_primary=(i == 0),
                ))

            # Tags
            tags = []
            if watch_style:
                tags.append(watch_style)
            if case_material:
                tags.append(case_material.lower())
            if dial_color:
                tags.append(dial_color.lower())
            for comp in (complications or []):
                tags.append(comp)
            if movement_type:
                tags.append(movement_type)

            for tag in list(dict.fromkeys(tags)):
                db.add(WatchTag(reference_id=ref.id, tag=tag, confidence=1.0))

            inserted += 1

        db.commit()
        count = db.query(WatchReference).count()
        print(f"\n✅ Seed complete!")
        print(f"   {count} watches inserted")
        print(f"   {skipped} skipped (unknown brand)")
        print(f"   {len(collection_map)} collections")
        print(f"   {len(brand_map)} brands")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding database from watchbase catalog...\n")
    seed()
