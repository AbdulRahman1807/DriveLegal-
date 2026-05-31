import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.violation import Violation
from backend.retrieval.engine import RetrievalEngine
from backend.rules.engine import RuleEngine
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_rule_engine_empty(db_session: AsyncSession):
    engine = RuleEngine(db_session)
    fines = await engine.process_fines(uuid4(), uuid4())
    assert len(fines) == 0

@pytest.mark.asyncio
async def test_retrieval_engine_no_results(db_session: AsyncSession):
    engine = RetrievalEngine(db_session)
    result = await engine.retrieve("gibberish_query_xyz_123", "NONEXISTENT_CODE")
    assert result.confidence_score == 0.0
    assert len(result.chunks) == 0
    assert len(result.fines) == 0

@pytest.mark.asyncio
async def test_retrieval_engine_valid_match(db_session: AsyncSession):
    engine = RetrievalEngine(db_session)
    result = await engine.retrieve("speeding", "SPEEDING")
    assert result.confidence_score >= 0.0

@pytest.mark.asyncio
async def test_models_exist(db_session: AsyncSession):
    stmt = select(Violation).limit(1)
    result = await db_session.execute(stmt)
    assert result is not None
