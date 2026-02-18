"""
Seed script: populates the DB with iconic watch references.
Run: python scripts/seed_catalog.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal, engine, Base
from app.models.watch import Brand, Collection, WatchReference, WatchImage
import re


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # ─── BRANDS ───────────────────────────────────────────────────────────
        brands_data = [
            {"name": "Rolex", "country": "Switzerland", "founded_year": 1905},
            {"name": "Omega", "country": "Switzerland", "founded_year": 1848},
            {"name": "Patek Philippe", "country": "Switzerland", "founded_year": 1839},
            {"name": "Audemars Piguet", "country": "Switzerland", "founded_year": 1875},
            {"name": "IWC Schaffhausen", "country": "Switzerland", "founded_year": 1868},
            {"name": "Jaeger-LeCoultre", "country": "Switzerland", "founded_year": 1833},
            {"name": "Tudor", "country": "Switzerland", "founded_year": 1926},
            {"name": "Longines", "country": "Switzerland", "founded_year": 1832},
            {"name": "TAG Heuer", "country": "Switzerland", "founded_year": 1860},
            {"name": "Seiko", "country": "Japan", "founded_year": 1881},
            {"name": "Grand Seiko", "country": "Japan", "founded_year": 1960},
            {"name": "Cartier", "country": "France", "founded_year": 1847},
            {"name": "A. Lange & Söhne", "country": "Germany", "founded_year": 1845},
            {"name": "Vacheron Constantin", "country": "Switzerland", "founded_year": 1755},
            {"name": "Breitling", "country": "Switzerland", "founded_year": 1884},
            {"name": "Panerai", "country": "Italy", "founded_year": 1860},
            {"name": "Zenith", "country": "Switzerland", "founded_year": 1865},
            {"name": "Blancpain", "country": "Switzerland", "founded_year": 1735},
            {"name": "Breguet", "country": "Switzerland", "founded_year": 1775},
            {"name": "Nomos Glashütte", "country": "Germany", "founded_year": 1990},
        ]

        brand_map = {}
        for b in brands_data:
            existing = db.query(Brand).filter(Brand.name == b["name"]).first()
            if not existing:
                brand = Brand(name=b["name"], slug=slugify(b["name"]), **{k: v for k, v in b.items() if k != "name"})
                db.add(brand)
                db.flush()
                brand_map[b["name"]] = brand
            else:
                brand_map[b["name"]] = existing

        db.flush()

        # ─── WATCH DATA ───────────────────────────────────────────────────────
        watches = [
            # ── ROLEX ──
            {
                "brand": "Rolex", "collection": "Submariner",
                "ref": "116610LN", "name": "Submariner Date",
                "year_start": 2010, "year_end": 2020,
                "case_material": "Steel", "case_shape": "round", "diameter": 40.0, "thickness": 12.5, "lug_width": 20.0, "water_resistance": 300,
                "dial_color": "Black", "dial_style": "matte", "dial_indices": "hour markers", "complications": ["date"],
                "bezel_type": "rotating_uni", "bezel_material": "Steel", "bezel_style": "ceramic", "bezel_insert_color": "Black",
                "hand_style": "mercedes", "hand_lume": True,
                "movement_type": "automatic", "caliber": "Cal. 3135", "jewels": 31, "power_reserve": 48, "frequency": 28800,
                "bracelet_type": "oyster", "bracelet_material": "Steel", "clasp_type": "Oysterlock",
                "gender": "mens", "watch_style": "diver", "era": "modern",
                "image": "https://images.unsplash.com/photo-1548171916-c8fd84c32a94?w=600",
            },
            {
                "brand": "Rolex", "collection": "Submariner",
                "ref": "126610LN", "name": "Submariner Date",
                "year_start": 2020,
                "case_material": "Oystersteel", "case_shape": "round", "diameter": 41.0, "thickness": 12.5, "lug_width": 20.0, "water_resistance": 300,
                "dial_color": "Black", "dial_style": "matte", "dial_indices": "hour markers", "complications": ["date"],
                "bezel_type": "rotating_uni", "bezel_material": "Ceramic", "bezel_style": "ceramic", "bezel_insert_color": "Black",
                "hand_style": "mercedes", "hand_lume": True,
                "movement_type": "automatic", "caliber": "Cal. 3235", "jewels": 31, "power_reserve": 70, "frequency": 28800,
                "bracelet_type": "oyster", "bracelet_material": "Oystersteel", "clasp_type": "Oysterlock",
                "gender": "mens", "watch_style": "diver", "era": "modern",
                "image": "https://images.unsplash.com/photo-1523170335258-f5ed11844a49?w=600",
            },
            {
                "brand": "Rolex", "collection": "Datejust",
                "ref": "126300", "name": "Datejust 41",
                "year_start": 2016,
                "case_material": "Oystersteel", "case_shape": "round", "diameter": 41.0, "thickness": 12.0, "lug_width": 20.0, "water_resistance": 100,
                "dial_color": "Silver", "dial_style": "sunburst", "dial_indices": "baton", "complications": ["date"],
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "smooth",
                "hand_style": "baton", "hand_lume": True,
                "movement_type": "automatic", "caliber": "Cal. 3235", "jewels": 31, "power_reserve": 70, "frequency": 28800,
                "bracelet_type": "jubilee", "bracelet_material": "Oystersteel", "clasp_type": "Oysterlock",
                "gender": "mens", "watch_style": "dress", "era": "modern",
                "image": "https://images.unsplash.com/photo-1612817288484-6f916006741a?w=600",
            },
            {
                "brand": "Rolex", "collection": "GMT-Master II",
                "ref": "126710BLRO", "name": "GMT-Master II Pepsi",
                "year_start": 2018,
                "case_material": "Oystersteel", "case_shape": "round", "diameter": 40.0, "thickness": 12.0, "lug_width": 20.0, "water_resistance": 100,
                "dial_color": "Black", "dial_style": "matte", "dial_indices": "hour markers", "complications": ["date", "gmt"],
                "bezel_type": "rotating_bi", "bezel_material": "Ceramic", "bezel_style": "ceramic", "bezel_insert_color": "Red/Blue",
                "hand_style": "mercedes", "hand_lume": True,
                "movement_type": "automatic", "caliber": "Cal. 3285", "jewels": 31, "power_reserve": 70, "frequency": 28800,
                "bracelet_type": "jubilee", "bracelet_material": "Oystersteel", "clasp_type": "Oysterlock",
                "gender": "mens", "watch_style": "sport", "era": "modern",
                "image": "https://images.unsplash.com/photo-1620625515032-6ed0c1790c75?w=600",
            },
            {
                "brand": "Rolex", "collection": "Daytona",
                "ref": "116500LN", "name": "Cosmograph Daytona",
                "year_start": 2016,
                "case_material": "Oystersteel", "case_shape": "round", "diameter": 40.0, "thickness": 12.4, "lug_width": 20.0, "water_resistance": 100,
                "dial_color": "White", "dial_style": "matte", "dial_indices": "arabic", "complications": ["chronograph"],
                "bezel_type": "fixed", "bezel_material": "Ceramic", "bezel_style": "tachymeter",
                "hand_style": "baton", "hand_lume": True,
                "movement_type": "automatic", "caliber": "Cal. 4130", "jewels": 44, "power_reserve": 72, "frequency": 28800,
                "bracelet_type": "oyster", "bracelet_material": "Oystersteel", "clasp_type": "Oysterlock",
                "gender": "mens", "watch_style": "racing", "era": "modern",
                "image": "https://images.unsplash.com/photo-1547996160-81dfa63595aa?w=600",
            },
            {
                "brand": "Rolex", "collection": "Explorer",
                "ref": "214270", "name": "Explorer II",
                "year_start": 2011, "year_end": 2021,
                "case_material": "Oystersteel", "case_shape": "round", "diameter": 42.0, "thickness": 12.6, "lug_width": 21.0, "water_resistance": 100,
                "dial_color": "White", "dial_style": "matte", "dial_indices": "arabic", "complications": ["date", "gmt"],
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "smooth",
                "hand_style": "mercedes", "hand_lume": True,
                "movement_type": "automatic", "caliber": "Cal. 3187", "jewels": 31, "power_reserve": 48, "frequency": 28800,
                "bracelet_type": "oyster", "bracelet_material": "Oystersteel", "clasp_type": "Oysterlock",
                "gender": "mens", "watch_style": "field", "era": "modern",
                "image": "https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=600",
            },
            # ── OMEGA ──
            {
                "brand": "Omega", "collection": "Speedmaster",
                "ref": "311.30.42.30.01.005", "name": "Speedmaster Moonwatch Professional",
                "year_start": 2021,
                "case_material": "Steel", "case_shape": "round", "diameter": 42.0, "thickness": 13.2, "lug_width": 21.0, "water_resistance": 50,
                "dial_color": "Black", "dial_style": "matte", "dial_indices": "arabic", "complications": ["chronograph"],
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "tachymeter",
                "hand_style": "baton", "hand_lume": True,
                "movement_type": "manual", "caliber": "Cal. 3861", "jewels": 18, "power_reserve": 50, "frequency": 21600,
                "bracelet_type": "bracelet", "bracelet_material": "Steel", "clasp_type": "Folding",
                "gender": "mens", "watch_style": "sport", "era": "modern",
                "image": "https://images.unsplash.com/photo-1614164185128-e4ec99c436d7?w=600",
            },
            {
                "brand": "Omega", "collection": "Seamaster",
                "ref": "210.30.42.20.01.001", "name": "Seamaster Diver 300M",
                "year_start": 2018,
                "case_material": "Steel", "case_shape": "round", "diameter": 42.0, "thickness": 13.0, "lug_width": 21.0, "water_resistance": 300,
                "dial_color": "Blue", "dial_style": "wave", "dial_indices": "baton", "complications": ["date"],
                "bezel_type": "rotating_uni", "bezel_material": "Ceramic", "bezel_style": "ceramic", "bezel_insert_color": "Blue",
                "hand_style": "baton", "hand_lume": True,
                "movement_type": "automatic", "caliber": "Cal. 8800", "jewels": 39, "power_reserve": 55, "frequency": 25200,
                "bracelet_type": "bracelet", "bracelet_material": "Steel", "clasp_type": "Folding",
                "gender": "mens", "watch_style": "diver", "era": "modern",
                "image": "https://images.unsplash.com/photo-1526045612212-70caf35c14df?w=600",
            },
            {
                "brand": "Omega", "collection": "Constellation",
                "ref": "131.10.39.20.53.001", "name": "Constellation Co-Axial Master",
                "year_start": 2020,
                "case_material": "Steel", "case_shape": "round", "diameter": 39.0, "thickness": 11.1, "lug_width": 19.0, "water_resistance": 100,
                "dial_color": "Silver", "dial_style": "sunburst", "dial_indices": "baton", "complications": ["date"],
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "claws",
                "hand_style": "sword", "hand_lume": False,
                "movement_type": "automatic", "caliber": "Cal. 8700", "jewels": 39, "power_reserve": 60, "frequency": 25200,
                "bracelet_type": "bracelet", "bracelet_material": "Steel", "clasp_type": "Folding",
                "gender": "unisex", "watch_style": "dress", "era": "modern",
                "image": "https://images.unsplash.com/photo-1633174524827-db00a6b7bc74?w=600",
            },
            # ── PATEK PHILIPPE ──
            {
                "brand": "Patek Philippe", "collection": "Nautilus",
                "ref": "5711/1A-010", "name": "Nautilus",
                "year_start": 2006, "year_end": 2021,
                "case_material": "Steel", "case_shape": "round", "diameter": 40.0, "thickness": 8.3, "lug_width": 19.0, "water_resistance": 120,
                "dial_color": "Blue", "dial_style": "horizontal stripes", "dial_indices": "baton", "complications": ["date"],
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "integrated",
                "hand_style": "baton", "hand_lume": True,
                "movement_type": "automatic", "caliber": "Cal. 324 SC", "jewels": 29, "power_reserve": 45, "frequency": 28800,
                "bracelet_type": "integrated", "bracelet_material": "Steel", "clasp_type": "Folding",
                "gender": "mens", "watch_style": "sport", "era": "modern",
                "image": "https://images.unsplash.com/photo-1619946794135-5bc917a27793?w=600",
            },
            {
                "brand": "Patek Philippe", "collection": "Calatrava",
                "ref": "5196G-001", "name": "Calatrava",
                "year_start": 2010,
                "case_material": "White Gold", "case_shape": "round", "diameter": 37.0, "thickness": 7.0, "lug_width": 19.0, "water_resistance": 30,
                "dial_color": "Silver", "dial_style": "sunburst", "dial_indices": "roman numerals",
                "bezel_type": "fixed", "bezel_material": "White Gold", "bezel_style": "smooth",
                "hand_style": "cathedral", "hand_lume": False,
                "movement_type": "manual", "caliber": "Cal. 215 PS", "jewels": 18, "power_reserve": 44, "frequency": 28800,
                "bracelet_type": "leather", "bracelet_material": "Alligator", "clasp_type": "Pin buckle",
                "gender": "mens", "watch_style": "dress", "era": "modern",
                "image": "https://images.unsplash.com/photo-1434056886845-dac89ffe9b56?w=600",
            },
            # ── AUDEMARS PIGUET ──
            {
                "brand": "Audemars Piguet", "collection": "Royal Oak",
                "ref": "15202ST.OO.1240ST.01", "name": "Royal Oak Jumbo Extra-Thin",
                "year_start": 2012,
                "case_material": "Steel", "case_shape": "octagonal", "diameter": 39.0, "thickness": 8.1, "lug_width": 21.0, "water_resistance": 50,
                "dial_color": "Blue", "dial_style": "Grande Tapisserie", "dial_indices": "baton", "complications": ["date"],
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "hexagonal screws",
                "hand_style": "baton", "hand_lume": True,
                "movement_type": "automatic", "caliber": "Cal. 2121", "jewels": 36, "power_reserve": 40, "frequency": 19800,
                "bracelet_type": "integrated", "bracelet_material": "Steel", "clasp_type": "Folding",
                "gender": "mens", "watch_style": "sport", "era": "modern",
                "image": "https://images.unsplash.com/photo-1629485456558-3e0d4e3d7d7d?w=600",
            },
            {
                "brand": "Audemars Piguet", "collection": "Royal Oak Offshore",
                "ref": "26470ST.OO.A101CR.01", "name": "Royal Oak Offshore Chronograph",
                "year_start": 2018,
                "case_material": "Steel", "case_shape": "octagonal", "diameter": 42.0, "thickness": 14.4, "lug_width": 22.0, "water_resistance": 100,
                "dial_color": "Grey", "dial_style": "Méga Tapisserie", "dial_indices": "arabic", "complications": ["chronograph", "date"],
                "bezel_type": "fixed", "bezel_material": "Ceramic", "bezel_style": "smooth",
                "hand_style": "baton", "hand_lume": True,
                "movement_type": "automatic", "caliber": "Cal. 3126/3840", "jewels": 59, "power_reserve": 60, "frequency": 21600,
                "bracelet_type": "leather", "bracelet_material": "Rubber", "clasp_type": "Folding",
                "gender": "mens", "watch_style": "sport", "era": "modern",
                "image": "https://images.unsplash.com/photo-1588534510807-96b119c4b3c8?w=600",
            },
            # ── IWC ──
            {
                "brand": "IWC Schaffhausen", "collection": "Pilot's Watch",
                "ref": "IW329301", "name": "Pilot's Watch Mark XX",
                "year_start": 2022,
                "case_material": "Steel", "case_shape": "round", "diameter": 40.0, "thickness": 10.9, "lug_width": 20.0, "water_resistance": 100,
                "dial_color": "Black", "dial_style": "matte", "dial_indices": "arabic", "complications": ["date"],
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "smooth",
                "hand_style": "baton", "hand_lume": True,
                "movement_type": "automatic", "caliber": "Cal. 32111", "jewels": 28, "power_reserve": 120, "frequency": 28800,
                "bracelet_type": "leather", "bracelet_material": "Calfskin", "clasp_type": "Pin buckle",
                "gender": "mens", "watch_style": "pilot", "era": "modern",
                "image": "https://images.unsplash.com/photo-1508057198894-247b23fe5ade?w=600",
            },
            {
                "brand": "IWC Schaffhausen", "collection": "Portugieser",
                "ref": "IW500705", "name": "Portugieser Automatic",
                "year_start": 2021,
                "case_material": "Steel", "case_shape": "round", "diameter": 42.3, "thickness": 10.8, "lug_width": 21.0, "water_resistance": 30,
                "dial_color": "White", "dial_style": "sunburst", "dial_indices": "roman numerals", "complications": ["date"],
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "smooth",
                "hand_style": "dauphine", "hand_lume": False,
                "movement_type": "automatic", "caliber": "Cal. 52010", "jewels": 45, "power_reserve": 168, "frequency": 28800,
                "bracelet_type": "leather", "bracelet_material": "Alligator", "clasp_type": "Pin buckle",
                "gender": "mens", "watch_style": "dress", "era": "modern",
                "image": "https://images.unsplash.com/photo-1518131672697-613becd21bc4?w=600",
            },
            # ── TUDOR ──
            {
                "brand": "Tudor", "collection": "Black Bay",
                "ref": "79230N", "name": "Black Bay 58 Navy Blue",
                "year_start": 2021,
                "case_material": "Steel", "case_shape": "round", "diameter": 39.0, "thickness": 11.9, "lug_width": 19.0, "water_resistance": 200,
                "dial_color": "Navy Blue", "dial_style": "matte", "dial_indices": "hour markers",
                "bezel_type": "rotating_uni", "bezel_material": "Aluminium", "bezel_style": "anodized", "bezel_insert_color": "Blue",
                "hand_style": "sword", "hand_lume": True,
                "movement_type": "automatic", "caliber": "MT5402", "jewels": 26, "power_reserve": 70, "frequency": 28800,
                "bracelet_type": "bracelet", "bracelet_material": "Steel", "clasp_type": "Folding",
                "gender": "mens", "watch_style": "diver", "era": "modern",
                "image": "https://images.unsplash.com/photo-1574914629385-46448b607b78?w=600",
            },
            {
                "brand": "Tudor", "collection": "Pelagos",
                "ref": "25600TN", "name": "Pelagos",
                "year_start": 2015,
                "case_material": "Titanium", "case_shape": "round", "diameter": 42.0, "thickness": 12.0, "lug_width": 21.0, "water_resistance": 500,
                "dial_color": "Black", "dial_style": "matte", "dial_indices": "hour markers", "complications": ["date"],
                "bezel_type": "rotating_uni", "bezel_material": "Ceramic", "bezel_style": "ceramic", "bezel_insert_color": "Black",
                "hand_style": "mercedes", "hand_lume": True,
                "movement_type": "automatic", "caliber": "MT5612", "jewels": 26, "power_reserve": 70, "frequency": 28800,
                "bracelet_type": "bracelet", "bracelet_material": "Titanium", "clasp_type": "Folding",
                "gender": "mens", "watch_style": "diver", "era": "modern",
                "image": "https://images.unsplash.com/photo-1607703702520-2b5831a0c3d6?w=600",
            },
            # ── SEIKO ──
            {
                "brand": "Seiko", "collection": "Prospex",
                "ref": "SPB143J1", "name": "Prospex 1970 Diver's Re-creation",
                "year_start": 2020,
                "case_material": "Steel", "case_shape": "cushion", "diameter": 42.7, "thickness": 13.2, "lug_width": 22.0, "water_resistance": 200,
                "dial_color": "Black", "dial_style": "matte", "dial_indices": "hour markers",
                "bezel_type": "rotating_uni", "bezel_material": "Steel", "bezel_style": "coin-edge", "bezel_insert_color": "Black",
                "hand_style": "sword", "hand_lume": True,
                "movement_type": "automatic", "caliber": "6R35", "jewels": 24, "power_reserve": 70, "frequency": 21600,
                "bracelet_type": "bracelet", "bracelet_material": "Steel", "clasp_type": "Folding",
                "gender": "mens", "watch_style": "diver", "era": "modern",
                "image": "https://images.unsplash.com/photo-1615655114865-4cc1bbb32365?w=600",
            },
            {
                "brand": "Seiko", "collection": "5 Sports",
                "ref": "SRPD51K1", "name": "5 Sports Automatic",
                "year_start": 2019,
                "case_material": "Steel", "case_shape": "round", "diameter": 42.5, "thickness": 11.4, "lug_width": 22.0, "water_resistance": 100,
                "dial_color": "Blue", "dial_style": "sunburst", "dial_indices": "baton", "complications": ["date", "day"],
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "smooth",
                "hand_style": "sword", "hand_lume": True,
                "movement_type": "automatic", "caliber": "4R36", "jewels": 24, "power_reserve": 41, "frequency": 21600,
                "bracelet_type": "bracelet", "bracelet_material": "Steel", "clasp_type": "Folding",
                "gender": "unisex", "watch_style": "sport", "era": "modern",
                "image": "https://images.unsplash.com/photo-1628010610394-c4e6a09d42a6?w=600",
            },
            # ── GRAND SEIKO ──
            {
                "brand": "Grand Seiko", "collection": "Heritage",
                "ref": "SBGW231", "name": "Heritage Manual Wind",
                "year_start": 2019,
                "case_material": "Steel", "case_shape": "round", "diameter": 38.0, "thickness": 10.7, "lug_width": 19.0, "water_resistance": 30,
                "dial_color": "White", "dial_style": "Zaratsu", "dial_indices": "baton",
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "smooth",
                "hand_style": "sword", "hand_lume": True,
                "movement_type": "manual", "caliber": "Cal. 9S64", "jewels": 21, "power_reserve": 72, "frequency": 28800,
                "bracelet_type": "leather", "bracelet_material": "Calfskin", "clasp_type": "Pin buckle",
                "gender": "mens", "watch_style": "dress", "era": "modern",
                "image": "https://images.unsplash.com/photo-1553531087-b75f2b4b6b14?w=600",
            },
            # ── CARTIER ──
            {
                "brand": "Cartier", "collection": "Tank",
                "ref": "WSTA0041", "name": "Tank Must",
                "year_start": 2021,
                "case_material": "Steel", "case_shape": "rectangular", "diameter": 33.7, "thickness": 6.6, "lug_width": 18.0, "water_resistance": 30,
                "dial_color": "Green", "dial_style": "lacquered", "dial_indices": "roman numerals",
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "smooth",
                "hand_style": "sword", "hand_lume": False,
                "movement_type": "quartz", "caliber": "Cal. 057",
                "bracelet_type": "leather", "bracelet_material": "Calfskin", "clasp_type": "Pin buckle",
                "gender": "unisex", "watch_style": "dress", "era": "modern",
                "image": "https://images.unsplash.com/photo-1619946794135-5bc917a27793?w=600",
            },
            {
                "brand": "Cartier", "collection": "Santos",
                "ref": "WSSA0009", "name": "Santos de Cartier Large",
                "year_start": 2018,
                "case_material": "Steel", "case_shape": "square", "diameter": 39.8, "thickness": 9.08, "lug_width": 21.0, "water_resistance": 100,
                "dial_color": "Silver", "dial_style": "guilloché", "dial_indices": "roman numerals", "complications": ["date"],
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "smooth",
                "hand_style": "sword", "hand_lume": False,
                "movement_type": "automatic", "caliber": "Cal. 1847 MC", "jewels": 25, "power_reserve": 40, "frequency": 28800,
                "bracelet_type": "integrated", "bracelet_material": "Steel", "clasp_type": "Folding",
                "gender": "mens", "watch_style": "dress", "era": "modern",
                "image": "https://images.unsplash.com/photo-1508057198894-247b23fe5ade?w=600",
            },
            # ── TAG HEUER ──
            {
                "brand": "TAG Heuer", "collection": "Carrera",
                "ref": "CBN2A1AA.BA0643", "name": "Carrera Heuer 02 Chronograph",
                "year_start": 2019,
                "case_material": "Steel", "case_shape": "round", "diameter": 44.0, "thickness": 15.5, "lug_width": 22.0, "water_resistance": 100,
                "dial_color": "Black", "dial_style": "matte", "dial_indices": "arabic", "complications": ["chronograph", "date"],
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "tachymeter",
                "hand_style": "baton", "hand_lume": True,
                "movement_type": "automatic", "caliber": "Heuer 02", "jewels": 33, "power_reserve": 80, "frequency": 28800,
                "bracelet_type": "leather", "bracelet_material": "Calfskin", "clasp_type": "Folding",
                "gender": "mens", "watch_style": "racing", "era": "modern",
                "image": "https://images.unsplash.com/photo-1547996160-81dfa63595aa?w=600",
            },
            # ── LONGINES ──
            {
                "brand": "Longines", "collection": "HydroConquest",
                "ref": "L3.781.4.96.6", "name": "HydroConquest Automatic",
                "year_start": 2020,
                "case_material": "Steel", "case_shape": "round", "diameter": 41.0, "thickness": 11.5, "lug_width": 21.0, "water_resistance": 300,
                "dial_color": "Blue", "dial_style": "sunburst", "dial_indices": "baton", "complications": ["date"],
                "bezel_type": "rotating_uni", "bezel_material": "Ceramic", "bezel_style": "ceramic", "bezel_insert_color": "Blue",
                "hand_style": "sword", "hand_lume": True,
                "movement_type": "automatic", "caliber": "Cal. L888.4", "jewels": 26, "power_reserve": 72, "frequency": 25200,
                "bracelet_type": "bracelet", "bracelet_material": "Steel", "clasp_type": "Folding",
                "gender": "mens", "watch_style": "diver", "era": "modern",
                "image": "https://images.unsplash.com/photo-1612817288484-6f916006741a?w=600",
            },
            # ── NOMOS ──
            {
                "brand": "Nomos Glashütte", "collection": "Tangente",
                "ref": "101", "name": "Tangente 35",
                "year_start": 2015,
                "case_material": "Steel", "case_shape": "round", "diameter": 35.0, "thickness": 6.6, "lug_width": 16.0, "water_resistance": 30,
                "dial_color": "White", "dial_style": "lacquered", "dial_indices": "arabic",
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "smooth",
                "hand_style": "dauphine", "hand_lume": False,
                "movement_type": "manual", "caliber": "Alpha", "jewels": 17, "power_reserve": 43, "frequency": 21600,
                "bracelet_type": "leather", "bracelet_material": "Calfskin", "clasp_type": "Pin buckle",
                "gender": "unisex", "watch_style": "dress", "era": "modern",
                "image": "https://images.unsplash.com/photo-1434056886845-dac89ffe9b56?w=600",
            },
            # ── PANERAI ──
            {
                "brand": "Panerai", "collection": "Luminor",
                "ref": "PAM01312", "name": "Luminor Marina",
                "year_start": 2021,
                "case_material": "Steel", "case_shape": "cushion", "diameter": 44.0, "thickness": 15.0, "lug_width": 24.0, "water_resistance": 300,
                "dial_color": "Black", "dial_style": "matte", "dial_indices": "arabic",
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "smooth",
                "hand_style": "baton", "hand_lume": True,
                "movement_type": "automatic", "caliber": "Cal. P.9010", "jewels": 28, "power_reserve": 72, "frequency": 28800,
                "bracelet_type": "leather", "bracelet_material": "Calfskin", "clasp_type": "Pin buckle",
                "gender": "mens", "watch_style": "diver", "era": "modern",
                "image": "https://images.unsplash.com/photo-1573408301185-9519f95a95bc?w=600",
            },
            # ── A. LANGE & SÖHNE ──
            {
                "brand": "A. Lange & Söhne", "collection": "Lange 1",
                "ref": "101.025", "name": "Lange 1",
                "year_start": 1994,
                "case_material": "Yellow Gold", "case_shape": "round", "diameter": 38.5, "thickness": 10.0, "lug_width": 19.0, "water_resistance": 30,
                "dial_color": "Silver", "dial_style": "guilloché", "dial_indices": "arabic", "complications": ["date", "power reserve"],
                "bezel_type": "fixed", "bezel_material": "Yellow Gold", "bezel_style": "smooth",
                "hand_style": "dauphine", "hand_lume": False,
                "movement_type": "manual", "caliber": "Cal. L901.0", "jewels": 53, "power_reserve": 72, "frequency": 21600,
                "bracelet_type": "leather", "bracelet_material": "Alligator", "clasp_type": "Pin buckle",
                "gender": "mens", "watch_style": "dress", "era": "modern",
                "image": "https://images.unsplash.com/photo-1518131672697-613becd21bc4?w=600",
            },
            # ── BREITLING ──
            {
                "brand": "Breitling", "collection": "Navitimer",
                "ref": "AB0139211G1P2", "name": "Navitimer B01 Chronograph 43",
                "year_start": 2021,
                "case_material": "Steel", "case_shape": "round", "diameter": 43.0, "thickness": 14.75, "lug_width": 22.0, "water_resistance": 30,
                "dial_color": "Silver", "dial_style": "sunburst", "dial_indices": "arabic", "complications": ["chronograph"],
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "circular slide rule",
                "hand_style": "baton", "hand_lume": True,
                "movement_type": "automatic", "caliber": "Cal. B01", "jewels": 47, "power_reserve": 70, "frequency": 28800,
                "bracelet_type": "leather", "bracelet_material": "Calfskin", "clasp_type": "Folding",
                "gender": "mens", "watch_style": "pilot", "era": "modern",
                "image": "https://images.unsplash.com/photo-1614164185128-e4ec99c436d7?w=600",
            },
            # ── JAEGER-LECOULTRE ──
            {
                "brand": "Jaeger-LeCoultre", "collection": "Reverso",
                "ref": "Q3858522", "name": "Reverso Classic Medium",
                "year_start": 2019,
                "case_material": "Steel", "case_shape": "rectangular", "diameter": 40.1, "thickness": 9.1, "lug_width": 18.0, "water_resistance": 30,
                "dial_color": "Silver", "dial_style": "guilloché", "dial_indices": "arabic",
                "bezel_type": "fixed", "bezel_material": "Steel", "bezel_style": "smooth",
                "hand_style": "dauphine", "hand_lume": False,
                "movement_type": "manual", "caliber": "Cal. 822/2", "jewels": 17, "power_reserve": 45, "frequency": 21600,
                "bracelet_type": "leather", "bracelet_material": "Calfskin", "clasp_type": "Pin buckle",
                "gender": "mens", "watch_style": "dress", "era": "modern",
                "image": "https://images.unsplash.com/photo-1553531087-b75f2b4b6b14?w=600",
            },
        ]

        # ─── Insert collections and references ───────────────────────────────
        for w in watches:
            brand = brand_map.get(w["brand"])
            if not brand:
                continue

            # Get or create collection
            coll = db.query(Collection).filter(
                Collection.brand_id == brand.id, Collection.name == w["collection"]
            ).first()
            if not coll:
                coll = Collection(
                    brand_id=brand.id,
                    name=w["collection"],
                    slug=slugify(f"{w['brand']}-{w['collection']}"),
                )
                db.add(coll)
                db.flush()

            # Build unique slug
            base_slug = slugify(f"{w['brand']}-{w['name']}-{w['ref']}")
            existing_ref = db.query(WatchReference).filter(
                WatchReference.slug == base_slug
            ).first()
            if existing_ref:
                continue  # already seeded

            ref = WatchReference(
                collection_id=coll.id,
                reference_number=w.get("ref"),
                name=w["name"],
                slug=base_slug,
                production_year_start=w.get("year_start"),
                production_year_end=w.get("year_end"),
                case_material=w.get("case_material"),
                case_shape=w.get("case_shape"),
                case_diameter_mm=w.get("diameter"),
                case_thickness_mm=w.get("thickness"),
                lug_width_mm=w.get("lug_width"),
                water_resistance_m=w.get("water_resistance"),
                dial_color=w.get("dial_color"),
                dial_style=w.get("dial_style"),
                dial_indices=w.get("dial_indices"),
                dial_complications=w.get("complications"),
                bezel_type=w.get("bezel_type"),
                bezel_material=w.get("bezel_material"),
                bezel_style=w.get("bezel_style"),
                bezel_insert_color=w.get("bezel_insert_color"),
                hand_style=w.get("hand_style"),
                hand_lume=w.get("hand_lume", False),
                movement_type=w.get("movement_type"),
                movement_caliber=w.get("caliber"),
                movement_jewels=w.get("jewels"),
                power_reserve_hours=w.get("power_reserve"),
                frequency_bph=w.get("frequency"),
                bracelet_type=w.get("bracelet_type"),
                bracelet_material=w.get("bracelet_material"),
                clasp_type=w.get("clasp_type"),
                gender=w.get("gender"),
                watch_style=w.get("watch_style"),
                era=w.get("era"),
                primary_image_url=w.get("image"),
                thumbnail_url=w.get("image"),
                is_published=True,
                view_count=0,
            )
            db.add(ref)
            db.flush()

            if w.get("image"):
                img = WatchImage(
                    reference_id=ref.id,
                    url=w["image"],
                    angle="front",
                    is_primary=True,
                )
                db.add(img)

        db.commit()
        count = db.query(WatchReference).count()
        print(f"✅ Seed complete. {count} watches in catalog.")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
