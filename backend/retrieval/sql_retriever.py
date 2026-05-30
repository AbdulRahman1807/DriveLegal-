from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.models.violation import Violation
from backend.models.fine_schedule import FineSchedule
from backend.models.legal_section import LegalSection
from backend.schemas.retrieval import FineResult

class SQLRetriever:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def search_fines(self, violation_code: str, jurisdiction_id: str = None) -> list[FineResult]:
        stmt = select(Violation).where(Violation.violation_code == violation_code)
        result = await self.session.execute(stmt)
        violation = result.scalars().first()
        
        if not violation:
            return []
            
        stmt2 = select(FineSchedule).where(FineSchedule.violation_id == violation.id)
        if jurisdiction_id:
            stmt2 = stmt2.where(FineSchedule.jurisdiction_id == jurisdiction_id)
        stmt2 = stmt2.options(selectinload(FineSchedule.jurisdiction))
        result2 = await self.session.execute(stmt2)
        fines = result2.scalars().all()
        
        out = []
        for f in fines:
            out.append(FineResult(
                violation_id=violation.id,
                violation_code=violation.violation_code,
                violation_name=violation.name,
                vehicle_category=f.vehicle_category,
                base_fine=f.first_offence_fine,
                surcharges=f.first_offence_fine * (f.surcharge_percent/100.0) if f.surcharge_percent else 0.0,
                total_fine=f.first_offence_fine * (1.0 + (f.surcharge_percent/100.0 if f.surcharge_percent else 0.0)),
                imprisonment_months=f.imprisonment_months,
                license_suspension_months=f.license_suspension_months,
                compoundable=f.compoundable,
                jurisdiction_name=f.jurisdiction.name if f.jurisdiction else "Unknown",
                legal_section_id=f.legal_section_id
            ))
        return out
