import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.violation import Violation

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

async def seed_violations(session: AsyncSession):
    violations_data = [
        {
            "violation_code": "SPEEDING",
            "defaults": {
                "name": "Driving at excessive speed",
                "description": "Driving a motor vehicle at a speed exceeding the maximum speed limit.",
                "category": "SAFETY",
                "keywords": "speeding, overspeeding, fast, over speed",
                "aliases": ["overspeeding", "driving too fast"]
            }
        },
        {
            "violation_code": "DRUNK_DRIVING",
            "defaults": {
                "name": "Driving by a drunken person",
                "description": "Driving under the influence of alcohol or drugs exceeding permissible limits.",
                "category": "SAFETY",
                "keywords": "drunk, alcohol, drinking, intoxicant",
                "aliases": ["dui", "dwi", "drinking and driving"]
            }
        },
        {
            "violation_code": "NO_HELMET",
            "defaults": {
                "name": "Driving without helmet",
                "description": "Driving or riding a two-wheeler without protective headgear.",
                "category": "SAFETY",
                "keywords": "helmet, without helmet, headgear",
                "aliases": ["no helmet", "without helmet"]
            }
        },
        {
            "violation_code": "NO_SEATBELT",
            "defaults": {
                "name": "Driving without seat belt",
                "description": "Driving a motor vehicle without wearing a seat belt.",
                "category": "SAFETY",
                "keywords": "seatbelt, seat belt, belt",
                "aliases": ["no seatbelt", "without seatbelt"]
            }
        },
        {
            "violation_code": "NO_LICENSE",
            "defaults": {
                "name": "Driving without license",
                "description": "Driving a motor vehicle without a valid driving license.",
                "category": "DOCUMENT",
                "keywords": "license, dl, driving license, without license",
                "aliases": ["no dl", "without driving license"]
            }
        },
        {
            "violation_code": "NO_INSURANCE",
            "defaults": {
                "name": "Driving without insurance",
                "description": "Driving a motor vehicle without a valid insurance policy.",
                "category": "DOCUMENT",
                "keywords": "insurance, policy, uninsured",
                "aliases": ["no insurance", "uninsured vehicle"]
            }
        }
    ]
    
    for v_data in violations_data:
        await get_or_create(session, Violation, violation_code=v_data["violation_code"], defaults=v_data["defaults"])
        
    logger.info(f"Successfully seeded {len(violations_data)} violations.")
