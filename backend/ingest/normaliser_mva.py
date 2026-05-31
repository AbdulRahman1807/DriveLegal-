"""
Normalises MVA dataset → Violation, LegalSection, and FineSchedule records.

Source:  data/legal/drivelegal_india_mva_dataset.json
Targets: violations, legal_sections, fine_schedules tables

The MVA JSON does not contain verbatim statutory text, so legal_sections
for these entries are constructed from available violation metadata
(violation_name, enforcement_procedure, evidence_required).  They are
clearly marked as summary entries in explanation_text.

These sections exist to satisfy the NOT NULL FK on fine_schedules and to
make the violations BM25-searchable.  They do NOT replace the hand-seeded
verbatim sections (129, 183, 185, 194D).

Dedup keys:
  violations:    violation_code  (unique constraint on DB)
  legal_sections: page_index     (format: mva_json:{section})
  fine_schedules: (violation_id, jurisdiction_id, vehicle_category) — checked in pipeline
"""

import json
import logging
import os
import re
from datetime import date

from backend.ingest.validator import validate_legal_section, parse_fine_amount, parse_imprisonment_months

logger = logging.getLogger(__name__)

_DATA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "legal",
    "drivelegal_india_mva_dataset.json"
)
_ACT_NAME = "Motor Vehicles Act, 1988 (Amended 2019)"

# Existing violation_codes — must never be overwritten
_EXISTING_CODES = frozenset({
    "SPEEDING", "DRUNK_DRIVING", "NO_HELMET",
    "NO_SEATBELT", "NO_LICENSE", "NO_INSURANCE",
})


def _load_raw() -> dict:
    with open(_DATA_FILE) as f:
        raw = json.load(f)
    return raw if isinstance(raw, dict) else raw[0]


def _to_violation_code(violation_name: str) -> str:
    """Convert a human-readable name to an UPPER_SNAKE_CASE violation code."""
    code = re.sub(r'[^A-Z0-9]+', '_', violation_name.upper().strip()).strip('_')
    # Truncate to 100 chars (DB column limit)
    return code[:100]


def _build_full_text(v: dict) -> str:
    """
    Build a BM25-searchable full_text from violation metadata.
    Not verbatim statutory text — used only for new MVA violations
    that lack full section text in the dataset.
    """
    parts = [
        f"{v['violation_name']} — {v['legal_citation']}.",
        f"Enforcement: {v.get('enforcement_procedure', '')}.",
    ]
    evidence = v.get("evidence_required", [])
    if evidence:
        parts.append(f"Evidence required: {'; '.join(evidence)}.")
    authority = v.get("officer_authority", "")
    if authority:
        parts.append(f"Enforcing authority: {authority}.")
    return " ".join(p for p in parts if p.strip() and p != ".").strip()


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except (ValueError, TypeError):
        return None


def load_mva_violations() -> list[dict]:
    """
    Returns normalised violation dicts.
    Skips any violation_code that already exists (existing seeds take precedence).
    """
    kb = _load_raw()["drivelegal_knowledge_base"]
    records = []

    for v in kb.get("traffic_violations", []):
        code = _to_violation_code(v["violation_name"])

        if code in _EXISTING_CODES:
            logger.debug("normaliser_mva: skip existing violation_code=%s", code)
            continue

        # Map MVA category strings to the existing category convention
        cat_map = {
            "GENERAL": "GENERAL", "ROAD_RULES": "SAFETY", "PUBLIC_TRANSPORT": "PUBLIC_TRANSPORT",
            "AUTHORITY_DISOBEDIENCE": "GENERAL", "LICENSING": "DOCUMENT", "SPEED": "SAFETY",
            "DANGEROUS_DRIVING": "SAFETY", "DUI_DWI": "SAFETY", "RACING": "SAFETY",
            "PERMIT": "DOCUMENT", "AGGREGATOR": "DOCUMENT", "OVERLOADING": "SAFETY",
            "VEHICLE_STANDARDS": "SAFETY", "SAFETY": "SAFETY", "EMERGENCY_VEHICLE": "SAFETY",
            "INSURANCE": "DOCUMENT", "JUVENILE": "SAFETY",
        }
        category = cat_map.get(v.get("category", ""), "GENERAL")

        records.append({
            "violation_code": code,
            "name":           v["violation_name"],
            "description":    v.get("enforcement_procedure", v["violation_name"]),
            "category":       category,
            "keywords":       v["violation_name"].lower(),
            "aliases":        [],
            # Keep violation_id for cross-referencing during fine schedule load
            "_source_violation_id": v["violation_id"],
            "_section": v["section"],
        })

    logger.info("normaliser_mva: %d new violations prepared", len(records))
    return records


def load_mva_sections(violations: list[dict]) -> list[dict]:
    """
    Creates one LegalSection per new violation to satisfy the NOT NULL FK
    on fine_schedules.  Text is derived from violation metadata.

    Returns normalised section dicts.  Validation applied.
    """
    seen: set[str] = set()
    records = []

    for v in violations:
        section_num = v["_section"]
        page_index  = f"mva_json:{section_num}"

        record = {
            "act_name":         _ACT_NAME,
            "section_number":   section_num,
            "chapter":          "13",    # all penalty sections are in Chapter XIII
            "explanation_text": f"[Summary] {v['name']} — Section {section_num} MV Act 1988",
            "full_text":        _build_full_text({
                "violation_name":       v["name"],
                "legal_citation":       f"Section {section_num}, {_ACT_NAME}",
                "enforcement_procedure":v["description"],
                "evidence_required":    [],
                "officer_authority":    "",
            }),
            "page_index": page_index,
            "source_url": "https://indiacode.nic.in/handle/123456789/2249",
        }

        if validate_legal_section(record, seen):
            seen.add(page_index)
            records.append(record)

    logger.info("normaliser_mva: %d section stubs prepared", len(records))
    return records


def load_mva_fines(violations: list[dict]) -> list[dict]:
    """
    Returns normalised fine schedule dicts.
    Cross-references violation_codes via _source_violation_id.
    DATA_NOT_AVAILABLE → None (never 0).
    """
    kb = _load_raw()["drivelegal_knowledge_base"]

    # Build lookup: source violation_id → violation_code + section
    vid_to_code: dict[str, str] = {
        v["_source_violation_id"]: v["violation_code"]
        for v in violations
    }
    vid_to_section: dict[str, str] = {
        v["_source_violation_id"]: v["_section"]
        for v in violations
    }

    records = []
    for f in kb.get("national_fine_schedule", []):
        vid = f["violation_id"]
        # Some fine entries use compound IDs like "VIO009_LMV" / "VIO009_MPV".
        # Strip the vehicle-type suffix to resolve back to the base violation ID.
        base_vid = vid.split("_")[0] if vid not in vid_to_code else vid
        if base_vid in vid_to_code:
            vid = base_vid
        if vid not in vid_to_code:
            logger.debug("normaliser_mva: skip fine for unknown vid=%s", vid)
            continue

        first_fine = parse_fine_amount(f.get("fine_first_offence_inr"))
        if first_fine is None:
            logger.warning("normaliser_mva: skip fine — no valid first_offence amount  vid=%s", vid)
            continue

        records.append({
            "violation_code":       vid_to_code[vid],
            "section_number":       vid_to_section[vid],
            "vehicle_category":     f.get("vehicle_type", "ALL"),
            "first_offence_fine":   first_fine,
            "repeat_offence_fine":  parse_fine_amount(f.get("fine_repeat_offence_inr")),
            "imprisonment_months":  parse_imprisonment_months(f.get("imprisonment")),
            "compoundable":         bool(f.get("compoundable", True)),
            "effective_date":       _parse_date(f.get("effective_date")),
        })

    logger.info("normaliser_mva: %d fine schedules prepared", len(records))
    return records
