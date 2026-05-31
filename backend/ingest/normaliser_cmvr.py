"""
Normalises CMVR 1989 dataset → LegalSection records.

Source:  data/legal/drivelegal_cmvr1989_dataset.json
Target:  legal_sections table

Mapping:
  chapters[n].chapter_number  → chapter
  chapters[n].rules[m].rule_number    → section_number
  chapters[n].rules[m].title          → explanation_text
  chapters[n].rules[m].description    → full_text
  chapters[n].rules[m].effective_date → effective_date
  chapters[n].rules[m].gazette_ref    → gazette_reference
  pageindex_chunks[source_url by rule_number] → source_url
  "Central Motor Vehicles Rules, 1989"        → act_name
  f"cmvr:{chapter_lower}:{rule_number}"       → page_index
"""

import json
import logging
import os
from datetime import date

from backend.ingest.validator import validate_legal_section

logger = logging.getLogger(__name__)

_DATA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "legal",
    "drivelegal_cmvr1989_dataset.json"
)
_ACT_NAME = "Central Motor Vehicles Rules, 1989"


def _load_raw() -> dict:
    with open(_DATA_FILE) as f:
        raw = json.load(f)
    return raw if isinstance(raw, dict) else raw[0]


def _build_source_url_index(kb: dict) -> dict[str, str]:
    """Build rule_number → source_url from pageindex_chunks."""
    idx = {}
    for chunk in kb.get("pageindex_chunks", []):
        rule_num = str(chunk.get("rule_number", "")).strip()
        url = chunk.get("source_url", "")
        if rule_num and url:
            idx[rule_num] = url
    return idx


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except (ValueError, TypeError):
        return None


def load_cmvr_sections() -> list[dict]:
    """
    Returns a list of normalised dicts ready for DB insert.
    Validation is applied; invalid records are excluded and logged.
    """
    kb = _load_raw()["drivelegal_knowledge_base"]
    url_idx = _build_source_url_index(kb)
    seen_page_indexes: set[str] = set()

    records = []
    total = 0
    for chapter in kb.get("chapters", []):
        chapter_num = str(chapter.get("chapter_number", "")).strip()

        for rule in chapter.get("rules", []):
            total += 1
            rule_num = str(rule.get("rule_number", "")).strip()
            page_index = f"cmvr:{chapter_num.lower()}:{rule_num}"

            record = {
                "act_name":         _ACT_NAME,
                "section_number":   rule_num,
                "chapter":          chapter_num,
                "explanation_text": rule.get("title", "").strip() or None,
                "full_text":        (rule.get("description") or "").strip(),
                "effective_date":   _parse_date(rule.get("effective_date")),
                "gazette_reference": rule.get("gazette_ref", "").strip() or None,
                "source_url":       url_idx.get(rule_num, "").strip() or None,
                "page_index":       page_index,
            }

            if validate_legal_section(record, seen_page_indexes):
                seen_page_indexes.add(page_index)
                records.append(record)

    logger.info(
        "normaliser_cmvr: %d/%d rules passed validation", len(records), total
    )
    return records
