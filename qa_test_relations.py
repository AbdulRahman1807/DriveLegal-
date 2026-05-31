import asyncio
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select
from backend.database import async_session_maker
from backend.models.fine_schedule import FineSchedule
from backend.models.violation import Violation
from backend.models.jurisdiction import Jurisdiction

async def main():
    async with async_session_maker() as session:
        # Let's use joinedload to fetch a fine schedule with its violation and jurisdiction
        stmt = select(FineSchedule).options(
            joinedload(FineSchedule.violation),
            joinedload(FineSchedule.jurisdiction)
        ).limit(1)
        
        result = await session.execute(stmt)
        fine = result.scalar_one_or_none()
        
        if fine:
            print("Successfully fetched FineSchedule!")
            print(f"ID: {fine.id}")
            print(f"Vehicle Category: {fine.vehicle_category}")
            print(f"First Offence Fine: {fine.first_offence_fine}")
            print(f"Violation: {fine.violation.name} (Code: {fine.violation.violation_code})")
            print(f"Jurisdiction: {fine.jurisdiction.name} (Type: {fine.jurisdiction.type})")
        else:
            print("No FineSchedule found in the database.")

if __name__ == "__main__":
    asyncio.run(main())
