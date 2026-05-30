import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.fine_schedule import FineSchedule
from backend.models.jurisdiction import Jurisdiction
from backend.models.violation import Violation
from backend.models.legal_section import LegalSection

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

async def seed_fines(session: AsyncSession):
    # Fetch lookups
    stmt = select(Jurisdiction).where(Jurisdiction.code == "IN")
    india = (await session.execute(stmt)).scalars().first()
    
    stmt = select(Violation)
    violations = {v.violation_code: v for v in (await session.execute(stmt)).scalars().all()}
    
    stmt = select(LegalSection)
    sections = {s.section_number: s for s in (await session.execute(stmt)).scalars().all()}
    
    if not india or not violations or not sections:
        logger.error("Missing required data for fine schedules. Run other seeds first.")
        return
        
    fines_data = [
        {
            "keys": {
                "violation_id": violations["SPEEDING"].id,
                "jurisdiction_id": india.id,
                "legal_section_id": sections["183"].id,
                "vehicle_category": "LMV"
            },
            "defaults": {
                "first_offence_fine": 1000.0,
                "repeat_offence_fine": 2000.0,
                "compoundable": True
            }
        },
        {
            "keys": {
                "violation_id": violations["SPEEDING"].id,
                "jurisdiction_id": india.id,
                "legal_section_id": sections["183"].id,
                "vehicle_category": "HMV"
            },
            "defaults": {
                "first_offence_fine": 2000.0,
                "repeat_offence_fine": 4000.0,
                "compoundable": True
            }
        },
        {
            "keys": {
                "violation_id": violations["DRUNK_DRIVING"].id,
                "jurisdiction_id": india.id,
                "legal_section_id": sections["185"].id,
                "vehicle_category": "ALL"
            },
            "defaults": {
                "first_offence_fine": 10000.0,
                "repeat_offence_fine": 15000.0,
                "imprisonment_months": 6,
                "compoundable": False
            }
        },
        {
            "keys": {
                "violation_id": violations["NO_HELMET"].id,
                "jurisdiction_id": india.id,
                "legal_section_id": sections["194D"].id,
                "vehicle_category": "2W"
            },
            "defaults": {
                "first_offence_fine": 1000.0,
                "license_suspension_months": 3,
                "compoundable": True
            }
        }
    ]
    
    for f_data in fines_data:
        await get_or_create(session, FineSchedule, defaults=f_data["defaults"], **f_data["keys"])
        
    logger.info(f"Successfully seeded {len(fines_data)} fine schedules.")
