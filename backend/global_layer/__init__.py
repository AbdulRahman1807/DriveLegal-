"""
backend/global_layer/__init__.py
---------------------------------
Public API for the Global Intelligence Layer.

Exposes only the symbols needed by the integration hook.
Internal implementation details remain unexported.
"""

from backend.global_layer.global_context_builder import (
    GlobalContext,
    build_global_context,
)
from backend.global_layer.response_guardrail import (
    sanitize_reply,
    build_offline_response,
    build_error_response,
    is_reply_safe,
)
from backend.global_layer.connectivity_checker import (
    ConnectivityMode,
    ConnectivityStatus,
)
from backend.global_layer.country_detector import detect_country
from backend.global_layer.global_data import (
    CountryMetadata,
    get_country_by_iso,
    get_country_by_name,
    get_default_country,
)
from backend.global_layer.global_answer_engine import get_global_answer
from backend.global_layer.fallback_evaluator import (
    evaluate_and_fallback,
    FallbackDecision,
    ConfidenceTier,
)
from backend.global_layer.rxl import (
    rxl_prepare,
    rxl_finalize,
    RXLResult,
    QueryIntent,
    classify_intent,
)

__all__ = [
    # Context building (primary integration surface)
    "GlobalContext",
    "build_global_context",
    # Fallback evaluation (unified confidence-tier routing)
    "evaluate_and_fallback",
    "FallbackDecision",
    "ConfidenceTier",
    # International / general answer engine
    "get_global_answer",
    # Response Experience Layer (RXL)
    "rxl_prepare",
    "rxl_finalize",
    "RXLResult",
    "QueryIntent",
    "classify_intent",
    # Guardrail
    "sanitize_reply",
    "build_offline_response",
    "build_error_response",
    "is_reply_safe",
    # Connectivity
    "ConnectivityMode",
    "ConnectivityStatus",
    # Detection
    "detect_country",
    # Data
    "CountryMetadata",
    "get_country_by_iso",
    "get_country_by_name",
    "get_default_country",
]
