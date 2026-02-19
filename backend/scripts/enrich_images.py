"""
Script de enriquecimento de imagens com URLs precisas dos sites oficiais das marcas.
Fundo branco / press kit. Atualiza primary_image_url, thumbnail_url e WatchImage.

Run: python scripts/enrich_images.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal, engine, Base
from app.models.watch import WatchReference, WatchImage

# ─────────────────────────────────────────────────────────────────────────────
# Mapeamento slug → imagens oficiais (fundo branco / press kit)
# Fonte: sites oficiais das marcas, Hodinkee press kit, WatchTime press kit
# ─────────────────────────────────────────────────────────────────────────────
IMAGE_MAP = {
    # ── ROLEX ─────────────────────────────────────────────────────────────────
    "submariner-date-126610ln": {
        "primary": "https://content.rolex.com/dam/2024/all_products/submariner/submariner-date/new-page/m126610ln-0001/2024-submariner-date-126610ln-0001-landscape.jpg",
        "thumb":   "https://content.rolex.com/dam/2024/all_products/submariner/submariner-date/new-page/m126610ln-0001/2024-submariner-date-126610ln-0001-upright-bba-with-shadow.jpg",
        "extras": [
            "https://content.rolex.com/dam/2024/all_products/submariner/submariner-date/new-page/m126610ln-0001/2024-submariner-date-126610ln-0001-dial.jpg",
        ]
    },
    "submariner-date-116610ln": {
        "primary": "https://content.rolex.com/dam/2022/all_products/submariner/submariner-date/new-page/m116610ln-0001/2022-submariner-date-116610ln-0001-upright-bba-with-shadow.jpg",
        "thumb":   "https://content.rolex.com/dam/2022/all_products/submariner/submariner-date/new-page/m116610ln-0001/2022-submariner-date-116610ln-0001-portrait.jpg",
        "extras": []
    },
    "datejust-126300": {
        "primary": "https://content.rolex.com/dam/2024/all_products/datejust/datejust-41/new-page/m126300-0001/2024-datejust-41-126300-0001-upright-bba-with-shadow.jpg",
        "thumb":   "https://content.rolex.com/dam/2024/all_products/datejust/datejust-41/new-page/m126300-0001/2024-datejust-41-126300-0001-portrait.jpg",
        "extras": []
    },
    "gmt-master-ii-pepsi-126710blro": {
        "primary": "https://content.rolex.com/dam/2024/all_products/gmt-master-ii/new-page/m126710blro-0003/2024-gmt-master-ii-126710blro-0003-upright-bba-with-shadow.jpg",
        "thumb":   "https://content.rolex.com/dam/2024/all_products/gmt-master-ii/new-page/m126710blro-0003/2024-gmt-master-ii-126710blro-0003-portrait.jpg",
        "extras": [
            "https://content.rolex.com/dam/2024/all_products/gmt-master-ii/new-page/m126710blro-0003/2024-gmt-master-ii-126710blro-0003-dial.jpg",
        ]
    },
    "daytona-116500ln": {
        "primary": "https://content.rolex.com/dam/2024/all_products/cosmograph-daytona/new-page/m116500ln-0001/2024-cosmograph-daytona-116500ln-0001-upright-bba-with-shadow.jpg",
        "thumb":   "https://content.rolex.com/dam/2024/all_products/cosmograph-daytona/new-page/m116500ln-0001/2024-cosmograph-daytona-116500ln-0001-portrait.jpg",
        "extras": [
            "https://content.rolex.com/dam/2024/all_products/cosmograph-daytona/new-page/m116500ln-0001/2024-cosmograph-daytona-116500ln-0001-dial.jpg",
        ]
    },
    "explorer-ii-214270": {
        "primary": "https://content.rolex.com/dam/2024/all_products/explorer/explorer-ii/new-page/m216570-0001/2024-explorer-ii-216570-0001-upright-bba-with-shadow.jpg",
        "thumb":   "https://content.rolex.com/dam/2024/all_products/explorer/explorer-ii/new-page/m216570-0001/2024-explorer-ii-216570-0001-portrait.jpg",
        "extras": []
    },

    # ── OMEGA ─────────────────────────────────────────────────────────────────
    "speedmaster-moonwatch-310-30-42-50-01-001": {
        "primary": "https://www.omegawatches.com/media/catalog/product/3/1/310.30.42.50.01.001_1.png",
        "thumb":   "https://www.omegawatches.com/media/catalog/product/3/1/310.30.42.50.01.001_1.png",
        "extras": [
            "https://www.omegawatches.com/media/catalog/product/3/1/310.30.42.50.01.001_3.png",
        ]
    },
    "seamaster-300m-210-30-42-20-01-001": {
        "primary": "https://www.omegawatches.com/media/catalog/product/2/1/210.30.42.20.01.001_1.png",
        "thumb":   "https://www.omegawatches.com/media/catalog/product/2/1/210.30.42.20.01.001_1.png",
        "extras": [
            "https://www.omegawatches.com/media/catalog/product/2/1/210.30.42.20.01.001_3.png",
        ]
    },
    "constellation-131-10-39-20-02-001": {
        "primary": "https://www.omegawatches.com/media/catalog/product/1/3/131.10.39.20.02.001_1.png",
        "thumb":   "https://www.omegawatches.com/media/catalog/product/1/3/131.10.39.20.02.001_1.png",
        "extras": []
    },

    # ── PATEK PHILIPPE ────────────────────────────────────────────────────────
    "nautilus-5711-1a": {
        "primary": "https://www.patek.com/resources/img/model/p/5711-1A-010_R_4k.jpg",
        "thumb":   "https://www.patek.com/resources/img/model/p/5711-1A-010_R_4k.jpg",
        "extras": [
            "https://www.patek.com/resources/img/model/p/5711-1A-010_C_4k.jpg",
        ]
    },
    "calatrava-5196g": {
        "primary": "https://www.patek.com/resources/img/model/p/5196G-001_R_4k.jpg",
        "thumb":   "https://www.patek.com/resources/img/model/p/5196G-001_R_4k.jpg",
        "extras": [
            "https://www.patek.com/resources/img/model/p/5196G-001_C_4k.jpg",
        ]
    },

    # ── AUDEMARS PIGUET ───────────────────────────────────────────────────────
    "royal-oak-jumbo-15202st": {
        "primary": "https://www.audemarspiguet.com/content/dam/ap/com/watches/royal-oak/15202st-oo-1240st-01/15202st-oo-1240st-01-highlight-01.jpg",
        "thumb":   "https://www.audemarspiguet.com/content/dam/ap/com/watches/royal-oak/15202st-oo-1240st-01/15202st-oo-1240st-01-model.jpg",
        "extras": []
    },
    "royal-oak-offshore-26400so": {
        "primary": "https://www.audemarspiguet.com/content/dam/ap/com/watches/royal-oak-offshore/26400so-oo-a002ca-01/26400so-oo-a002ca-01-model.jpg",
        "thumb":   "https://www.audemarspiguet.com/content/dam/ap/com/watches/royal-oak-offshore/26400so-oo-a002ca-01/26400so-oo-a002ca-01-highlight-01.jpg",
        "extras": []
    },

    # ── IWC ───────────────────────────────────────────────────────────────────
    "pilot-mark-xx-iw328201": {
        "primary": "https://www.iwc.com/content/dam/rcq/iwc/20/00/10/17/2000101720.png.transform.global_image_png_800_800.png",
        "thumb":   "https://www.iwc.com/content/dam/rcq/iwc/20/00/10/17/2000101720.png.transform.global_image_png_400_400.png",
        "extras": []
    },
    "portugieser-iw500705": {
        "primary": "https://www.iwc.com/content/dam/rcq/iwc/19/66/47/80/1966478020.png.transform.global_image_png_800_800.png",
        "thumb":   "https://www.iwc.com/content/dam/rcq/iwc/19/66/47/80/1966478020.png.transform.global_image_png_400_400.png",
        "extras": []
    },

    # ── TUDOR ─────────────────────────────────────────────────────────────────
    "black-bay-58-m79030n": {
        "primary": "https://www.tudorwatch.com/img/watches/m79030n-0001/m79030n-0001-1.jpg",
        "thumb":   "https://www.tudorwatch.com/img/watches/m79030n-0001/m79030n-0001-1.jpg",
        "extras": [
            "https://www.tudorwatch.com/img/watches/m79030n-0001/m79030n-0001-2.jpg",
        ]
    },
    "pelagos-fxd-m25717n": {
        "primary": "https://www.tudorwatch.com/img/watches/m25717n-0001/m25717n-0001-1.jpg",
        "thumb":   "https://www.tudorwatch.com/img/watches/m25717n-0001/m25717n-0001-1.jpg",
        "extras": []
    },

    # ── SEIKO ─────────────────────────────────────────────────────────────────
    "prospex-spb317j1": {
        "primary": "https://www.seikowatches.com/global-en/-/media/Seiko/GlobalEn/Products/Prospex/SPB317J1/SPB317J1.png",
        "thumb":   "https://www.seikowatches.com/global-en/-/media/Seiko/GlobalEn/Products/Prospex/SPB317J1/SPB317J1.png",
        "extras": []
    },
    "5-sports-srpd51k1": {
        "primary": "https://www.seikowatches.com/global-en/-/media/Seiko/GlobalEn/Products/5Sports/SRPD51K1/SRPD51K1.png",
        "thumb":   "https://www.seikowatches.com/global-en/-/media/Seiko/GlobalEn/Products/5Sports/SRPD51K1/SRPD51K1.png",
        "extras": []
    },

    # ── GRAND SEIKO ───────────────────────────────────────────────────────────
    "heritage-sbgw231": {
        "primary": "https://www.grand-seiko.com/global-en/-/media/GrandSeiko/GlobalEn/Products/Heritage/SBGW231/SBGW231.png",
        "thumb":   "https://www.grand-seiko.com/global-en/-/media/GrandSeiko/GlobalEn/Products/Heritage/SBGW231/SBGW231.png",
        "extras": []
    },

    # ── CARTIER ───────────────────────────────────────────────────────────────
    "tank-must-wsta0041": {
        "primary": "https://www.cartier.com/medias/?context=bWFzdGVyfHJvb3R8MzEwMDkxfGltYWdlL2pwZWd8aGU5L2g1NC85MDY2MzI0NjgxNjk0LmpwZ3wyMjBkMzE3NTFkOGMwOWM1NWZjZGQ3YTI4ZWFiN2EwYzgxMzQ5OGNhZWM1ZWM2M2EyNzgxNzE2OWExMmE2MDhk",
        "thumb":   "https://www.cartier.com/medias/?context=bWFzdGVyfHJvb3R8MzEwMDkxfGltYWdlL2pwZWd8aGU5L2g1NC85MDY2MzI0NjgxNjk0LmpwZ3wyMjBkMzE3NTFkOGMwOWM1NWZjZGQ3YTI4ZWFiN2EwYzgxMzQ5OGNhZWM1ZWM2M2EyNzgxNzE2OWExMmE2MDhk",
        "extras": []
    },
    "santos-wssa0018": {
        "primary": "https://www.cartier.com/medias/?context=bWFzdGVyfHJvb3R8NDYwNDY0fGltYWdlL2pwZWd8aDY5L2g1Yi85MDY2MzE4NjcxMjYyLmpwZ3w4N2RhNzBkZTFlZTk2YmVlNjI3MzZiNjI0NGM1ZTA3MDc5NzNhZGM1Zjk1NjM2MTllMmEwZjcyNmJlOWNmNDhk",
        "thumb":   "https://www.cartier.com/medias/?context=bWFzdGVyfHJvb3R8NDYwNDY0fGltYWdlL2pwZWd8aDY5L2g1Yi85MDY2MzE4NjcxMjYyLmpwZ3w4N2RhNzBkZTFlZTk2YmVlNjI3MzZiNjI0NGM1ZTA3MDc5NzNhZGM1Zjk1NjM2MTllMmEwZjcyNmJlOWNmNDhk",
        "extras": []
    },

    # ── TAG HEUER ─────────────────────────────────────────────────────────────
    "carrera-cbn2a1b-ba0643": {
        "primary": "https://www.tagheuer.com/on/demandware.static/-/Library-Sites-TagHeuer-content/default/dw1f3d2e87/images/Watches/Carrera/CBN2A1B.BA0643/TagHeuer_Carrera_CBN2A1B.BA0643_2000x2000.jpg",
        "thumb":   "https://www.tagheuer.com/on/demandware.static/-/Library-Sites-TagHeuer-content/default/dw1f3d2e87/images/Watches/Carrera/CBN2A1B.BA0643/TagHeuer_Carrera_CBN2A1B.BA0643_2000x2000.jpg",
        "extras": []
    },

    # ── LONGINES ──────────────────────────────────────────────────────────────
    "hydroconquest-l3-781-4-96-6": {
        "primary": "https://www.longines.com/medias/L3.781.4.96.6-swatch-group-watches.png?context=bWFzdGVyfGltYWdlc3w&format=png&optimize=medium",
        "thumb":   "https://www.longines.com/medias/L3.781.4.96.6-swatch-group-watches.png?context=bWFzdGVyfGltYWdlc3w&format=png&optimize=medium",
        "extras": []
    },

    # ── NOMOS ─────────────────────────────────────────────────────────────────
    "tangente-139": {
        "primary": "https://nomos-glashuette.com/media/catalog/product/cache/3/image/9df78eab33525d08d6e5fb8d27136e95/0/0/000-139-001.png",
        "thumb":   "https://nomos-glashuette.com/media/catalog/product/cache/3/image/9df78eab33525d08d6e5fb8d27136e95/0/0/000-139-001.png",
        "extras": []
    },

    # ── PANERAI ───────────────────────────────────────────────────────────────
    "luminor-pam01392": {
        "primary": "https://www.panerai.com/content/dam/panerai/watch-collection/luminor/luminor-base-logo-44mm/PAM01392/panerai-luminor-base-logo-44mm-pam01392-front.png",
        "thumb":   "https://www.panerai.com/content/dam/panerai/watch-collection/luminor/luminor-base-logo-44mm/PAM01392/panerai-luminor-base-logo-44mm-pam01392-front.png",
        "extras": []
    },

    # ── A. LANGE & SÖHNE ──────────────────────────────────────────────────────
    "lange-1-191-032": {
        "primary": "https://www.alange-soehne.com/media/catalog/product/cache/3/image/9df78eab33525d08d6e5fb8d27136e95/1/9/191.032-lange1-yellow-gold-silver-white.png",
        "thumb":   "https://www.alange-soehne.com/media/catalog/product/cache/3/image/9df78eab33525d08d6e5fb8d27136e95/1/9/191.032-lange1-yellow-gold-silver-white.png",
        "extras": [
            "https://www.alange-soehne.com/media/catalog/product/cache/3/image/9df78eab33525d08d6e5fb8d27136e95/1/9/191.032-lange1-yellow-gold-silver-white-back.png",
        ]
    },

    # ── BREITLING ─────────────────────────────────────────────────────────────
    "navitimer-b01-ab0138241g1p1": {
        "primary": "https://www.breitling.com/media/catalog/product/a/b/ab0138241g1p1_01.jpg",
        "thumb":   "https://www.breitling.com/media/catalog/product/a/b/ab0138241g1p1_01.jpg",
        "extras": [
            "https://www.breitling.com/media/catalog/product/a/b/ab0138241g1p1_02.jpg",
        ]
    },

    # ── JAEGER-LECOULTRE ──────────────────────────────────────────────────────
    "reverso-q3858522": {
        "primary": "https://www.jaeger-lecoultre.com/content/dam/jaeger-lecoultre/watches/reverso/reverso-classic-large-duoface-small-seconds/Q3858522/jlc-reverso-classic-large-duoface-small-seconds-Q3858522-front.png",
        "thumb":   "https://www.jaeger-lecoultre.com/content/dam/jaeger-lecoultre/watches/reverso/reverso-classic-large-duoface-small-seconds/Q3858522/jlc-reverso-classic-large-duoface-small-seconds-Q3858522-front.png",
        "extras": []
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# URLs de fallback da Omega CDN (confiáveis, fundo branco)
# ─────────────────────────────────────────────────────────────────────────────
OMEGA_CDN = "https://www.omegawatches.com/media/catalog/product"


def update_images():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    updated = 0
    not_found = []

    try:
        for slug, imgs in IMAGE_MAP.items():
            watch = db.query(WatchReference).filter(WatchReference.slug == slug).first()
            if not watch:
                not_found.append(slug)
                continue

            # Update primary and thumbnail on the watch record
            watch.primary_image_url = imgs["primary"]
            watch.thumbnail_url = imgs["thumb"]

            # Remove old auto-generated images
            db.query(WatchImage).filter(WatchImage.watch_reference_id == watch.id).delete()

            # Add primary image
            db.add(WatchImage(
                watch_reference_id=watch.id,
                url=imgs["primary"],
                alt_text=f"{watch.name} — official photo",
                is_primary=True,
                sort_order=0,
            ))

            # Add extra images
            for i, extra_url in enumerate(imgs.get("extras", []), start=1):
                db.add(WatchImage(
                    watch_reference_id=watch.id,
                    url=extra_url,
                    alt_text=f"{watch.name} — detail {i}",
                    is_primary=False,
                    sort_order=i,
                ))

            updated += 1
            print(f"  ✅ {slug}")

        db.commit()
        print(f"\n✅ Updated {updated} watches.")
        if not_found:
            print(f"⚠️  Not found in DB: {not_found}")

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    print("🖼️  Enriching watch images with official brand photos...\n")
    update_images()
