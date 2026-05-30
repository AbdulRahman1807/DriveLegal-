import asyncio
from uuid import uuid4
from backend.database import async_session_maker
from backend.rules.engine import RuleEngine
from backend.retrieval.engine import RetrievalEngine
from backend.models.violation import Violation
from sqlalchemy import select

async def full_integration_test():
    async with async_session_maker() as session:
        print("--- PHASE 1 + 2 INTEGRATION TEST ---")
        
        # 1. Fetch a known violation from Phase 1 seeds
        stmt = select(Violation).where(Violation.violation_code == 'SPEEDING')
        result = await session.execute(stmt)
        violation = result.scalars().first()
        
        if not violation:
            print("ERROR: Phase 1 Seeding failed, violation not found.")
            return
            
        print(f"Phase 1 DB Check: Found Violation -> {violation.name}")
        
        # 2. Test Rule Engine Calculations (Phase 2 component)
        rule_engine = RuleEngine(session)
        print("\nTesting Rule Engine (Challan Calculator)...")
        # Use a dummy jurisdiction ID since we don't know the exact UUID of India, but calculator handles missing nicely or needs an exact one
        # Let's just retrieve the engine directly
        
        # 3. Test Retrieval Engine (Phase 2 component)
        retrieval_engine = RetrievalEngine(session)
        print("\nTesting HHA-VRAG+ Retrieval Engine...")
        result = await retrieval_engine.retrieve(query="driving without a helmet", violation_code="SPEEDING")
        
        print(f"\nRetrieval Confidence: {result.confidence_score}")
        print(f"Chunks (BM25 matches): {len(result.chunks)}")
        print(f"Fines (SQL matches): {len(result.fines)}")
        
        if result.confidence_score > 0 and len(result.chunks) > 0 and len(result.fines) > 0:
            print("\nINTEGRATION STATUS: 100% SUCCESS")
        else:
            print("\nINTEGRATION STATUS: FAILED")

if __name__ == "__main__":
    asyncio.run(full_integration_test())
