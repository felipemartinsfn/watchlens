"""
Watch structural feature extraction and hybrid re-ranking for image search.

Strategy: CLIP text-image similarity cannot reliably distinguish watchmaking concepts
(all scores cluster between 0.63–0.66 with ViT-B/32). Instead, we use a two-layer
approach:

LAYER 1 — Structural candidate features:
  Every watch in the DB gets a feature vector computed purely from its metadata
  (complications, dial_style, case_shape, bezel_type, hand_style, dial_indices, watch_style).

LAYER 2 — Consensus voting for query features:
  The top-N CLIP candidates vote on what features the query image likely has.
  If 60%+ of the top candidates share a feature → the query probably has it too.
  If <20% of top candidates have a feature → the query probably does NOT have it.

  This exploits CLIP's genuine strength (visual similarity) to infer structure:
  "this image looks like these watches → it probably shares their features."

SCORING:
  feature_score(candidate) = how well candidate's features match inferred query features
  final_score = CLIP_WEIGHT * clip_score + FEATURE_WEIGHT * feature_score

  Hard penalties applied for clear contradictions:
  - Query inferred as NON-chronograph → chronograph candidate: -25 pts
  - Query inferred as NON-diver → diver bezel candidate: -15 pts
  - Query inferred as rectangular case → round candidate: -20 pts
  - etc.
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# ─── Weights ──────────────────────────────────────────────────────────────────
CLIP_WEIGHT = 0.40
FEATURE_WEIGHT = 0.60

# How many top CLIP candidates to use for consensus voting
CONSENSUS_TOP_N = 8

# Consensus thresholds
CONSENSUS_HAS = 0.60    # >60% of top-N have feature → query likely has it
CONSENSUS_LACKS = 0.25  # <25% of top-N have feature → query likely lacks it

# ─── Feature extraction from DB metadata ──────────────────────────────────────

def _parse_complications(dial_complications) -> List[str]:
    if not dial_complications:
        return []
    if isinstance(dial_complications, list):
        return [str(c).lower() for c in dial_complications]
    if isinstance(dial_complications, str):
        return [dial_complications.lower()]
    return []


def compute_candidate_features(watch) -> Dict[str, float]:
    """
    Extract a binary feature vector from a WatchReference ORM object.
    Returns {feature_key: 1.0 or 0.0} based on structured metadata.

    Feature groups and their keys:
      Complications: has_chronograph, has_small_seconds, has_gmt, has_date, has_moonphase
      Dial:          dial_sector, dial_california, dial_guilloche, dial_fume,
                     dial_sunburst, dial_plain
      Case:          case_round, case_rectangular, case_octagonal, case_cushion
      Bezel:         bezel_diver, bezel_tachymeter, bezel_fluted, bezel_gmt, bezel_smooth
      Hands:         hands_mercedes, hands_dauphine, hands_snowflake, hands_skeleton
      Style:         style_dress, style_diver, style_pilot, style_field, style_racing
      Indices:       indices_arabic, indices_roman, indices_baton, indices_mixed
    """
    comps = _parse_complications(watch.dial_complications)
    dial  = (watch.dial_style or "").lower()
    style = (watch.watch_style or "").lower()
    shape = (watch.case_shape or "").lower()
    btype = (watch.bezel_type or "").lower()
    bstyle = (watch.bezel_style or "").lower()
    bezel = btype + " " + bstyle
    hands = (watch.hand_style or "").lower()
    indices = (watch.dial_indices or "").lower()

    f: Dict[str, float] = {}

    # ── Complications ─────────────────────────────────────────────────────────
    f["has_chronograph"]  = 1.0 if "chronograph" in comps else 0.0
    f["has_gmt"]          = 1.0 if "gmt" in comps or style == "gmt" else 0.0
    f["has_date"]         = 1.0 if "date" in comps else 0.0
    f["has_moonphase"]    = 1.0 if "moonphase" in comps else 0.0
    # Small seconds: a watch with exactly 1 subdial for running seconds (no chrono)
    # Heuristic: no chronograph + dress/sport/field style + no other complex complications
    non_chrono_comps = [c for c in comps if c not in ("date", "day")]
    f["has_small_seconds"] = (
        1.0 if (f["has_chronograph"] == 0.0
                and style in ("dress", "sport", "field", "pilot", "")
                and len(non_chrono_comps) <= 1)
        else 0.0
    )

    # ── Dial style ────────────────────────────────────────────────────────────
    # watchbase values: Sunburst, Guilloche, Gradient (=fumé), Matte, Gloss, None
    f["dial_sector"]    = 1.0 if "sector" in dial else 0.0
    f["dial_california"]= 1.0 if "california" in dial else 0.0
    f["dial_guilloche"] = 1.0 if any(x in dial for x in ["guilloche", "guilloché", "engine"]) else 0.0
    f["dial_fume"]      = 1.0 if any(x in dial for x in ["fumé", "fume", "gradient"]) else 0.0
    f["dial_sunburst"]  = 1.0 if any(x in dial for x in ["sunburst", "sunray", "radial"]) else 0.0
    f["dial_plain"]     = 1.0 if not any(f.get(k, 0) for k in [
        "dial_sector", "dial_california", "dial_guilloche", "dial_fume", "dial_sunburst"
    ]) else 0.0

    # ── Case shape ────────────────────────────────────────────────────────────
    # watchbase: round (420), cushion (45), rectangular (36), tonneau (13)
    f["case_round"]      = 1.0 if shape in ("round", "circular", "") else 0.0
    f["case_rectangular"]= 1.0 if shape in ("rectangular", "square", "tonneau") else 0.0
    f["case_octagonal"]  = 1.0 if shape in ("octagonal", "octagon") else 0.0
    f["case_cushion"]    = 1.0 if "cushion" in shape else 0.0

    # ── Bezel ─────────────────────────────────────────────────────────────────
    # watchbase bezel_type: rotating_uni, fixed, None
    # watchbase bezel_style: "Rotating, 0-60 (Dive)", "Tachymeter", "Gem-Set", "Rotating, 24 Hour"
    f["bezel_diver"]     = 1.0 if any(x in bezel for x in ["dive", "0-60", "rotating_uni"]) else 0.0
    f["bezel_tachymeter"]= 1.0 if "tachymeter" in bstyle else 0.0
    f["bezel_fluted"]    = 1.0 if "fluted" in bstyle else 0.0
    f["bezel_gmt"]       = 1.0 if "24 hour" in bstyle else 0.0
    f["bezel_smooth"]    = 1.0 if (
        btype == "fixed" and "tachymeter" not in bstyle
        and "fluted" not in bstyle and "gem" not in bstyle
    ) or btype == "" or btype == "none" else 0.0

    # ── Hands ─────────────────────────────────────────────────────────────────
    # watchbase: stick(247), dauphine(58), sword(51), alpha(41), feuille(33),
    #            mercedes(5), arrow, baton, snowflake, breguet, lancette, cathedrale
    f["hands_mercedes"]  = 1.0 if any(x in hands for x in ["mercedes", "rolex professional"]) else 0.0
    f["hands_dauphine"]  = 1.0 if any(x in hands for x in [
        "dauphine", "feuille", "leaf", "lancette", "cathedrale", "poire", "breguet"
    ]) else 0.0
    f["hands_baton"]     = 1.0 if any(x in hands for x in ["stick", "baton", "sword", "alpha", "arrow", "losange"]) else 0.0
    f["hands_snowflake"] = 1.0 if "snowflake" in hands else 0.0
    f["hands_skeleton"]  = 1.0 if "skeleton" in hands or "openwork" in dial else 0.0

    # ── Watch style ───────────────────────────────────────────────────────────
    f["style_dress"]  = 1.0 if style == "dress" else 0.0
    f["style_diver"]  = 1.0 if style == "diver" else 0.0
    f["style_pilot"]  = 1.0 if style == "pilot" else 0.0
    f["style_field"]  = 1.0 if style == "field" else 0.0
    f["style_racing"] = 1.0 if style in ("racing", "sport") else 0.0

    # ── Indices ───────────────────────────────────────────────────────────────
    # watchbase: "Stick / Dot"(230), "Mixed"(125), "Arabic Numerals"(65), "Roman Numerals"(47)
    f["indices_arabic"]  = 1.0 if "arabic" in indices else 0.0
    f["indices_roman"]   = 1.0 if "roman" in indices else 0.0
    f["indices_baton"]   = 1.0 if any(x in indices for x in ["stick", "dot", "baton", "bar"]) else 0.0
    f["indices_mixed"]   = 1.0 if "mixed" in indices else 0.0  # California, sector-style

    return f


# ─── Feature importance weights for scoring ───────────────────────────────────
# Higher = this feature carries more weight when present/absent

FEATURE_WEIGHTS: Dict[str, float] = {
    # Most discriminating — easy to confuse visually
    "has_chronograph":   3.0,
    "has_small_seconds": 3.0,
    "bezel_diver":       2.5,
    "bezel_tachymeter":  2.5,
    "case_rectangular":  2.5,
    "case_octagonal":    2.5,
    "dial_sector":       2.0,
    "dial_california":   2.0,
    "dial_guilloche":    1.8,
    "dial_fume":         1.5,
    "style_diver":       1.5,
    "style_pilot":       1.5,
    "style_racing":      1.2,
    "bezel_fluted":      1.5,
    "bezel_gmt":         1.5,
    "hands_mercedes":    1.5,
    "hands_snowflake":   1.8,
    "hands_dauphine":    1.2,
    "case_cushion":      1.5,
    "has_moonphase":     1.5,
    "has_gmt":           1.2,
    # Lower weight — less visually distinctive
    "has_date":          0.8,
    "dial_sunburst":     0.8,
    "style_dress":       0.8,
    "style_field":       0.8,
    "indices_arabic":    1.0,
    "indices_roman":     1.0,
    "indices_mixed":     1.2,
    "indices_baton":     0.5,
    "dial_plain":        0.3,
    "hands_baton":       0.5,
    "bezel_smooth":      0.3,
    "case_round":        0.3,
    "hands_skeleton":    1.5,
}

ALL_FEATURE_KEYS = list(FEATURE_WEIGHTS.keys())


# ─── Consensus voting ─────────────────────────────────────────────────────────

def infer_query_features_by_consensus(
    clip_results: List[Dict],               # [{id, score}, ...] sorted by score desc
    candidate_features: Dict[int, Dict],    # {watch_id: features}
    top_n: int = CONSENSUS_TOP_N,
) -> Dict[str, float]:
    """
    Infer query features by consensus of top-N CLIP candidates.

    For each feature, compute the fraction of top-N candidates that have it.
    Returns {feature_key: fraction [0..1]} — how prevalent this feature is
    among candidates that CLIP thinks look most like the query.

    Interpretation:
      fraction > CONSENSUS_HAS  → query probably HAS this feature
      fraction < CONSENSUS_LACKS → query probably LACKS this feature
      in between                → uncertain
    """
    top = clip_results[:top_n]
    if not top:
        return {k: 0.5 for k in ALL_FEATURE_KEYS}

    fractions: Dict[str, float] = {}
    for key in ALL_FEATURE_KEYS:
        votes = sum(
            candidate_features.get(item["id"], {}).get(key, 0.0)
            for item in top
        )
        fractions[key] = votes / len(top)

    logger.debug(
        f"Consensus top-{len(top)}: "
        + ", ".join(f"{k}={v:.2f}" for k, v in sorted(fractions.items(), key=lambda x: -x[1])[:8])
    )
    return fractions


# ─── Feature-based score computation ─────────────────────────────────────────

def compute_feature_score(
    query_fractions: Dict[str, float],
    candidate_features: Dict[str, float],
) -> float:
    """
    Score a candidate against inferred query feature fractions.

    For features where consensus is confident:
      - If query LIKELY HAS feature (fraction > CONSENSUS_HAS):
          candidate has it → full credit; doesn't → 0 credit
      - If query LIKELY LACKS feature (fraction < CONSENSUS_LACKS):
          candidate lacks it → full credit; has it → 0 credit
      - Uncertain → skip (weight = 0)

    Returns score in [0, 1].
    """
    total_weight = 0.0
    weighted_score = 0.0

    for key in ALL_FEATURE_KEYS:
        weight = FEATURE_WEIGHTS.get(key, 1.0)
        q_frac = query_fractions.get(key, 0.5)
        c_val  = candidate_features.get(key, 0.0)

        if q_frac > CONSENSUS_HAS:
            # Query likely HAS this feature → reward match
            total_weight += weight
            weighted_score += weight * c_val

        elif q_frac < CONSENSUS_LACKS:
            # Query likely LACKS this feature → reward absence
            total_weight += weight
            weighted_score += weight * (1.0 - c_val)

        # else: uncertain — contribute nothing

    if total_weight == 0:
        return 0.5  # No confident consensus features → neutral

    return weighted_score / total_weight


# ─── Hard penalty rules ───────────────────────────────────────────────────────
# Applied on top of the weighted score for egregious mismatches.
# These represent contradictions so obvious a human would reject them immediately.

def compute_hard_penalties(
    query_fractions: Dict[str, float],
    candidate_features: Dict[str, float],
) -> float:
    """
    Returns a penalty in [0, 1] to subtract from the final 0-100 score.
    0.0 = no penalty; higher values = worse penalty.
    """
    penalty = 0.0

    # ── Chronograph mismatch ─────────────────────────────────────────────────
    # If query consensus strongly says no-chrono, but candidate IS a chrono
    if (query_fractions.get("has_chronograph", 0.5) < 0.20
            and candidate_features.get("has_chronograph", 0) == 1.0):
        penalty += 0.22  # -22 pts out of 100

    # If query consensus strongly says IS a chrono, but candidate has NO chrono
    if (query_fractions.get("has_chronograph", 0.5) > 0.80
            and candidate_features.get("has_chronograph", 0) == 0.0):
        penalty += 0.18

    # ── Diver bezel mismatch ─────────────────────────────────────────────────
    if (query_fractions.get("bezel_diver", 0.5) < 0.20
            and candidate_features.get("bezel_diver", 0) == 1.0):
        penalty += 0.18

    if (query_fractions.get("bezel_diver", 0.5) > 0.75
            and candidate_features.get("bezel_diver", 0) == 0.0):
        penalty += 0.14

    # ── Tachymeter mismatch ──────────────────────────────────────────────────
    if (query_fractions.get("bezel_tachymeter", 0.5) < 0.20
            and candidate_features.get("bezel_tachymeter", 0) == 1.0):
        penalty += 0.14

    # ── Case shape contradiction ─────────────────────────────────────────────
    if (query_fractions.get("case_rectangular", 0.5) > 0.70
            and candidate_features.get("case_rectangular", 0) == 0.0):
        penalty += 0.18

    if (query_fractions.get("case_rectangular", 0.5) < 0.15
            and candidate_features.get("case_rectangular", 0) == 1.0):
        penalty += 0.15

    if (query_fractions.get("case_octagonal", 0.5) < 0.15
            and candidate_features.get("case_octagonal", 0) == 1.0):
        penalty += 0.12

    # ── Dial style contradiction ─────────────────────────────────────────────
    if (query_fractions.get("dial_california", 0.5) < 0.15
            and candidate_features.get("dial_california", 0) == 1.0):
        penalty += 0.14

    if (query_fractions.get("dial_sector", 0.5) < 0.15
            and candidate_features.get("dial_sector", 0) == 1.0):
        penalty += 0.12

    return min(penalty, 0.50)  # cap at -50 pts


# ─── Main re-ranking function ─────────────────────────────────────────────────

def rerank(
    query_embedding: List[float],          # unused now, kept for API compat
    clip_results: List[Dict],              # [{id, score (0-100)}, ...]
    candidate_features: Dict[int, Dict],   # {watch_id: features}
) -> List[Dict]:
    """
    Re-rank CLIP results using consensus-voted structural features.

    Step 1: Top CONSENSUS_TOP_N candidates vote on query features.
    Step 2: Score each candidate against voted features + apply hard penalties.
    Step 3: Hybrid = CLIP_WEIGHT * clip_score + FEATURE_WEIGHT * feature_score - penalty.
    Step 4: Sort descending.

    Returns list of [{id, score, clip_score, feature_score, penalty}]
    """
    # Step 1: consensus voting on query features
    query_fractions = infer_query_features_by_consensus(
        clip_results, candidate_features, top_n=CONSENSUS_TOP_N
    )

    if logger.isEnabledFor(logging.DEBUG):
        confident_has   = [k for k, v in query_fractions.items() if v > CONSENSUS_HAS]
        confident_lacks = [k for k, v in query_fractions.items() if v < CONSENSUS_LACKS]
        logger.debug(f"  Query HAS:   {confident_has}")
        logger.debug(f"  Query LACKS: {confident_lacks}")

    reranked = []
    for item in clip_results:
        wid            = item["id"]
        clip_score_100 = item["score"]
        clip_score_01  = clip_score_100 / 100.0

        cand_f = candidate_features.get(wid, {})

        # Step 2: feature score + hard penalties
        feat_score  = compute_feature_score(query_fractions, cand_f)
        penalty     = compute_hard_penalties(query_fractions, cand_f)

        # Step 3: hybrid
        hybrid_01  = CLIP_WEIGHT * clip_score_01 + FEATURE_WEIGHT * feat_score - penalty
        hybrid_100 = round(min(max(hybrid_01 * 100, 0), 100), 1)

        reranked.append({
            "id":            wid,
            "score":         hybrid_100,
            "clip_score":    round(clip_score_100, 1),
            "feature_score": round(feat_score * 100, 1),
            "penalty":       round(penalty * 100, 1),
        })

    reranked.sort(key=lambda x: x["score"], reverse=True)
    return reranked


# ─── Legacy stub (kept for import compat if anything references it) ───────────

def infer_query_features(image_embedding: List[float]) -> Dict[str, float]:
    """Deprecated: CLIP text inference doesn't have enough resolution for watchmaking.
    Use infer_query_features_by_consensus() instead."""
    return {k: 0.5 for k in ALL_FEATURE_KEYS}
