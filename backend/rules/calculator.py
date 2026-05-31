from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from backend.models.fine_schedule import FineSchedule
from backend.models.violation import Violation
from backend.models.jurisdiction import Jurisdiction
from backend.schemas.retrieval import FineResult
from backend.jurisdiction.resolver import JurisdictionResolver
from sqlalchemy.orm import joinedload

class ChallanCalculator:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.resolver = JurisdictionResolver(session)
        
    async def calculate(self, violation_id: UUID, jurisdiction_id: UUID, vehicle_category: str = 'ALL', is_repeat_offence: bool = False) -> list[FineResult]:
        """
        Calculates the fine based on deterministic rule logic.
        Resolves the jurisdiction chain to find the most specific rule.
        """
        chain = await self.resolver.resolve_by_id(jurisdiction_id)
        jurisdiction_ids = [node.id for node in chain]
        
        # Query fine schedules for the violation in any of the jurisdictions in the chain
        stmt = (
            select(FineSchedule)
            .options(joinedload(FineSchedule.violation), joinedload(FineSchedule.jurisdiction))
            .where(
                FineSchedule.violation_id == violation_id,
                FineSchedule.jurisdiction_id.in_(jurisdiction_ids)
            )
        )
        
        result = await self.session.execute(stmt)
        schedules = result.scalars().all()
        
        # Filter for applicable vehicle categories
        applicable_schedules = []
        for s in schedules:
            if s.vehicle_category == 'ALL' or s.vehicle_category == vehicle_category:
                applicable_schedules.append(s)
                
        # Sort by jurisdiction specificity (most specific first, meaning lower index in chain)
        applicable_schedules.sort(key=lambda s: jurisdiction_ids.index(s.jurisdiction_id))
        
        results = []
        for s in applicable_schedules:
            base = s.repeat_offence_fine if is_repeat_offence and s.repeat_offence_fine else s.first_offence_fine
            surcharges = base * (s.surcharge_percent / 100.0) if s.surcharge_percent else 0.0
            
            results.append(FineResult(
                violation_id=s.violation_id,
                violation_code=s.violation.violation_code,
                violation_name=s.violation.name,
                vehicle_category=s.vehicle_category,
                base_fine=base,
                surcharges=surcharges,
                total_fine=base + surcharges,
                imprisonment_months=s.imprisonment_months,
                license_suspension_months=s.license_suspension_months,
                compoundable=s.compoundable,
                jurisdiction_name=s.jurisdiction.name,
                legal_section_id=s.legal_section_id
            ))
            
        return results
