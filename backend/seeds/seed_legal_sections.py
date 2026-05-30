import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.models.legal_section import LegalSection
from backend.models.jurisdiction import Jurisdiction

logger = logging.getLogger(__name__)

async def get_or_create(session: AsyncSession, model, defaults=None, **kwargs):
    stmt = select(model).filter_by(**kwargs)
    result = await session.execute(stmt)
    instance = result.scalars().first()
    if instance:
        return instance
    
    params = dict((k, v) for k, v in kwargs.items())
    if defaults:
        params.update(defaults)
    instance = model(**params)
    session.add(instance)
    await session.commit()
    await session.refresh(instance)
    return instance

async def seed_legal_sections(session: AsyncSession):
    # Get India jurisdiction
    stmt = select(Jurisdiction).where(Jurisdiction.code == "IN")
    result = await session.execute(stmt)
    india = result.scalars().first()
    
    if not india:
        logger.error("National jurisdiction not found. Run seed_jurisdictions first.")
        return

    sections_data = [
        {
            "page_index": "mva:13:183:1",
            "defaults": {
                "act_name": "Motor Vehicles Act, 1988 (Amended 2019)",
                "section_number": "183",
                "chapter": "13",
                "clause": "1",
                "explanation_text": "Driving at excessive speed, etc.",
                "full_text": "Whoever drives or causes any person who is employed by him or subjects someone under his control to drive a motor vehicle in contravention of the speed limits referred to in section 112 shall be punishable with a fine.",
                "jurisdiction_id": india.id,
            }
        },
        {
            "page_index": "mva:13:185",
            "defaults": {
                "act_name": "Motor Vehicles Act, 1988 (Amended 2019)",
                "section_number": "185",
                "chapter": "13",
                "full_text": "Whoever, while driving, or attempting to drive, a motor vehicle,— (a) has, in his blood, alcohol exceeding 30 mg. per 100 ml. of blood detected in a test by a breath analyser, or (b) is under this influence of a drug to such an extent as to be incapable of exercising proper control over the vehicle, shall be punishable for the first offence with imprisonment for a term which may extend to six months, or with fine of ten thousand rupees, or with both.",
                "jurisdiction_id": india.id,
            }
        },
        {
            "page_index": "mva:13:194d",
            "defaults": {
                "act_name": "Motor Vehicles Act, 1988 (Amended 2019)",
                "section_number": "194D",
                "chapter": "13",
                "full_text": "Whoever drives a motor cycle or causes or allows a motor cycle to be driven in contravention of the provisions of section 129 or the rules or regulations made thereunder shall be punishable with a fine of one thousand rupees and he shall be disqualified for holding licence for a period of three months.",
                "jurisdiction_id": india.id,
            }
        },
    ]
    
    for s_data in sections_data:
        instance = await get_or_create(session, LegalSection, page_index=s_data["page_index"], defaults=s_data["defaults"])
        
        # Manually populate TSVECTOR using func if it's not set
        if not instance.keywords:
            instance.keywords = func.to_tsvector('english', instance.full_text)
            session.add(instance)
            await session.commit()
            
    logger.info(f"Successfully seeded {len(sections_data)} legal sections.")
