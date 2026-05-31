"""
Shared validation for all ingest normalisers.

Rules applied before any DB insert:
  - full_text must be a non-empty string and not the sentinel "DATA_NOT_AVAILABLE"
  - section_number / rule_number must be present
  - page_index must be present
  - duplicate page_index values are rejected (checked in-memory against already-seen set)

These are checks against source data quality, not business logic.
"""

import logging

logger = logging.getLogger(__name__)

_SENTINEL = "DATA_NOT_AVAILABLE"


def _is_sentinel(value) -> bool:
    if not isinstance(value, str):
        return False
    return value.strip().upper() in (_SENTINEL, "DATA NOT AVAILABLE", "N/A", "")


def validate_legal_section(record: dict, seen_page_indexes: set) -> bool:
    """
    Returns True if the record is safe to insert, False otherwise.
    Logs a warning for each rejection with the reason.
    """
    page_index = record.get("page_index", "")
    section    = record.get("section_number", "")
    full_text  = record.get("full_text", "")

    if not page_index or not page_index.strip():
        logger.warning("ingest.skip  missing page_index: %s", record)
        return False

    if page_index in seen_page_indexes:
        logger.debug("ingest.skip  duplicate page_index=%s", page_index)
        return False

    if not section or not section.strip():
        logger.warning("ingest.skip  missing section_number  page_index=%s", page_index)
        return False

    if not full_text or _is_sentinel(full_text):
        logger.warning("ingest.skip  empty/sentinel full_text  page_index=%s", page_index)
        return False

    if len(full_text.strip()) < 20:
        logger.warning("ingest.skip  full_text too short (%d chars)  page_index=%s",
                       len(full_text.strip()), page_index)
        return False

    return True


def parse_fine_amount(raw) -> float | None:
    """
    Convert a fine field to float.  Returns None for sentinel strings — never 0.
    """
    if isinstance(raw, (int, float)) and raw > 0:
        return float(raw)
    if isinstance(raw, str) and not _is_sentinel(raw):
        try:
            v = float(raw.replace(",", "").strip())
            return v if v > 0 else None
        except ValueError:
            pass
    return None


def parse_imprisonment_months(raw) -> int | None:
    """
    Extract an integer month count from strings like:
      "Up to 6 months (first offence), up to 2 years (repeat)"
    Returns only the first number found, interpreted as months.
    Returns None if unparseable.
    """
    if raw is None or _is_sentinel(raw):
        return None
    if isinstance(raw, (int, float)):
        return int(raw)
    if isinstance(raw, str):
        import re
        m = re.search(r'(\d+)\s*month', raw, re.IGNORECASE)
        if m:
            return int(m.group(1))
        m = re.search(r'(\d+)\s*year', raw, re.IGNORECASE)
        if m:
            return int(m.group(1)) * 12
    return None
