"""
global_answer_engine.py — Global Intelligence Layer
------------------------------------------------------
Generates helpful, human-like answers when the local RAG pipeline
returns no usable results (confidence_score = 0.0 or chunks = 0).

Handles three query classes:
  1. International (country != IN) — uses jurisdiction metadata + general knowledge
  2. India, no DB match — uses general Indian traffic law knowledge
  3. Metadata/informational — emergency numbers, driving side, authority info

Legal safety guarantees (enforced via prompt):
  - Never fabricates statutes, section numbers, penalties, or court rulings
  - Clearly signals uncertainty when exact rules depend on local jurisdiction
  - Recommends official sources for authoritative detail
  - Never exposes internal architecture, retrieval status, or metadata

Design constraints:
  - Returns None on any failure so the caller falls back gracefully
  - Never raises exceptions
  - All replies pass through response_guardrail.sanitize_reply() before return
"""

import logging
import uuid
from typing import Optional

import httpx

from backend.global_layer.global_data import CountryMetadata
from backend.global_layer.response_guardrail import sanitize_reply
from backend.config import settings

logger = logging.getLogger(__name__)

_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta"
    "/models/gemini-2.5-flash:generateContent"
)
_TIMEOUT = 30.0

# ---------------------------------------------------------------------------
# Prompt builders — one per query class
# ---------------------------------------------------------------------------

def _build_international_prompt(query: str, country: CountryMetadata) -> str:
    """
    For non-India queries where our database has no matching documents.
    Uses country metadata purely as context signals — not as legal evidence.
    """
    return f"""You are DriveLegal, a knowledgeable and professional traffic law \
advisor with expertise in road regulations across multiple countries.

A user is asking about a traffic or road-law matter in {country.country_name}.
Background context (for your awareness only — do not mention these to the user):
- Legal system: {country.legal_system}
- Vehicles drive on the {country.driving_side} side of the road
- National emergency number: {country.emergency_number}
- Primary transport authority: {country.transport_authority}
- Official reference site: {country.official_sources[0]}

Instructions:
1. Answer the user's question using your general knowledge of traffic and road \
law in {country.country_name}.
2. Where rules vary by state, province, or municipality, say so clearly and \
naturally — e.g. "This can vary by state" or "Local regulations differ, so it's \
worth checking with your local authority."
3. If the question is about emergency services, mention {country.emergency_number} \
as the relevant emergency number.
4. If you are uncertain about a specific rule, say so plainly and suggest \
checking {country.official_sources[0]} for authoritative information.
5. NEVER fabricate specific fines, statute numbers, or court rulings.
6. NEVER mention that you have a database, retrieval system, embeddings, or any \
internal tool. Do not say "I don't know based on the provided legal data."
7. Respond as a knowledgeable human advisor would — conversational, warm, clear, \
and professionally worded.

User's question: {query}

Provide a helpful, human-like answer."""


def _build_india_general_prompt(query: str, country: CountryMetadata) -> str:
    """
    For India queries where our database has no matching documents.
    The system has Indian law data but none matched this specific query.
    Could be a very generic question, an edge case, or a novel phrasing.
    """
    return f"""You are DriveLegal, an expert AI assistant specialising in Indian \
traffic law and road regulations.

A user has asked a question about Indian traffic law, but the specific topic \
may relate to general road safety, vehicle documentation, driving etiquette, \
or areas not covered by a specific Motor Vehicles Act section.

Instructions:
1. Answer helpfully using your general knowledge of Indian traffic rules, \
the Motor Vehicles Act (1988, as amended 2019), and common road safety practices.
2. If the topic involves a specific state regulation, note that rules can vary \
by state and recommend checking with the relevant State Transport Authority or \
visiting parivahan.gov.in for authoritative details.
3. For emergencies in India, the national emergency number is 112.
4. NEVER fabricate specific section numbers, fines, or court rulings you are \
not certain about.
5. If you are genuinely uncertain, say so clearly and naturally — e.g. \
"The exact rules around this can vary, and I'd recommend verifying with \
the official Parivahan portal at parivahan.gov.in."
6. NEVER mention databases, retrieval systems, embeddings, or internal tools. \
Do not say "I don't know based on the provided legal data."
7. Be conversational, professional, and helpful — like a knowledgeable friend \
who understands Indian traffic law.

User's question: {query}

Provide a helpful, human-like answer."""


def _build_generic_prompt(query: str, country: CountryMetadata) -> str:
    """
    Generic fallback for any remaining cases — informational, metadata, or
    queries that don't fit either of the above categories cleanly.
    """
    return f"""You are DriveLegal, a helpful and knowledgeable traffic law \
advisor. A user has asked the following question:

"{query}"

The question appears to be related to traffic rules, road safety, vehicle \
regulations, or driving law — potentially in {country.country_name}.

Instructions:
1. Answer as helpfully as possible using your general knowledge.
2. If specific rules depend on location or jurisdiction, note this clearly.
3. For emergencies in {country.country_name}, the emergency number is \
{country.emergency_number}.
4. NEVER fabricate specific statutes, fines, penalties, or legal citations.
5. If you cannot provide a reliable answer, say so honestly and suggest where \
the user can find authoritative information (e.g. {country.official_sources[0]}).
6. Do NOT mention internal systems, databases, or retrieval mechanisms.
7. Keep your response natural, warm, and professional.

Provide a helpful response."""


def _select_prompt(query: str, country: CountryMetadata) -> str:
    """
    Choose the most appropriate prompt template based on detected country.
    """
    if country.iso_code == "IN":
        return _build_india_general_prompt(query, country)
    else:
        return _build_international_prompt(query, country)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def get_global_answer(
    query: str,
    country: CountryMetadata,
) -> Optional[str]:
    """
    Call Gemini with a jurisdiction-aware fallback prompt.

    Returns the sanitized reply string, or None if the call fails
    (so the caller can fall back to a safe generic message).

    Never raises.
    """
    api_key = getattr(settings, "GEMINI_API_KEY", None)

    if not api_key or api_key == "dummy_key":
        logger.warning("global_answer_engine.no_api_key — cannot generate fallback answer")
        return _build_no_api_key_response(country)

    prompt = _select_prompt(query, country)
    ref = str(uuid.uuid4())

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{_GEMINI_URL}?key={api_key}",
                json={"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
                timeout=_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])

            if not candidates:
                logger.warning("global_answer_engine.no_candidates ref=%s", ref)
                return None

            reply_text = (
                candidates[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            if not reply_text or not reply_text.strip():
                logger.warning("global_answer_engine.empty_reply ref=%s", ref)
                return None

            return sanitize_reply(reply_text)

    except httpx.TimeoutException:
        logger.warning("global_answer_engine.timeout ref=%s", ref)
        return None

    except httpx.HTTPStatusError as e:
        logger.error(
            "global_answer_engine.http_error status=%s ref=%s",
            e.response.status_code, ref,
        )
        return None

    except Exception:
        logger.exception("global_answer_engine.unexpected_error ref=%s", ref)
        return None


def _build_no_api_key_response(country: CountryMetadata) -> Optional[str]:
    """
    When the Gemini API key is missing/dummy, return a minimal safe response
    using only the country metadata we have on hand.
    """
    return (
        f"I can share some general information about traffic regulations in "
        f"{country.country_name}. For specific legal questions, I recommend "
        f"consulting {country.official_sources[0]} or contacting the "
        f"{country.transport_authority} directly. "
        f"For emergencies in {country.country_name}, dial {country.emergency_number}."
    )
