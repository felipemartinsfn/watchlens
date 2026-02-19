"""
Gera embeddings CLIP para todos os relógios do catálogo.
Baixa a imagem primária de cada relógio e armazena o embedding no banco.

Run: python scripts/generate_embeddings.py

Opções:
  --batch 50     Processa em batches de N (default: 50)
  --skip-done    Pula relógios que já têm embedding (default: True)
  --force        Regenera todos os embeddings, mesmo os já existentes
"""
import sys, os, time, argparse, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import urllib.request
import numpy as np
from io import BytesIO
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

from app.core.database import SessionLocal, engine, Base
from app.models.watch import WatchReference

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Referer": "https://watchbase.com/",
}

# ─── Load CLIP model ───────────────────────────────────────────────────────────

def load_clip():
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading CLIP model (clip-ViT-B-32)...")
        model = SentenceTransformer("clip-ViT-B-32")
        logger.info("✅ CLIP model loaded.")
        return model
    except Exception as e:
        logger.error(f"❌ Could not load CLIP model: {e}")
        return None


def embed_image(model, img: Image.Image):
    """Generate CLIP embedding for a PIL image."""
    img = img.convert("RGB").resize((224, 224))
    vec = model.encode(img)
    return vec.tolist()


# ─── Image fetching ────────────────────────────────────────────────────────────

def fetch_image(url: str, retries: int = 2) -> bytes | None:
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.read()
        except Exception as e:
            if attempt < retries:
                time.sleep(1.0)
            else:
                return None


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate CLIP embeddings for watch catalog")
    parser.add_argument("--batch", type=int, default=50, help="Commit every N watches")
    parser.add_argument("--force", action="store_true", help="Regenerate all embeddings")
    args = parser.parse_args()

    model = load_clip()
    if model is None:
        logger.error("Cannot proceed without CLIP model. Install sentence-transformers.")
        sys.exit(1)

    db = SessionLocal()
    try:
        query = db.query(WatchReference).filter(WatchReference.is_published == True)
        if not args.force:
            query = query.filter(WatchReference.embedding == None)

        watches = query.all()
        total = len(watches)
        logger.info(f"📋 {total} watches to process")

        done = 0
        failed = 0
        batch_count = 0

        for i, watch in enumerate(watches, 1):
            img_url = watch.primary_image_url or watch.thumbnail_url
            if not img_url:
                logger.warning(f"  [{i}/{total}] {watch.slug} — no image URL, skipping")
                failed += 1
                continue

            # Fetch image
            img_bytes = fetch_image(img_url)
            if not img_bytes:
                logger.warning(f"  [{i}/{total}] {watch.slug} — fetch failed: {img_url}")
                failed += 1
                continue

            # Generate embedding
            try:
                img = Image.open(BytesIO(img_bytes))
                embedding = embed_image(model, img)
                watch.embedding = embedding
                done += 1
                batch_count += 1
                logger.info(f"  [{i}/{total}] ✅ {watch.slug}")
            except Exception as e:
                logger.warning(f"  [{i}/{total}] ❌ {watch.slug} — embed error: {e}")
                failed += 1
                continue

            # Commit in batches
            if batch_count >= args.batch:
                db.commit()
                logger.info(f"  💾 Committed batch ({done} done so far)")
                batch_count = 0

            # Small delay to be polite to CDN
            time.sleep(0.1)

        # Final commit
        if batch_count > 0:
            db.commit()

        logger.info(f"\n{'='*50}")
        logger.info(f"✅ Done! {done} embeddings generated, {failed} failed")

        # Verify
        total_with_emb = db.query(WatchReference).filter(WatchReference.embedding != None).count()
        logger.info(f"📊 Watches with embeddings: {total_with_emb}/{db.query(WatchReference).count()}")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
