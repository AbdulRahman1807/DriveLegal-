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
        updated = False
        if defaults:
            for k, v in defaults.items():
                if getattr(instance, k) != v:
                    setattr(instance, k, v)
                    updated = True
        if updated:
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
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
        defaults={
            "name": "Karnataka",
            "type": "STATE",
            "parent_id": india.id,
            "coordinates_bounds": {"lat_min": 11.5, "lat_max": 18.5, "lon_min": 74.0, "lon_max": 78.5}
        }
    )
    tamil_nadu = await get_or_create(
        session, Jurisdiction, code="IN-TN",
        defaults={
            "name": "Tamil Nadu",
            "type": "STATE",
            "parent_id": india.id,
            "coordinates_bounds": {"lat_min": 8.0, "lat_max": 13.5, "lon_min": 76.0, "lon_max": 80.5}
        }
    )
    maharashtra = await get_or_create(
        session, Jurisdiction, code="IN-MH",
        defaults={
            "name": "Maharashtra",
            "type": "STATE",
            "parent_id": india.id,
            "coordinates_bounds": {"lat_min": 15.6, "lat_max": 22.0, "lon_min": 72.6, "lon_max": 80.9}
        }
    )
    gujarat = await get_or_create(
        session, Jurisdiction, code="IN-GJ",
        defaults={
            "name": "Gujarat",
            "type": "STATE",
            "parent_id": india.id,
            "coordinates_bounds": {"lat_min": 20.1, "lat_max": 24.7, "lon_min": 68.1, "lon_max": 74.4}
        }
    )
    telangana = await get_or_create(
        session, Jurisdiction, code="IN-TG",
        defaults={
            "name": "Telangana",
            "type": "STATE",
            "parent_id": india.id,
            "coordinates_bounds": {"lat_min": 15.8, "lat_max": 19.9, "lon_min": 77.2, "lon_max": 81.8}
        }
    )
    kerala = await get_or_create(
        session, Jurisdiction, code="IN-KL",
        defaults={
            "name": "Kerala",
            "type": "STATE",
            "parent_id": india.id,
            "coordinates_bounds": {"lat_min": 8.1, "lat_max": 12.8, "lon_min": 74.8, "lon_max": 77.5}
        }
    )
    mp = await get_or_create(
        session, Jurisdiction, code="IN-MP",
        defaults={
            "name": "Madhya Pradesh",
            "type": "STATE",
            "parent_id": india.id,
            "coordinates_bounds": {"lat_min": 21.1, "lat_max": 26.9, "lon_min": 74.0, "lon_max": 82.8}
        }
    )
    uttarakhand = await get_or_create(
        session, Jurisdiction, code="IN-UK",
        defaults={
            "name": "Uttarakhand",
            "type": "STATE",
            "parent_id": india.id,
            "coordinates_bounds": {"lat_min": 28.7, "lat_max": 31.5, "lon_min": 77.5, "lon_max": 81.0}
        }
    )
    rajasthan = await get_or_create(
        session, Jurisdiction, code="IN-RJ",
        defaults={
            "name": "Rajasthan",
            "type": "STATE",
            "parent_id": india.id,
            "coordinates_bounds": {"lat_min": 23.3, "lat_max": 30.2, "lon_min": 69.5, "lon_max": 78.3}
        }
    )
    sikkim = await get_or_create(
        session, Jurisdiction, code="IN-SK",
        defaults={
            "name": "Sikkim",
            "type": "STATE",
            "parent_id": india.id,
            "coordinates_bounds": {"lat_min": 27.0, "lat_max": 28.2, "lon_min": 88.0, "lon_max": 89.0}
        }
    )


    # Cities
    await get_or_create(
        session, Jurisdiction, code="BLR",
        defaults={
            "name": "Bangalore",
            "type": "CITY",
            "parent_id": karnataka.id,
            "coordinates_bounds": {"lat_min": 12.8, "lat_max": 13.1, "lon_min": 77.4, "lon_max": 77.7}
        }
    )
    await get_or_create(
        session, Jurisdiction, code="MAA",
        defaults={
            "name": "Chennai",
            "type": "CITY",
            "parent_id": tamil_nadu.id,
            "coordinates_bounds": {"lat_min": 12.9, "lat_max": 13.2, "lon_min": 80.1, "lon_max": 80.3}
        }
    )
    
    logger.info("Successfully seeded jurisdictions.")
