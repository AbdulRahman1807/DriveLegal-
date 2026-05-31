"""
country_detector.py — Global Intelligence Layer
-------------------------------------------------
Detects the target country/jurisdiction from a user query.

Detection priority order:
  1. Explicit country mention in the query text
  2. Session-level country preference (passed in by caller)
  3. User profile preference (passed in by caller)
  4. System default → India

Design constraints:
  - Never raises exceptions; always returns a valid CountryMetadata.
  - Never modifies query text; read-only analysis.
  - Never surfaces detection logic to users.
"""

import re
import logging
from typing import Optional

from backend.global_layer.global_data import (
    CountryMetadata,
    get_all_aliases,
    get_country_by_iso,
    get_default_country,
)

logger = logging.getLogger(__name__)

# Build a single compiled regex from all known aliases, longest-first to
# prevent "us" matching before "united states".
def _build_alias_pattern() -> re.Pattern:
    aliases = get_all_aliases()
    # Sort by descending length so multi-word phrases match before short codes.
    sorted_aliases = sorted(aliases.keys(), key=len, reverse=True)
    # Escape each alias and join with alternation; use word-boundary anchors.
    pattern = r'\b(' + '|'.join(re.escape(a) for a in sorted_aliases) + r')\b'
    return re.compile(pattern, re.IGNORECASE)


_ALIAS_PATTERN: re.Pattern = _build_alias_pattern()


def detect_country(
    query: str,
    session_country_iso: Optional[str] = None,
    user_preference_iso: Optional[str] = None,
) -> CountryMetadata:
    """
    Determine the relevant country for a given query.

    Parameters
    ----------
    query : str
        The raw user query. Read-only; never mutated.
    session_country_iso : str, optional
        ISO code stored in the user's current session (e.g. "US").
    user_preference_iso : str, optional
        ISO code from the user's profile/preference store.

    Returns
    -------
    CountryMetadata
        Always returns a valid metadata object; never raises.
    """
    try:
        # ── Priority 1: Explicit country mention in query ────────────────
        explicit = _detect_from_query(query)
        if explicit:
            logger.debug("country_detector.explicit_match country=%s", explicit.iso_code)
            return explicit

        # ── Priority 2: Session-level country ───────────────────────────
        if session_country_iso:
            session = get_country_by_iso(session_country_iso)
            if session:
                logger.debug("country_detector.session_match country=%s", session.iso_code)
                return session

        # ── Priority 3: User preference ─────────────────────────────────
        if user_preference_iso:
            preference = get_country_by_iso(user_preference_iso)
            if preference:
                logger.debug("country_detector.preference_match country=%s", preference.iso_code)
                return preference

        # ── Priority 4: Default ─────────────────────────────────────────
        default = get_default_country()
        logger.debug("country_detector.default_fallback country=%s", default.iso_code)
        return default

    except Exception:
        # Fail-safe: always return a valid default, never crash the pipeline.
        logger.exception("country_detector.unexpected_error — returning default")
        return get_default_country()


def _detect_from_query(query: str) -> Optional[CountryMetadata]:
    """
    Scan the query for a known country alias.
    Returns the first (longest) match found, or None.
    """
    aliases = get_all_aliases()
    match = _ALIAS_PATTERN.search(query)
    if not match:
        return None

    matched_alias = match.group(1).lower().strip()
    iso_code = aliases.get(matched_alias)
    if not iso_code:
        return None

    return get_country_by_iso(iso_code)
