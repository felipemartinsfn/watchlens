"""
Watch structural feature extraction and scoring for hybrid image search re-ranking.

This module analyzes structured watch metadata to produce a feature vector
that captures watchmaking-specific characteristics CLIP cannot reliably distinguish:
  - Number and type of subdials (small seconds ≠ chronograph subdials)
  - Dial pattern / finish (sector, guilloché, sunburst, fumé, California)
  - Case shape (round, rectangular, cushion, tonneau, octagonal)
  - Bezel type (smooth fixed, rotating diver, fluted, etc.)
  - Hand style (dauphine, mercedes, snowflake, leaf, baton, pencil)
  - Movement type (automatic, manual, quartz)
  - Watch style category (dress, diver, pilot, racing, gmt, sport)
  - Complication set (chronograph, gmt, moonphase, power reserve, etc.)

Scoring:
  Given a query image, we also run it through CLIP text-image similarity against
  a set of watchmaking concept phrases to infer query features. We then compare
  those inferred features against each candidate's structural features.

  final_score = (CLIP_WEIGHT * clip_score) + (FEATURE_WEIGHT * feature_score)
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

# Blend weights
CLIP_WEIGHT = 0.45
FEATURE_WEIGHT = 0.55

# ─── Feature concept definitions ──────────────────────────────────────────────
#
# Each "concept" is a dict with:
#   key       — internal identifier
#   prompts   — list of CLIP text prompts to probe the query image
#   db_fields — function(watch) -> float in [0,1] indicating how strongly
#               the candidate watch matches this concept

CONCEPTS = [
    # ── Subdial / complication type ─────────────────────────────────────────
    {
        "key": "has_chronograph",
        "prompts": [
            "a watch with two or three chronograph subdials and pushers on the case",
            "a chronograph wristwatch with stopwatch subdials at 3, 6, and 9 o'clock",
            "a racing chronograph with tachymeter bezel and multiple subdials",
        ],
        "weight": 2.5,  # High weight — small seconds vs chrono is the #1 confusion
    },
    {
        "key": "has_small_seconds",
        "prompts": [
            "a watch with a single small seconds subdial, no pushers, classic dress watch",
            "a watch with one small sub-dial showing running seconds at 6 o'clock",
            "a traditional watch with small seconds hand in a subsidiary dial",
        ],
        "weight": 2.5,
    },
    {
        "key": "has_gmt",
        "prompts": [
            "a GMT watch with a fourth hand pointing to a 24-hour bezel",
            "a dual timezone wristwatch with a GMT hand and 24-hour scale",
            "a pilot watch with GMT complication showing two time zones",
        ],
        "weight": 1.5,
    },
    {
        "key": "has_date",
        "prompts": [
            "a wristwatch with a date window at 3 o'clock showing a date aperture",
            "a watch with a small date complication display",
        ],
        "weight": 0.8,
    },
    {
        "key": "has_moonphase",
        "prompts": [
            "a watch with a moonphase complication showing the moon and stars",
            "a dress watch with a blue moonphase display in the dial",
        ],
        "weight": 1.5,
    },
    # ── Dial style ───────────────────────────────────────────────────────────
    {
        "key": "dial_sector",
        "prompts": [
            "a watch with a sector dial with concentric colored zones, two-tone dial",
            "a vintage-style sector dial wristwatch with different colored regions",
            "a watch with a sector dial showing distinct colored bands at different hour zones",
        ],
        "weight": 2.0,
    },
    {
        "key": "dial_california",
        "prompts": [
            "a California dial watch with Roman numerals on top half and Arabic numerals on bottom",
            "a watch with mixed Roman and Arabic numerals split across the dial",
            "a Panerai-style California dial with half Roman half Arabic hour markers",
        ],
        "weight": 2.0,
    },
    {
        "key": "dial_guilloche",
        "prompts": [
            "a watch with a guilloché engraved dial showing a geometric pattern",
            "a watch with an engine-turned guilloché dial texture",
            "a watch with an intricate hand-engraved guilloché pattern on the dial",
        ],
        "weight": 1.5,
    },
    {
        "key": "dial_fume",
        "prompts": [
            "a watch with a fumé gradient dial that fades from dark center to lighter edges",
            "a fumé dial wristwatch with gradual color transition from center to rim",
        ],
        "weight": 1.5,
    },
    {
        "key": "dial_sunburst",
        "prompts": [
            "a watch with a sunburst radial brushed dial reflecting light in rays",
            "a watch with a sunray finished dial with radiating light reflection",
        ],
        "weight": 0.8,
    },
    {
        "key": "dial_plain",
        "prompts": [
            "a watch with a clean plain matte or lacquered dial with no texture",
            "a watch with a simple solid color dial without patterns or complications",
        ],
        "weight": 0.5,
    },
    # ── Case shape ───────────────────────────────────────────────────────────
    {
        "key": "case_round",
        "prompts": [
            "a round circular watch case",
            "a wristwatch with a traditional round case shape",
        ],
        "weight": 1.0,
    },
    {
        "key": "case_rectangular",
        "prompts": [
            "a rectangular or square watch case, dress watch",
            "a watch with a tank-style or rectangular case shape",
            "a rectangular wristwatch like a Cartier Tank or similar",
        ],
        "weight": 1.8,
    },
    {
        "key": "case_octagonal",
        "prompts": [
            "an octagonal watch case with an integrated bracelet",
            "a watch with a distinctive octagonal case like a Royal Oak or Nautilus",
            "a luxury sports watch with a geometric octagonal or multi-faceted case",
        ],
        "weight": 2.0,
    },
    {
        "key": "case_cushion",
        "prompts": [
            "a cushion-shaped watch case with rounded corners",
            "a watch with a cushion case shape, softer than rectangular",
        ],
        "weight": 1.5,
    },
    # ── Bezel type ───────────────────────────────────────────────────────────
    {
        "key": "bezel_diver",
        "prompts": [
            "a diver watch with a rotating bezel with minute markers and luminous pip",
            "a professional diving watch with a unidirectional rotating bezel",
            "a scuba dive watch with a black ceramic or metal rotating bezel",
        ],
        "weight": 1.8,
    },
    {
        "key": "bezel_tachymeter",
        "prompts": [
            "a watch with a tachymeter scale on the bezel for measuring speed",
            "a chronograph racing watch with tachymeter bezel markings",
        ],
        "weight": 1.5,
    },
    {
        "key": "bezel_fluted",
        "prompts": [
            "a watch with a fluted bezel with vertical grooves around the edge",
            "a Rolex-style fluted gold bezel with decorative ridges",
        ],
        "weight": 1.3,
    },
    {
        "key": "bezel_smooth",
        "prompts": [
            "a watch with a plain smooth fixed bezel without markings or texture",
            "a dress watch with a clean smooth bezel",
        ],
        "weight": 0.5,
    },
    {
        "key": "bezel_gmt",
        "prompts": [
            "a watch with a 24-hour rotating bezel for tracking a second time zone",
            "a GMT watch with a bi-color 24-hour bezel",
        ],
        "weight": 1.5,
    },
    # ── Hand style ───────────────────────────────────────────────────────────
    {
        "key": "hands_mercedes",
        "prompts": [
            "a watch with Mercedes-style hands with a circle and three-spoked design",
            "a watch with Rolex-style Mercedes hands on the dial",
        ],
        "weight": 1.5,
    },
    {
        "key": "hands_dauphine",
        "prompts": [
            "a watch with dauphine hands that are faceted and tapered like a leaf",
            "a dress watch with elegant dauphine-style hands",
        ],
        "weight": 1.2,
    },
    {
        "key": "hands_snowflake",
        "prompts": [
            "a Grand Seiko watch with snowflake hands, broad flat paddle-shaped hands",
            "a watch with distinctive snowflake hands, flat wide hour hand",
        ],
        "weight": 1.8,
    },
    {
        "key": "hands_skeleton",
        "prompts": [
            "a skeleton watch with openwork dial showing the movement through the dial",
            "a watch with a skeletonized dial showing gears and movement underneath",
        ],
        "weight": 2.0,
    },
    # ── Watch style ─────────────────────────────────────────────────────────
    {
        "key": "style_dress",
        "prompts": [
            "an elegant thin dress watch with a clean minimalist dial",
            "a formal dress wristwatch with a simple dial and slim profile",
        ],
        "weight": 1.2,
    },
    {
        "key": "style_diver",
        "prompts": [
            "a professional diving watch with high water resistance and diver bezel",
            "a sports diver watch rated 200m or more water resistant",
        ],
        "weight": 1.5,
    },
    {
        "key": "style_pilot",
        "prompts": [
            "an aviator pilot watch with large Arabic numerals and oversized crown",
            "a flight instrument-inspired pilot watch with a legible bold dial",
        ],
        "weight": 1.5,
    },
    {
        "key": "style_field",
        "prompts": [
            "a military field watch with plain legible dial and canvas strap",
            "a robust field watch with high contrast dial and utilitarian design",
        ],
        "weight": 1.2,
    },
    # ── Index type ───────────────────────────────────────────────────────────
    {
        "key": "indices_arabic",
        "prompts": [
            "a watch with Arabic numeral hour markers on the dial",
            "a watch showing 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 Arabic numbers",
        ],
        "weight": 1.0,
    },
    {
        "key": "indices_roman",
        "prompts": [
            "a watch with Roman numeral hour markers on the dial: I II III IV V VI",
            "a classic dress watch with Roman numeral indices",
        ],
        "weight": 1.0,
    },
    {
        "key": "indices_baton",
        "prompts": [
            "a watch with baton or stick hour markers, no numerals",
            "a watch with simple rectangular baton index hour markers",
        ],
        "weight": 0.7,
    },
    {
        "key": "indices_even_only",
        "prompts": [
            "a watch with hour markers only at 12, 3, 6, and 9 o'clock positions",
            "a watch showing only even-hour markers, minimal indices",
            "a watch with hour markers only at even positions on the dial",
        ],
        "weight": 1.3,
    },
]

# ─── DB field → concept mapping ───────────────────────────────────────────────

def _parse_complications(watch_complications) -> List[str]:
    if not watch_complications:
        return []
    if isinstance(watch_complications, list):
        return [str(c).lower() for c in watch_complications]
    if isinstance(watch_complications, str):
        return [watch_complications.lower()]
    return []


def _parse_dial_style(watch) -> str:
    raw = (watch.dial_style or "").lower()
    return raw


def compute_candidate_features(watch) -> Dict[str, float]:
    """
    Given a WatchReference ORM object, return a dict {concept_key: score [0..1]}
    based purely on structured metadata fields.
    """
    features: Dict[str, float] = {}
    comps = _parse_complications(watch.dial_complications)
    dial = _parse_dial_style(watch)
    style = (watch.watch_style or "").lower()
    shape = (watch.case_shape or "").lower()
    bezel = (watch.bezel_type or "").lower() + " " + (watch.bezel_style or "").lower()
    hands = (watch.hand_style or "").lower()
    indices = (watch.dial_indices or "").lower()

    # Chronograph
    features["has_chronograph"] = 1.0 if "chronograph" in comps else 0.0
    # Small seconds
    features["has_small_seconds"] = (
        1.0 if ("small seconds" in indices or "small second" in (watch.dial_style or "").lower()
                or ("date" not in comps and "chronograph" not in comps and len(comps) <= 1 and style in ("dress", "sport")))
        else 0.0
    )
    # GMT
    features["has_gmt"] = 1.0 if ("gmt" in comps or style == "gmt") else 0.0
    # Date
    features["has_date"] = 1.0 if "date" in comps else 0.0
    # Moonphase
    features["has_moonphase"] = 1.0 if "moonphase" in comps else 0.0

    # Dial style — values from watchbase: Sunburst, Guilloche, Gradient, Matte, Gloss
    features["dial_sector"] = 1.0 if "sector" in dial else 0.0
    features["dial_california"] = 1.0 if "california" in dial else 0.0
    features["dial_guilloche"] = 1.0 if any(x in dial for x in ["guilloché", "guilloche", "engine"]) else 0.0
    # "Gradient" in watchbase = fumé dial (gradual color change center → rim)
    features["dial_fume"] = 1.0 if any(x in dial for x in ["fumé", "fume", "gradient"]) else 0.0
    features["dial_sunburst"] = 1.0 if any(x in dial for x in ["sunburst", "sunray", "radial"]) else 0.0
    features["dial_plain"] = 1.0 if not any(features[k] for k in ["dial_sector", "dial_california", "dial_guilloche", "dial_fume", "dial_sunburst"]) else 0.0

    # Case shape
    features["case_round"] = 1.0 if shape in ("round", "circular", "") else 0.0
    features["case_rectangular"] = 1.0 if shape in ("rectangular", "square") else 0.0
    features["case_octagonal"] = 1.0 if shape in ("octagonal", "octagon") else 0.0
    features["case_cushion"] = 1.0 if "cushion" in shape else 0.0

    # Bezel — watchbase values: bezel_type=rotating_uni/fixed; bezel_style="Rotating, 0-60 (Dive)", "Tachymeter", "Gem-Set", "Rotating, 24 Hour"
    features["bezel_diver"] = 1.0 if any(x in bezel for x in ["dive", "0-60", "rotating_uni", "rotating"]) else 0.0
    features["bezel_tachymeter"] = 1.0 if any(x in bezel for x in ["tachymeter", "tachy"]) else 0.0
    features["bezel_fluted"] = 1.0 if "fluted" in bezel else 0.0
    # GMT/pilot style 24hr rotating
    features["bezel_gmt"] = 1.0 if "24 hour" in bezel or "24-hour" in bezel else 0.0
    features["bezel_smooth"] = 1.0 if (bezel.strip() in ("none", "") or ("fixed" in (watch.bezel_type or "").lower() and "tachymeter" not in bezel and "fluted" not in bezel)) else 0.0

    # Hands — watchbase values: stick, dauphine, sword, alpha, feuille, mercedes, arrow, baton, snowflake
    features["hands_mercedes"] = 1.0 if any(x in hands for x in ["mercedes", "rolex professional"]) else 0.0
    # dauphine + feuille (leaf/feuille) + lancette + cathedrale = faceted/elegant hands
    features["hands_dauphine"] = 1.0 if any(x in hands for x in ["dauphine", "feuille", "leaf", "lancette", "cathedrale", "poire"]) else 0.0
    features["hands_snowflake"] = 1.0 if "snowflake" in hands else 0.0
    features["hands_skeleton"] = 1.0 if "skeleton" in hands or "openwork" in (watch.dial_style or "").lower() else 0.0

    # Watch style
    features["style_dress"] = 1.0 if style in ("dress",) else 0.0
    features["style_diver"] = 1.0 if style == "diver" else 0.0
    features["style_pilot"] = 1.0 if style == "pilot" else 0.0
    features["style_field"] = 1.0 if style == "field" else 0.0

    # Indices — watchbase values: "Stick / Dot", "Mixed", "Arabic Numerals", "Roman Numerals", "Gem-Set Indexes"
    features["indices_arabic"] = 1.0 if "arabic" in indices else 0.0
    features["indices_roman"] = 1.0 if "roman" in indices else 0.0
    # "Stick / Dot" = baton/index markers
    features["indices_baton"] = 1.0 if any(x in indices for x in ["stick", "dot", "baton", "bar", "index"]) else 0.0
    # Panerai California / sector-style = often mixed numerals
    features["indices_even_only"] = 1.0 if "mixed" in indices else 0.0

    return features


# ─── Query feature inference via CLIP text-image similarity ───────────────────

_clip_model = None
_clip_loaded = False


def _load_clip():
    global _clip_model, _clip_loaded
    if _clip_loaded:
        return
    try:
        from sentence_transformers import SentenceTransformer
        _clip_model = SentenceTransformer("clip-ViT-B-32")
        logger.info("Watch features CLIP model loaded.")
    except Exception as e:
        logger.warning(f"Could not load CLIP for feature inference: {e}")
    _clip_loaded = True


def infer_query_features(image_embedding: List[float]) -> Dict[str, float]:
    """
    Given a CLIP image embedding of the query photo, score each concept
    by comparing to CLIP text embeddings of the concept prompts.

    Returns {concept_key: score [0..1]} — how strongly the query image
    matches each watchmaking concept.
    """
    _load_clip()
    if _clip_model is None:
        # Fallback: return neutral (0.5) for all concepts
        return {c["key"]: 0.5 for c in CONCEPTS}

    query_vec = np.array(image_embedding, dtype=np.float32)
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)

    features: Dict[str, float] = {}

    for concept in CONCEPTS:
        # Get text embeddings for all prompts of this concept
        prompt_scores = []
        for prompt in concept["prompts"]:
            try:
                text_vec = _clip_model.encode(prompt)
                text_vec = text_vec / (np.linalg.norm(text_vec) + 1e-8)
                # Cosine similarity
                sim = float(np.dot(query_norm, text_vec))
                # CLIP cosine range is typically -1 to 1; normalize to 0..1
                prompt_scores.append((sim + 1) / 2)
            except Exception as e:
                logger.debug(f"CLIP text encode error for '{prompt}': {e}")
                prompt_scores.append(0.5)

        # Max-pool across prompts (any strong prompt is enough)
        features[concept["key"]] = max(prompt_scores) if prompt_scores else 0.5

    return features


# ─── Feature score computation ────────────────────────────────────────────────

def compute_feature_score(
    query_features: Dict[str, float],
    candidate_features: Dict[str, float],
) -> float:
    """
    Compare query inferred features vs candidate structured features.

    For each concept:
      - If query strongly indicates concept (score > 0.6) and candidate matches (1.0)   → reward
      - If query strongly indicates concept (score > 0.6) and candidate does NOT match  → penalise
      - If query strongly indicates ABSENCE (score < 0.4) and candidate matches (1.0)   → penalise
      - Otherwise: neutral contribution

    Returns a score in [0, 1].
    """
    concept_map = {c["key"]: c["weight"] for c in CONCEPTS}

    total_weight = 0.0
    weighted_score = 0.0

    for concept in CONCEPTS:
        key = concept["key"]
        weight = concept["weight"]
        q_score = query_features.get(key, 0.5)
        c_score = candidate_features.get(key, 0.0)

        if q_score > 0.60:
            # Query likely has this feature
            # Candidate match → full credit; mismatch → zero credit
            match = c_score
            total_weight += weight
            weighted_score += weight * match

        elif q_score < 0.40:
            # Query likely does NOT have this feature
            # Candidate absence → full credit; candidate match → zero credit
            match = 1.0 - c_score
            total_weight += weight
            weighted_score += weight * match

        # 0.40–0.60: uncertain, skip

    if total_weight == 0:
        return 0.5  # No confident features detected → neutral

    return weighted_score / total_weight


# ─── Main re-ranking function ─────────────────────────────────────────────────

def rerank(
    query_embedding: List[float],
    clip_results: List[Dict],  # [{id, score (0-100)}, ...]
    candidate_features: Dict[int, Dict[str, float]],  # {watch_id: features}
) -> List[Dict]:
    """
    Re-rank CLIP results using hybrid CLIP + structural feature score.

    Args:
        query_embedding: 512-dim CLIP embedding of the query image
        clip_results:    Initial CLIP ranking [{id, score}] (score 0-100)
        candidate_features: Pre-computed feature dict for each watch id

    Returns:
        Re-ranked list of [{id, score, clip_score, feature_score}]
    """
    query_features = infer_query_features(query_embedding)

    logger.debug(f"Query features (top): { {k: round(v,3) for k, v in sorted(query_features.items(), key=lambda x: -x[1])[:8]} }")

    reranked = []
    for item in clip_results:
        wid = item["id"]
        clip_score_100 = item["score"]
        clip_score_01 = clip_score_100 / 100.0

        cand_features = candidate_features.get(wid, {})
        feat_score = compute_feature_score(query_features, cand_features)

        # Hybrid score
        hybrid_01 = CLIP_WEIGHT * clip_score_01 + FEATURE_WEIGHT * feat_score
        hybrid_100 = round(min(max(hybrid_01 * 100, 0), 100), 1)

        reranked.append({
            "id": wid,
            "score": hybrid_100,
            "clip_score": round(clip_score_100, 1),
            "feature_score": round(feat_score * 100, 1),
        })

    reranked.sort(key=lambda x: x["score"], reverse=True)
    return reranked
