"""
fallback_evaluator.py — Global Intelligence Layer
---------------------------------------------------
Evaluates RetrievalResult confidence and determines whether the existing
ChatEngine output is sufficient or whether Global Fallback Mode must activate.

Confidence Tiers
----------------
HIGH   (≥ 0.5, chunks > 0)  → ChatEngine is sufficient; pass through
MEDIUM (0.0 < score < 0.5, chunks > 0) → ChatEngine + fallback enrichment hint
LOW    (score = 0.0 OR chunks == 0)    → Global Fallback Mode

In LOW tier the evaluator delegates to get_global_answer() which calls
Gemini with a jurisdiction-aware prompt that never fabricates legal facts.

Design constraints:
  - Never raises; always returns a FallbackDecision
  - Never modifies the original query or RetrievalResult
  - Never exposes pipeline internals to users
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from backend.global_layer.global_data import CountryMetadata

logger = logging.getLogger(__name__)

# Confidence thresholds
_HIGH_THRESHOLD = 0.5    # At or above → ChatEngine handles it well
_LOW_THRESHOLD  = 0.0    # Exactly 0.0 → definitely need fallback


class ConfidenceTier(str, Enum):
    HIGH   = "HIGH"    # Retrieval succeeded; ChatEngine answer is reliable
    MEDIUM = "MEDIUM"  # Partial retrieval; ChatEngine with a hint
    LOW    = "LOW"     # Retrieval failed; Global Fallback Mode required


@dataclass
class FallbackDecision:
    """
    Result of confidence evaluation.

    Fields
    ------
    tier : ConfidenceTier
        The determined confidence tier for this retrieval result.
    needs_fallback : bool
        True if the Global Fallback engine should generate the response.
    fallback_reply : str | None
        Pre-generated fallback reply (populated only when needs_fallback=True
        and get_global_answer() succeeded). None means use ChatEngine.
    """
    tier: ConfidenceTier
    needs_fallback: bool
    fallback_reply: Optional[str] = None


def _classify_tier(confidence_score: float, chunk_count: int) -> ConfidenceTier:
    """
    Map a (confidence_score, chunk_count) pair to a ConfidenceTier.

    The chunk_count is the primary gate: even a non-zero confidence_score
    is meaningless when the LLM will receive empty LEGAL CONTEXT.
    """
    if chunk_count == 0 or confidence_score <= _LOW_THRESHOLD:
        return ConfidenceTier.LOW
    if confidence_score >= _HIGH_THRESHOLD:
        return ConfidenceTier.HIGH
    return ConfidenceTier.MEDIUM


async def evaluate_and_fallback(
    query: str,
    confidence_score: float,
    chunk_count: int,
    country: CountryMetadata,
) -> FallbackDecision:
    """
    Evaluate retrieval quality and, if needed, generate a fallback reply.

    Parameters
    ----------
    query : str
        The original user query (never mutated).
    confidence_score : float
        The confidence_score from RetrievalResult (0.0–1.0).
    chunk_count : int
        Number of chunks in RetrievalResult.chunks.
    country : CountryMetadata
        The detected jurisdiction from the Global Intelligence Layer.

    Returns
    -------
    FallbackDecision
        Always returns; never raises.
    """
    try:
        tier = _classify_tier(confidence_score, chunk_count)

        logger.debug(
            "fallback_evaluator.tier confidence=%.2f chunks=%d tier=%s country=%s",
            confidence_score, chunk_count, tier.value, country.iso_code,
        )

        # HIGH or MEDIUM: ChatEngine can handle it — no fallback needed
        if tier in (ConfidenceTier.HIGH, ConfidenceTier.MEDIUM):
            return FallbackDecision(tier=tier, needs_fallback=False)

        # LOW: generate a fallback reply via the global answer engine
        # Import here to avoid circular imports at module load time
        from backend.global_layer.global_answer_engine import get_global_answer

        try:
            reply = await get_global_answer(query=query, country=country)
        except Exception:
            logger.exception("fallback_evaluator.get_global_answer_failed")
            reply = None

        if reply:
            return FallbackDecision(
                tier=tier,
                needs_fallback=True,
                fallback_reply=reply,
            )

        # get_global_answer returned None (API key missing, timeout, etc.)
        # Signal that fallback is needed but no reply was produced —
        # routes.py will use a safe generic response in this case.
        return FallbackDecision(tier=tier, needs_fallback=True, fallback_reply=None)

    except Exception:
        logger.exception("fallback_evaluator.unexpected_error — not applying fallback")
        # Safe default: don't activate fallback; let ChatEngine handle it
        return FallbackDecision(tier=ConfidenceTier.HIGH, needs_fallback=False)
