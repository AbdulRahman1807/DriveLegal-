"""
Ingestion pipeline — Phase 1.

Sequence:
  1. Load and validate CMVR sections.
  2. Load and validate MVA violations, section stubs, and fine schedules.
  3. Insert records (get_or_create — fully idempotent).
  4. Generate embeddings in one batch for all sections missing them.

Designed to run after the base seed scripts.
Re-running is safe — no duplicates will be created.
"""

import asyncio
import logging
from datetime import date
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.legal_section import LegalSection
from backend.models.violation import Violation
from backend.models.fine_schedule import FineSchedule
from backend.models.jurisdiction import Jurisdiction
from backend.ingest.normaliser_cmvr import load_cmvr_sections
from backend.ingest.normaliser_mva import load_mva_violations, load_mva_sections, load_mva_fines

logger = logging.getLogger(__name__)

_EMBEDDING_BATCH_SIZE = 16   # encode this many texts per SentenceTransformer call


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _get_india_id(session: AsyncSession):
    result = await session.execute(
        select(Jurisdiction).where(Jurisdiction.code == "IN")
    )
    india = result.scalars().first()
    if not india:
        raise RuntimeError("Jurisdiction 'IN' not found. Run seed_jurisdictions first.")
    return india.id


async def _upsert_legal_section(session: AsyncSession, record: dict, india_id) -> LegalSection:
    """
    Insert if page_index not in DB, otherwise return existing row.
    Never overwrites existing data.
    """
    result = await session.execute(
        select(LegalSection).where(LegalSection.page_index == record["page_index"])
    )
    existing = result.scalars().first()
    if existing:
        return existing

    section = LegalSection(
        id=uuid4(),
        act_name=record["act_name"],
        section_number=record["section_number"],
        chapter=record.get("chapter"),
        explanation_text=record.get("explanation_text"),
        full_text=record["full_text"],
        jurisdiction_id=india_id,
        effective_date=record.get("effective_date"),
        gazette_reference=record.get("gazette_reference"),
        source_url=record.get("source_url"),
        page_index=record["page_index"],
    )
    session.add(section)
    await session.flush()   # get id without committing
    return section


async def _upsert_violation(session: AsyncSession, record: dict) -> Violation:
    result = await session.execute(
        select(Violation).where(Violation.violation_code == record["violation_code"])
    )
    existing = result.scalars().first()
    if existing:
        return existing

    v = Violation(
        id=uuid4(),
        violation_code=record["violation_code"],
        name=record["name"],
        description=record["description"],
        category=record["category"],
        keywords=record["keywords"],
        aliases=record["aliases"],
    )
    session.add(v)
    await session.flush()
    return v


async def _upsert_fine_schedule(
    session: AsyncSession,
    record: dict,
    violation: Violation,
    section: LegalSection,
    india_id,
) -> bool:
    """Returns True if a new row was inserted."""
    result = await session.execute(
        select(FineSchedule).where(
            FineSchedule.violation_id == violation.id,
            FineSchedule.jurisdiction_id == india_id,
            FineSchedule.vehicle_category == record["vehicle_category"],
        )
    )
    if result.scalars().first():
        return False

    fs = FineSchedule(
        id=uuid4(),
        violation_id=violation.id,
        jurisdiction_id=india_id,
        legal_section_id=section.id,
        vehicle_category=record["vehicle_category"],
        first_offence_fine=record["first_offence_fine"],
        repeat_offence_fine=record.get("repeat_offence_fine"),
        imprisonment_months=record.get("imprisonment_months") or 0,
        license_suspension_months=0,
        compoundable=record["compoundable"],
        surcharge_percent=0.0,
        effective_date=record.get("effective_date"),
    )
    session.add(fs)
    return True


# ── Embedding generation ──────────────────────────────────────────────────────

def _encode_batch(model, texts: list[str]) -> list[list[float]]:
    vectors = model.encode(texts, batch_size=_EMBEDDING_BATCH_SIZE, show_progress_bar=False)
    return [v.tolist() for v in vectors]


async def generate_embeddings(session: AsyncSession):
    """
    Find all LegalSection rows with NULL embeddings and populate them.
    Loads SentenceTransformer once and encodes in batches.
    """
    result = await session.execute(
        select(LegalSection).where(LegalSection.embedding == None)  # noqa: E711
    )
    sections = result.scalars().all()

    if not sections:
        logger.info("pipeline.embeddings: all sections already have embeddings")
        return

    logger.info("pipeline.embeddings: generating for %d sections", len(sections))

    def _load_and_encode(texts):
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return _encode_batch(model, texts)

    texts = [s.full_text or s.explanation_text or "" for s in sections]
    vectors = await asyncio.to_thread(_load_and_encode, texts)

    for section, vector in zip(sections, vectors):
        section.embedding = vector

    await session.commit()
    logger.info("pipeline.embeddings: committed embeddings for %d sections", len(sections))


# ── Orchestrator ─────────────────────────────────────────────────────────────

async def run_ingest_pipeline(session: AsyncSession):
    """
    Entry point called from run_seeds.py after base seeds complete.
    Fully idempotent — safe to call multiple times.
    """
    india_id = await _get_india_id(session)

    # ── 1. CMVR legal sections ────────────────────────────────────────────────
    cmvr_records = load_cmvr_sections()
    new_cmvr = 0
    for record in cmvr_records:
        result = await session.execute(
            select(LegalSection).where(LegalSection.page_index == record["page_index"])
        )
        if not result.scalars().first():
            await _upsert_legal_section(session, record, india_id)
            new_cmvr += 1

    await session.commit()
    logger.info("pipeline: CMVR sections — %d new / %d total", new_cmvr, len(cmvr_records))

    # ── 2. MVA violations ─────────────────────────────────────────────────────
    mva_violation_records = load_mva_violations()
    violation_objects: dict[str, Violation] = {}  # violation_code → ORM object

    new_violations = 0
    for record in mva_violation_records:
        v = await _upsert_violation(session, record)
        violation_objects[record["violation_code"]] = v
        if v.name == record["name"]:  # newly created (name matches our record)
            new_violations += 1

    await session.commit()
    logger.info("pipeline: MVA violations — %d new / %d attempted", new_violations, len(mva_violation_records))

    # ── 3. MVA section stubs ──────────────────────────────────────────────────
    mva_section_records = load_mva_sections(mva_violation_records)
    section_objects: dict[str, LegalSection] = {}  # section_number → ORM object

    new_sections = 0
    for record in mva_section_records:
        s = await _upsert_legal_section(session, record, india_id)
        section_objects[record["section_number"]] = s
        new_sections += 1

    await session.commit()
    logger.info("pipeline: MVA section stubs — %d new / %d attempted", new_sections, len(mva_section_records))

    # ── 4. MVA fine schedules ─────────────────────────────────────────────────
    mva_fine_records = load_mva_fines(mva_violation_records)
    new_fines = 0
    skipped_fines = 0

    for record in mva_fine_records:
        vc = record["violation_code"]
        sn = record["section_number"]

        violation = violation_objects.get(vc)
        section   = section_objects.get(sn)

        if not violation or not section:
            logger.warning(
                "pipeline: skip fine — missing violation=%s or section=%s", vc, sn
            )
            skipped_fines += 1
            continue

        inserted = await _upsert_fine_schedule(session, record, violation, section, india_id)
        if inserted:
            new_fines += 1

    await session.commit()
    logger.info(
        "pipeline: MVA fines — %d new / %d skipped / %d attempted",
        new_fines, skipped_fines, len(mva_fine_records)
    )

    # ── 5. Embeddings ─────────────────────────────────────────────────────────
    await generate_embeddings(session)

    logger.info(
        "pipeline: complete — cmvr_sections=%d  violations=%d  sections=%d  fines=%d",
        new_cmvr, new_violations, new_sections, new_fines
    )
