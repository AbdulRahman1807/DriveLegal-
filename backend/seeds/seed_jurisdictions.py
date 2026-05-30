import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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

async def seed_jurisdictions(session: AsyncSession):
    # National
    india = await get_or_create(
        session, Jurisdiction,
        code="IN",
        defaults={
            "name": "India",
            "type": "NATIONAL",
            "coordinates_bounds": {"lat_min": 8.4, "lat_max": 37.6, "lon_min": 68.7, "lon_max": 97.25}
        }
    )

    # States
    karnataka = await get_or_create(
        session, Jurisdiction, code="IN-KA",
        defaults={"name": "Karnataka", "type": "STATE", "parent_id": india.id}
    )
    tamil_nadu = await get_or_create(
        session, Jurisdiction, code="IN-TN",
        defaults={"name": "Tamil Nadu", "type": "STATE", "parent_id": india.id}
    )
    maharashtra = await get_or_create(
        session, Jurisdiction, code="IN-MH",
        defaults={"name": "Maharashtra", "type": "STATE", "parent_id": india.id}
    )

    # Cities
    await get_or_create(
        session, Jurisdiction, code="BLR",
        defaults={"name": "Bangalore", "type": "CITY", "parent_id": karnataka.id}
    )
    await get_or_create(
        session, Jurisdiction, code="MAA",
        defaults={"name": "Chennai", "type": "CITY", "parent_id": tamil_nadu.id}
    )
    
    logger.info("Successfully seeded jurisdictions.")
