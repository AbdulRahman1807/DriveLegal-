import asyncio
from backend.database import async_session_maker
from backend.retrieval.engine import RetrievalEngine

async def test_phase_2():
    async with async_session_maker() as session:
        engine = RetrievalEngine(session)
        print("Testing Retrieval Engine with BM25...")
        
        # Test a semantic query about alcohol
        result = await engine.retrieve(query="drunk driving alcohol limit", violation_code="DRUNKEN_DRIVING")
        
        print(f"Confidence Score: {result.confidence_score}")
        print(f"Chunks Found: {len(result.chunks)}")
        for chunk in result.chunks:
            print(f" - {chunk.act_name}, Section {chunk.section_number}: {chunk.text[:50]}...")
            
        print(f"Fines Found: {len(result.fines)}")
        for fine in result.fines:
            print(f" - Fine: {fine.total_fine} for {fine.violation_name}")
            
if __name__ == "__main__":
    asyncio.run(test_phase_2())
