from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.models.violation import Violation
from backend.models.fine_schedule import FineSchedule
from backend.schemas.retrieval import FineResult
from backend.jurisdiction.resolver import JurisdictionResolver


class SQLRetriever:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._resolver = JurisdictionResolver(session)

    async def search_fines(self, violation_code: str, jurisdiction_id: str = None) -> list[FineResult]:
        # No violation code → nothing we can look up deterministically.
        if not violation_code:
            return []

        result = await self.session.execute(
            select(Violation).where(Violation.violation_code == violation_code)
        )
        violation = result.scalars().first()
        if not violation:
            return []

        stmt = (
            select(FineSchedule)
            .where(FineSchedule.violation_id == violation.id)
            .options(selectinload(FineSchedule.jurisdiction))
        )

        if jurisdiction_id:
            # Walk the hierarchy (e.g. Tamil Nadu → India) so a state-level query
            # correctly surfaces national-level fine schedules when no state override
            # exists.  Previously this was an exact-match filter that always returned
            # empty when the fine was stored at the parent jurisdiction.
            try:
                from uuid import UUID
                chain = await self._resolver.resolve_by_id(UUID(jurisdiction_id))
                jurisdiction_ids = [node.id for node in chain]
                stmt = stmt.where(FineSchedule.jurisdiction_id.in_(jurisdiction_ids))
            except Exception:
                # Malformed UUID or resolver failure — fall back to exact match so
                # we degrade gracefully rather than blow up the whole request.
                stmt = stmt.where(FineSchedule.jurisdiction_id == jurisdiction_id)

        result2 = await self.session.execute(stmt)
        fines = result2.scalars().all()

        out = []
        for f in fines:
            surcharge_rate = f.surcharge_percent / 100.0 if f.surcharge_percent else 0.0
            base = f.first_offence_fine
            out.append(FineResult(
                violation_id=violation.id,
                violation_code=violation.violation_code,
                violation_name=violation.name,
                vehicle_category=f.vehicle_category,
                base_fine=base,
                surcharges=base * surcharge_rate,
                total_fine=base * (1.0 + surcharge_rate),
                imprisonment_months=f.imprisonment_months or 0,
                license_suspension_months=f.license_suspension_months or 0,
                compoundable=f.compoundable,
                jurisdiction_name=f.jurisdiction.name if f.jurisdiction else "Unknown",
                legal_section_id=f.legal_section_id
            ))
        return out
