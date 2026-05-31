import pytest
from uuid import uuid4
from backend.chat.engine import ChatEngine
from backend.schemas.retrieval import RetrievalResult, LegalChunk, Citation, FineResult

@pytest.mark.asyncio
async def test_chat_engine_isolated():
    engine = ChatEngine()
    engine.api_key = "dummy_key" # Force simulated fallback for deterministic isolated testing
    
    # Create realistic mock data mapping Phase 2 output
    mock_chunk = LegalChunk(
        id=uuid4(),
        act_name="Mock Act",
        section_number="123",
        text="Driving without a helmet is prohibited."
    )
    mock_fine = FineResult(
        violation_id=uuid4(),
        violation_code="NO_HELMET",
        violation_name="Driving without helmet",
        vehicle_category="ALL",
        base_fine=1000.0,
        surcharges=0.0,
        total_fine=1000.0,
        imprisonment_months=0,
        license_suspension_months=0,
        compoundable=True,
        jurisdiction_name="National",
        legal_section_id=uuid4()
    )
    mock_citation = Citation(
        id=mock_chunk.id,
        act_name=mock_chunk.act_name,
        section=mock_chunk.section_number,
        relevance_score=1.0
    )
    
    retrieval_result = RetrievalResult(
        chunks=[mock_chunk],
        fines=[mock_fine],
        citations=[mock_citation],
        confidence_score=1.0
    )
    
    response = await engine.generate_response("What is the fine for no helmet?", retrieval_result)
    
    assert response is not None
    assert response.reply.startswith("[API Key not configured")
    assert len(response.citations) == 1
    assert response.citations[0].act_name == "Mock Act"
    assert response.citations[0].section == "123"
    assert len(response.fines) == 1
    assert response.fines[0].total_fine == 1000.0
    
@pytest.mark.asyncio
async def test_chat_engine_empty_retrieval():
    engine = ChatEngine()
    engine.api_key = "dummy_key"
    
    retrieval_result = RetrievalResult(
        chunks=[],
        fines=[],
        citations=[],
        confidence_score=0.0
    )
    
    response = await engine.generate_response("What is the fine for no helmet?", retrieval_result)
    assert response is not None
    assert len(response.citations) == 0
    assert len(response.fines) == 0
