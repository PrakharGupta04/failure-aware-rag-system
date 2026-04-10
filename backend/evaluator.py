"""
evaluator.py - Failure Detection & Evaluation Module

This is the core "intelligence" of the system:
  1. Decides whether a retrieval result is good enough to answer.
  2. Assigns a confidence level (High / Medium / Low).
  3. Generates a structured rejection response when confidence is too low.
  4. Logs every query + outcome to a JSONL file for analysis.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from config import (
    SIMILARITY_THRESHOLD,
    CONFIDENCE_BANDS,
    LOG_FILE,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# In-memory evaluation statistics (reset per server restart)
# ──────────────────────────────────────────────────────────────
_stats = {
    "total":    0,
    "answered": 0,
    "rejected": 0,
    "scores":   [],   # list of float max-similarity scores
}


# ════════════════════════════════════════════════════════════════
# Confidence banding
# ════════════════════════════════════════════════════════════════

def get_confidence(max_score: float) -> str:
    """
    Map a similarity score to a confidence label.

    Bands are defined in config.CONFIDENCE_BANDS:
      High   : ≥ 0.70
      Medium : 0.50 – 0.70
      Low    : 0.40 – 0.50
      (below threshold → rejected, not labelled)
    """
    for label, (lo, hi) in CONFIDENCE_BANDS.items():
        if lo <= max_score < hi:
            return label
    # Shouldn't reach here if threshold ≥ lowest band lower bound,
    # but provide a fallback.
    return "Low"


# ════════════════════════════════════════════════════════════════
# Failure detection
# ════════════════════════════════════════════════════════════════

def should_reject(scores: List[float], threshold: float = SIMILARITY_THRESHOLD) -> bool:
    """
    Return True if the retrieval is not reliable enough to generate an answer.

    Rule: reject when the MAXIMUM similarity score across all retrieved
    chunks is below *threshold*.
    """
    if not scores:
        return True
    return max(scores) < threshold


def build_rejection(
    query: str,
    scores: List[float],
    threshold: float = SIMILARITY_THRESHOLD,
) -> Dict[str, Any]:
    """
    Build a structured rejection payload.

    Returns a dict that the API can return directly as JSON.
    """
    max_score = max(scores) if scores else 0.0
    return {
        "status":     "rejected",
        "answer":     None,
        "confidence": None,
        "sources":    [],
        "rejection": {
            "message": (
                "I couldn't find sufficiently relevant information to answer "
                "this question confidently. Please try rephrasing your query "
                "or ask about a topic covered in the knowledge base."
            ),
            "reason": (
                f"Maximum retrieval similarity ({max_score:.4f}) is below the "
                f"required threshold of {threshold:.2f}."
            ),
            "max_similarity_score": round(max_score, 4),
            "threshold":            threshold,
        },
    }


# ════════════════════════════════════════════════════════════════
# Success response builder
# ════════════════════════════════════════════════════════════════

def build_success(
    query: str,
    answer: str,
    scores: List[float],
    sources: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a structured success payload.
    """
    max_score  = max(scores) if scores else 0.0
    confidence = get_confidence(max_score)

    return {
        "status":     "answered",
        "answer":     answer,
        "confidence": confidence,
        "sources":    sources,
        "rejection":  None,
        "meta": {
            "max_similarity_score": round(max_score, 4),
            "num_sources":          len(sources),
        },
    }


# ════════════════════════════════════════════════════════════════
# Logging / Statistics
# ════════════════════════════════════════════════════════════════

def log_query(
    query:   str,
    outcome: str,           # "answered" | "rejected"
    scores:  List[float],
    answer:  Optional[str] = None,
) -> None:
    """
    Append one record to the JSONL evaluation log and update in-memory stats.
    """
    # ── In-memory stats ───────────────────────────────────────
    _stats["total"]  += 1
    _stats["scores"].append(max(scores) if scores else 0.0)
    if outcome == "answered":
        _stats["answered"] += 1
    else:
        _stats["rejected"] += 1

    # ── File log ──────────────────────────────────────────────
    record = {
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "query":       query,
        "outcome":     outcome,
        "max_score":   round(max(scores), 4) if scores else 0.0,
        "all_scores":  [round(s, 4) for s in scores],
        "answer_len":  len(answer) if answer else 0,
    }

    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except OSError as e:
        logger.warning("Could not write eval log: %s", e)


def get_stats() -> Dict[str, Any]:
    """
    Return a summary of evaluation statistics collected so far.
    """
    scores = _stats["scores"]
    return {
        "total_queries":    _stats["total"],
        "answered":         _stats["answered"],
        "rejected":         _stats["rejected"],
        "answer_rate_pct":  (
            round(100 * _stats["answered"] / _stats["total"], 1)
            if _stats["total"] > 0 else 0.0
        ),
        "avg_max_score":    round(sum(scores) / len(scores), 4) if scores else 0.0,
        "min_max_score":    round(min(scores), 4)                if scores else 0.0,
        "max_max_score":    round(max(scores), 4)                if scores else 0.0,
    }
