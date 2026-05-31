"""
global_data.py — Global Intelligence Layer
-------------------------------------------
Stores lightweight, structural metadata for supported jurisdictions.

Design constraints (MUST NOT be violated):
  - No fines, penalties, court rulings, or legal interpretations.
  - No laws, regulations, or amendments.
  - Metadata only — used for context enrichment, never for legal answers.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CountryMetadata:
    """Immutable metadata record for a single jurisdiction."""
    country_name: str
    iso_code: str               # ISO 3166-1 alpha-2
    legal_system: str
    driving_side: str           # "Left" or "Right"
    emergency_number: str
    transport_authority: str
    official_sources: List[str]
    languages: List[str]

    def as_context_block(self) -> str:
        """
        Returns a formatted internal context block.
        This is for LLM prompt injection only — never surfaced to users.
        """
        sources = ", ".join(self.official_sources)
        languages = ", ".join(self.languages)
        return (
            f"Country: {self.country_name}\n"
            f"Legal System: {self.legal_system}\n"
            f"Driving Side: {self.driving_side}\n"
            f"Emergency Number: {self.emergency_number}\n"
            f"Transport Authority: {self.transport_authority}\n"
            f"Official Sources: {sources}\n"
            f"Languages: {languages}"
        )


# ---------------------------------------------------------------------------
# Registry — add new countries here without touching any other module.
# ---------------------------------------------------------------------------

COUNTRY_REGISTRY: Dict[str, CountryMetadata] = {
    "IN": CountryMetadata(
        country_name="India",
        iso_code="IN",
        legal_system="Common Law (Mixed — Federal + State)",
        driving_side="Left",
        emergency_number="112",
        transport_authority="Ministry of Road Transport and Highways (MoRTH)",
        official_sources=["morth.nic.in", "parivahan.gov.in", "nhai.gov.in"],
        languages=["Hindi", "English"],
    ),
    "US": CountryMetadata(
        country_name="United States",
        iso_code="US",
        legal_system="Common Law (Federal + State)",
        driving_side="Right",
        emergency_number="911",
        transport_authority="Department of Transportation (DOT)",
        official_sources=["dot.gov", "nhtsa.gov", "fhwa.dot.gov"],
        languages=["English"],
    ),
    "GB": CountryMetadata(
        country_name="United Kingdom",
        iso_code="GB",
        legal_system="Common Law",
        driving_side="Left",
        emergency_number="999",
        transport_authority="Driver and Vehicle Licensing Agency (DVLA)",
        official_sources=["gov.uk", "dvla.gov.uk", "highways.gov.uk"],
        languages=["English"],
    ),
}

# Convenience aliases for natural-language country name lookup
_NAME_ALIASES: Dict[str, str] = {
    # India
    "india": "IN",
    "bharat": "IN",
    "indian": "IN",
    # United States
    "united states": "US",
    "usa": "US",
    "us": "US",
    "america": "US",
    "american": "US",
    "u.s.": "US",
    "u.s.a.": "US",
    # United Kingdom
    "united kingdom": "GB",
    "uk": "GB",
    "britain": "GB",
    "great britain": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "northern ireland": "GB",
    "british": "GB",
}


def get_country_by_iso(iso_code: str) -> Optional[CountryMetadata]:
    """Return metadata for a given ISO code, or None if unsupported."""
    return COUNTRY_REGISTRY.get(iso_code.upper())


def get_country_by_name(name: str) -> Optional[CountryMetadata]:
    """Return metadata for a natural-language country name/alias, or None."""
    iso = _NAME_ALIASES.get(name.lower().strip())
    if iso:
        return COUNTRY_REGISTRY.get(iso)
    return None


def get_default_country() -> CountryMetadata:
    """System default — India."""
    return COUNTRY_REGISTRY["IN"]


def get_all_aliases() -> Dict[str, str]:
    """Expose alias map for use by country_detector."""
    return dict(_NAME_ALIASES)
