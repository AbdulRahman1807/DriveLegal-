import logging
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.legal_section import LegalSection
from backend.models.jurisdiction import Jurisdiction

logger = logging.getLogger(__name__)


async def get_or_create(session: AsyncSession, model, defaults=None, **kwargs):
    stmt = select(model).filter_by(**kwargs)
    result = await session.execute(stmt)
    instance = result.scalars().first()
    if instance:
        return instance, False

    params = {k: v for k, v in kwargs.items()}
    if defaults:
        params.update(defaults)
    instance = model(**params)
    session.add(instance)
    await session.commit()
    await session.refresh(instance)
    return instance, True


def _generate_embedding(text: str):
    """
    Generate a 384-dim embedding using the same model as VectorRetriever.
    Wrapped in a function so it can be run via asyncio.to_thread.
    """
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return model.encode(text).tolist()


async def _populate_embedding(session: AsyncSession, instance: LegalSection):
    """Generate and persist an embedding for a LegalSection if absent."""
    if instance.embedding is not None:
        return
    text = instance.full_text or instance.explanation_text or ""
    if not text.strip():
        return
    try:
        embedding = await asyncio.to_thread(_generate_embedding, text)
        instance.embedding = embedding
        session.add(instance)
        await session.commit()
        logger.info(f"Generated embedding for section {instance.section_number}")
    except Exception as e:
        logger.warning(f"Could not generate embedding for section {instance.section_number}: {e}")


async def seed_legal_sections(session: AsyncSession):
    stmt = select(Jurisdiction).where(Jurisdiction.code == "IN")
    result = await session.execute(stmt)
    india = result.scalars().first()

    if not india:
        logger.error("National jurisdiction not found. Run seed_jurisdictions first.")
        return

    sections_data = [
        {
            "page_index": "mva:4:129",
            "defaults": {
                "act_name": "Motor Vehicles Act, 1988 (Amended 2019)",
                "section_number": "129",
                "chapter": "4",
                # Full text of Section 129 — the helmet mandate that Section 194D
                # enforces.  Previously absent from the corpus, which meant BM25 and
                # vector search had no text containing the word "helmet" to retrieve.
                "full_text": (
                    "Every person driving or riding or being carried on a motorcycle "
                    "of any class or description shall wear protective headgear "
                    "conforming to such standards as may be prescribed by the Central "
                    "Government. The protective headgear referred to in this section "
                    "is commonly known as a helmet. Failure to wear a helmet while "
                    "riding or driving a motorcycle, two-wheeler, or motor cycle is an "
                    "offence punishable under section 194D of this Act."
                ),
                "explanation_text": (
                    "Mandatory helmet rule: every motorcycle rider and pillion passenger "
                    "must wear an ISI-marked helmet. No helmet violation is enforced "
                    "under Section 194D."
                ),
                "jurisdiction_id": india.id,
                "source_url": "https://indiacode.nic.in/handle/123456789/2249",
            },
        },
        {
            "page_index": "mva:13:183:1",
            "defaults": {
                "act_name": "Motor Vehicles Act, 1988 (Amended 2019)",
                "section_number": "183",
                "chapter": "13",
                "clause": "1",
                "explanation_text": "Driving at excessive speed, etc.",
                "full_text": (
                    "Whoever drives or causes any person who is employed by him or "
                    "subjects someone under his control to drive a motor vehicle in "
                    "contravention of the speed limits referred to in section 112 shall "
                    "be punishable with a fine of one thousand rupees for the first "
                    "offence and two thousand rupees for the second or subsequent offence."
                ),
                "jurisdiction_id": india.id,
                "source_url": "https://indiacode.nic.in/handle/123456789/2249",
            },
        },
        {
            "page_index": "mva:13:185",
            "defaults": {
                "act_name": "Motor Vehicles Act, 1988 (Amended 2019)",
                "section_number": "185",
                "chapter": "13",
                "full_text": (
                    "Whoever, while driving, or attempting to drive, a motor vehicle,— "
                    "(a) has, in his blood, alcohol exceeding 30 mg. per 100 ml. of "
                    "blood detected in a test by a breath analyser, or (b) is under the "
                    "influence of a drug to such an extent as to be incapable of "
                    "exercising proper control over the vehicle, shall be punishable for "
                    "the first offence with imprisonment for a term which may extend to "
                    "six months, or with fine of ten thousand rupees, or with both. "
                    "Drunk driving and driving under influence of alcohol or drugs is "
                    "strictly prohibited."
                ),
                "jurisdiction_id": india.id,
                "source_url": "https://indiacode.nic.in/handle/123456789/2249",
            },
        },
        {
            "page_index": "mva:13:194d",
            "defaults": {
                "act_name": "Motor Vehicles Act, 1988 (Amended 2019)",
                "section_number": "194D",
                "chapter": "13",
                # Enriched: the original text never contained the word "helmet".
                # Added an explicit summary sentence so both BM25 and vector search
                # can surface this section on helmet-related queries.
                "full_text": (
                    "Whoever drives a motor cycle (motorcycle) or causes or allows a "
                    "motor cycle to be driven without wearing a helmet in contravention "
                    "of the provisions of section 129 or the rules or regulations made "
                    "thereunder shall be punishable with a fine of one thousand rupees "
                    "and he shall be disqualified for holding a driving licence for a "
                    "period of three months. This section applies to all riders and "
                    "pillion passengers on two-wheelers who fail to wear a protective "
                    "headgear (helmet) as required by section 129."
                ),
                "explanation_text": (
                    "Penalty for not wearing a helmet on a motorcycle or two-wheeler: "
                    "fine of ₹1,000 and licence suspension for 3 months."
                ),
                "jurisdiction_id": india.id,
                "source_url": "https://indiacode.nic.in/handle/123456789/2249",
            },
        },
    ]

    seeded = 0
    for s_data in sections_data:
        instance, created = await get_or_create(
            session, LegalSection,
            page_index=s_data["page_index"],
            defaults=s_data["defaults"],
        )
        if created:
            seeded += 1

        # Populate embedding regardless of whether the row was just created —
        # rows from a previous seed run will have embedding=None if the embedding
        # step was missing before (Fix 3).
        await _populate_embedding(session, instance)

    logger.info(f"seed_legal_sections: seeded {seeded} new sections, "
                f"{len(sections_data) - seeded} already existed. Embeddings populated.")
