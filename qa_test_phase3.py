import asyncio
from backend.database import async_session_maker
from backend.chat.engine import ChatEngine
from backend.retrieval.engine import RetrievalEngine

async def test_phase_3():
    print("--- PHASE 3: API & CHAT ENGINE TEST ---")
    
    async with async_session_maker() as session:
        # Mock retrieval engine step
        retrieval_engine = RetrievalEngine(session)
        print("1. Running Retrieval (Simulated Phase 2 input)...")
        result = await retrieval_engine.retrieve(query="driving without a helmet", violation_code="SPEEDING")
        
        # Test Chat Engine
        chat_engine = ChatEngine()
        print("2. Generating Chat Response via Context Injection...")
        response = await chat_engine.generate_response(query="What is the fine for driving without a helmet and speeding?", retrieval_result=result)
        
        print("\n--- LLM RESPONSE ---")
        print(response.reply)
        print("\n--- CITATIONS ---")
        for c in response.citations:
            print(f"- {c.act_name}, Section {c.section}")
            
        print("\n--- FINES ---")
        for f in response.fines:
            print(f"- {f.violation_name}: {f.total_fine}")
            
        if response.reply:
            print("\nPHASE 3 STATUS: SUCCESS")
        else:
            print("\nPHASE 3 STATUS: FAILED")

if __name__ == "__main__":
    asyncio.run(test_phase_3())
