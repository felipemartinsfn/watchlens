"""
Embedding service using CLIP for visual similarity search.
Uses sentence-transformers CLIP model for multimodal embeddings.
Falls back to a lightweight dummy model if torch is not available.
"""
import numpy as np
import logging
from typing import List, Optional
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

_model = None
_processor = None
_model_loaded = False


def _load_model():
    global _model, _processor, _model_loaded
    if _model_loaded:
        return
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading CLIP model (clip-ViT-B-32)...")
        _model = SentenceTransformer("clip-ViT-B-32")
        _model_loaded = True
        logger.info("CLIP model loaded successfully.")
    except Exception as e:
        logger.warning(f"Could not load CLIP model: {e}. Using dummy embeddings.")
        _model_loaded = True


def get_image_embedding(image_bytes: bytes) -> List[float]:
    """Generate CLIP embedding from raw image bytes."""
    _load_model()
    try:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        img = img.resize((224, 224))
        if _model is not None:
            embedding = _model.encode(img)
            return embedding.tolist()
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
    # Fallback: random normalized vector
    vec = np.random.randn(512).astype(np.float32)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


def get_text_embedding(text: str) -> List[float]:
    """Generate CLIP embedding from text."""
    _load_model()
    try:
        if _model is not None:
            embedding = _model.encode(text)
            return embedding.tolist()
    except Exception as e:
        logger.error(f"Text embedding failed: {e}")
    vec = np.random.randn(512).astype(np.float32)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))


def similarity_to_score(cosine_sim: float) -> float:
    """
    Convert cosine similarity [-1, 1] to a 0-100% score.
    Watches with the same embedding = 100, completely orthogonal = 50.
    """
    score = (cosine_sim + 1) / 2 * 100
    return round(min(max(score, 0), 100), 1)


def find_similar(
    query_embedding: List[float],
    candidate_embeddings: List[tuple],  # list of (id, embedding)
    top_k: int = 20,
    min_score: float = 60.0,
) -> List[dict]:
    """
    Find most similar watches given a query embedding.
    Returns list of {id, score} sorted by score descending.
    """
    results = []
    for watch_id, emb in candidate_embeddings:
        if emb is None:
            continue
        sim = cosine_similarity(query_embedding, emb)
        score = similarity_to_score(sim)
        if score >= min_score:
            results.append({"id": watch_id, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
