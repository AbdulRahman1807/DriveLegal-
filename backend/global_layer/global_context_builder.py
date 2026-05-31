"""
global_context_builder.py — Global Intelligence Layer
-------------------------------------------------------
Orchestrates all sub-components to produce a GlobalContext object that
is invisibly injected into the existing chat pipeline.

Responsibilities:
  1. Detect the target country from the query.
  2. Check connectivity (ONLINE / OFFLINE).
  3. Build a hidden metadata block for LLM prompt enrichment.
  4. In OFFLINE mode, generate a safe, factual, metadata-only response
     when the user asks for restricted information (live legal data).

Design constraints:
  - READ + ENRICH + FORWARD only. Never produces legal answers.
  - Returns GlobalContext; the pipeline decides what to do with it.
  - Never crashes; always returns a valid GlobalContext even on failure.
  - The metadata block is INTERNAL ONLY — never shown to users.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from backend.global_layer.global_data import CountryMetadata, get_default_country
from backend.global_layer.country_detector import detect_country
from backend.global_layer.connectivity_checker import (
    ConnectivityStatus,
    ConnectivityMode,
    check_connectivity,
    ConnectivityStatus,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keywords that indicate the user wants live legal data (forbidden offline).
# ---------------------------------------------------------------------------
_LIVE_DATA_KEYWORDS = frozenset([
    "fine", "fines", "penalty", "penalties", "fee", "fees",
    "law", "laws", "regulation", "regulations", "rule", "rules",
    "amendment", "amendments", "court", "judgment", "judgement",
    "ruling", "act", "section", "clause", "latest", "recent",
    "current", "2023", "2024", "2025", "2026",
])


@dataclass
class GlobalContext:
    """
    Encapsulates all Global Intelligence Layer outputs for a single request.

    Fields
    ------
    country : CountryMetadata
        Detected jurisdiction metadata.
    connectivity : ConnectivityStatus
        Determined connectivity mode (ONLINE / OFFLINE).
    hidden_context_block : str
        Formatted metadata string for silent LLM prompt injection.
        MUST NOT be displayed to users.
    offline_safe_reply : str | None
        Pre-built factual reply (OFFLINE mode only) for queries that
        ask for live legal data. None when ONLINE or when the query
        is safe for offline answering.
    bypass : bool
        If True, the Global Layer encountered a critical failure and the
        caller must forward the original query unchanged, bypassing this layer.
    """
    country: CountryMetadata
    connectivity: ConnectivityStatus
    hidden_context_block: str
    offline_safe_reply: Optional[str] = None
    bypass: bool = False


async def build_global_context(
    query: str,
    session_country_iso: Optional[str] = None,
    user_preference_iso: Optional[str] = None,
) -> GlobalContext:
    """
    Build a GlobalContext for the given query.

    Parameters
    ----------
    query : str
        Raw user query. Never mutated.
    session_country_iso : str, optional
        ISO code from the active user session.
    user_preference_iso : str, optional
        ISO code from the user's saved preferences.

    Returns
    -------
    GlobalContext
        Always returns; never raises.
    """
    try:
        # ── Step 1: Country Detection ────────────────────────────────────
        country = detect_country(
            query=query,
            session_country_iso=session_country_iso,
            user_preference_iso=user_preference_iso,
        )

        # ── Step 2: Connectivity Check ───────────────────────────────────
        connectivity = await check_connectivity()

        # ── Step 3: Build Hidden Context Block ───────────────────────────
        hidden_block = _build_hidden_block(country, connectivity)

        # ── Step 4: Offline Gate ─────────────────────────────────────────
        offline_reply = None
        if connectivity.is_offline:
            offline_reply = _build_offline_reply(query, country)

        logger.debug(
            "global_context_builder.built country=%s mode=%s has_offline_reply=%s",
            country.iso_code,
            connectivity.mode.value,
            offline_reply is not None,
        )

        return GlobalContext(
            country=country,
            connectivity=connectivity,
            hidden_context_block=hidden_block,
            offline_safe_reply=offline_reply,
            bypass=False,
        )

    except Exception:
        # Fail-safe: critical failure → return bypass context so the caller
        # can forward the original query untouched.
        logger.exception("global_context_builder.critical_failure — bypass activated")
        return _make_bypass_context()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _build_hidden_block(country: CountryMetadata, connectivity: ConnectivityStatus) -> str:
    """
    Compose the internal metadata block injected into the LLM prompt.
    This string is NEVER shown to users.
    """
    mode_note = (
        "Connectivity: ONLINE — live retrieval active."
        if connectivity.is_online
        else "Connectivity: OFFLINE — respond using metadata and general knowledge only."
    )
    return (
        f"[GLOBAL INTELLIGENCE LAYER — INTERNAL CONTEXT]\n"
        f"{country.as_context_block()}\n"
        f"{mode_note}\n"
        f"[END INTERNAL CONTEXT]"
    )


# Keywords that suggest the user is asking about metadata we have offline.
_METADATA_KEYWORDS = frozenset([
    "emergency", "emergency number", "helpline", "dial", "call",
    "driving side", "left side", "right side", "which side",
    "transport authority", "authority", "official", "website", "portal",
    "language", "languages", "spoken",
    "legal system", "common law", "civil law",
])


def _build_offline_reply(query: str, country: CountryMetadata) -> Optional[str]:
    """
    Build a safe, factual offline reply.

    Two cases:
      1. Query needs live legal data (fines, laws, amendments) → polite
         unavailability notice with emergency number + official source.
      2. Query is about metadata we hold (emergency number, driving side,
         authority, etc.) → answer directly from CountryMetadata.

    Returns None only when the query is neither case and should be allowed
    to proceed to the (online-only) RAG pipeline.
    """
    query_lower = query.lower()
    needs_live_data = any(kw in query_lower for kw in _LIVE_DATA_KEYWORDS)

    # Case 1: live legal data requested — unavailable offline
    if needs_live_data:
        sources = ", ".join(country.official_sources[:2])
        return (
            f"You're asking about a legal matter related to {country.country_name}. "
            f"I'm currently operating without a live database connection, so I can't "
            f"provide specific information on fines, current laws, or recent amendments right now.\n\n"
            f"Here's what I can share from general information:\n"
            f"- **Emergency number** in {country.country_name}: **{country.emergency_number}**\n"
            f"- **Transport authority**: {country.transport_authority}\n"
            f"- **Official sources**: {sources}\n\n"
            f"Please check {country.official_sources[0]} for authoritative details, "
            f"or try again once your connection is restored."
        )

    # Case 2: metadata query — answer directly from what we have
    is_metadata_query = any(kw in query_lower for kw in _METADATA_KEYWORDS)
    if is_metadata_query:
        languages = ", ".join(country.languages)
        sources = ", ".join(country.official_sources[:2])
        return (
            f"Here's some general information about {country.country_name} "
            f"that I can share without needing a live connection:\n\n"
            f"- **Emergency number**: {country.emergency_number}\n"
            f"- **Driving side**: {country.driving_side}\n"
            f"- **Transport authority**: {country.transport_authority}\n"
            f"- **Legal system**: {country.legal_system}\n"
            f"- **Languages**: {languages}\n"
            f"- **Official sources**: {sources}\n\n"
            f"For live legal queries, please reconnect and ask again."
        )

    # Neither live-data nor metadata — allow to fall through to the pipeline.
    return None


def _make_bypass_context() -> GlobalContext:
    """
    Returns a bypass GlobalContext using safe defaults.
    Signals to the caller that the Global Layer must be skipped entirely.
    """
    from backend.global_layer.connectivity_checker import ConnectivityMode

    default_country = get_default_country()
    bypass_connectivity = ConnectivityStatus(
        mode=ConnectivityMode.ONLINE,
        reason="Bypass activated due to Global Layer failure",
    )
    return GlobalContext(
        country=default_country,
        connectivity=bypass_connectivity,
        hidden_context_block="",
        offline_safe_reply=None,
        bypass=True,
    )
