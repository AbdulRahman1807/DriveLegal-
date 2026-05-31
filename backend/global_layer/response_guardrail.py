"""
response_guardrail.py — Global Intelligence Layer
---------------------------------------------------
Guarantees that no internal architecture detail, metadata, prompt content,
or system state is ever exposed to the end user.

Responsibilities:
  - Strip any accidentally leaked internal markers from LLM responses.
  - Ensure responses feel human, natural, and conversational.
  - Provide sanitized offline-mode responses.
  - Provide safe fallback text when something unexpected occurs.

Design constraints:
  - Read + sanitize only. Never generates legal content.
  - Never raises exceptions. All errors produce a safe fallback reply.
  - Every string returned is user-facing and must sound professional.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Patterns that must NEVER appear in a user-facing response.
# These are markers that could leak internal architecture context.
# ---------------------------------------------------------------------------
_INTERNAL_MARKERS = [
    # Global Intelligence Layer & internal architecture
    r"\[GLOBAL INTELLIGENCE LAYER[^\]]*\]",
    r"\[END INTERNAL CONTEXT\]",
    r"Connectivity:\s*(ONLINE|OFFLINE)[^\n]*",
    r"Country:\s*\w+",
    r"Legal System:\s*[^\n]+",
    r"Driving Side:\s*(Left|Right)",
    r"Emergency Number:\s*\d+",
    r"Transport Authority:\s*[^\n]+",
    r"Official Sources:\s*[^\n]+",
    r"Languages:\s*[^\n]+",
    r"ISO Code:\s*\w+",
    r"\[INTERNAL CONTEXT[^\]]*\]",
    r"global_layer",
    r"GlobalContext",
    r"hidden_context_block",
    r"connectivity_checker",
    r"country_detector",
    r"RAG\s+pipeline",
    r"retrieval\s+engine",
    r"vector\s+database",
    r"BM25",
    r"HHA-VRAG",
    r"Gemini API",

    # Legal Artifact & Retrieval Leakage (Second Line of Defense)
    r"based on the provided legal data",
    r"based on the legal context",
    r"according to the motor vehicles act",
    r"as per section \w+",
    r"under section \w+",
    r"the context states",
    r"the document says",
    r"\[.*?motor vehicles act.*?\]",
    r"\[.*?section\s+\w+.*?\]",
]

_COMPILED_MARKERS = [
    re.compile(pattern, re.IGNORECASE | re.MULTILINE)
    for pattern in _INTERNAL_MARKERS
]

# Safe fallback message — used when a reply is empty after sanitization.
_FALLBACK_REPLY = (
    "I'm sorry, I wasn't able to generate a complete response right now. "
    "Please try rephrasing your question, and I'll do my best to help."
)


def sanitize_reply(reply: str) -> str:
    """
    Remove any internal markers from a reply string and return a clean,
    user-safe response.

    Parameters
    ----------
    reply : str
        The raw reply text (may contain internal context leakage).

    Returns
    -------
    str
        Sanitized, user-facing reply. Never empty; uses fallback if needed.
    """
    try:
        if not reply or not reply.strip():
            return _FALLBACK_REPLY

        sanitized = reply
        for pattern in _COMPILED_MARKERS:
            sanitized = pattern.sub("", sanitized)

        # Collapse excessive blank lines that may appear after removal.
        sanitized = re.sub(r'\n{3,}', '\n\n', sanitized).strip()

        if not sanitized:
            logger.warning("response_guardrail.reply_empty_after_sanitize — using fallback")
            return _FALLBACK_REPLY

        return sanitized

    except Exception:
        logger.exception("response_guardrail.sanitize_error — using fallback")
        return _FALLBACK_REPLY


def build_offline_response(
    base_reply: str,
    emergency_number: Optional[str] = None,
    official_source: Optional[str] = None,
) -> str:
    """
    Wrap an offline-mode reply with a natural, human-like disclaimer.

    Parameters
    ----------
    base_reply : str
        The pre-built factual reply from global_context_builder.
    emergency_number : str, optional
        Country emergency number to reinforce in the response.
    official_source : str, optional
        Primary official website for the detected jurisdiction.

    Returns
    -------
    str
        A polished, human-sounding response ready for the user.
    """
    try:
        clean = sanitize_reply(base_reply)
        return clean
    except Exception:
        logger.exception("response_guardrail.offline_response_error — using fallback")
        return _FALLBACK_REPLY


def build_error_response() -> str:
    """
    Return a safe, user-friendly error message when an unexpected
    system failure occurs.

    Returns
    -------
    str
        A human-like apology message with no technical details.
    """
    return (
        "I apologize, but I ran into an unexpected issue while processing "
        "your question. Please try again in a moment — I'm here to help."
    )


def is_reply_safe(reply: str) -> bool:
    """
    Check whether a reply contains any internal markers.
    Useful for testing and CI validation.

    Returns
    -------
    bool
        True if the reply is clean; False if internal markers were detected.
    """
    for pattern in _COMPILED_MARKERS:
        if pattern.search(reply):
            return False
    return True
