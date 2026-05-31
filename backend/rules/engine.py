from sqlalchemy.ext.asyncio import AsyncSession
from backend.rules.calculator import ChallanCalculator
from uuid import UUID
from backend.schemas.retrieval import FineResult

class RuleEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.calculator = ChallanCalculator(session)
        
    async def process_fines(self, violation_id: UUID, jurisdiction_id: UUID, vehicle_category: str = 'ALL', is_repeat: bool = False) -> list[FineResult]:
        """
        Entry point for the deterministic rule engine.
        Calculates all applicable fines and applies any overriding logic.
        """
        fines = await self.calculator.calculate(violation_id, jurisdiction_id, vehicle_category, is_repeat)
        # We can add more complex rules here if needed, like compounding logic, etc.
        return fines
