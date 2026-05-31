from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.retrieval.engine import RetrievalEngine
from backend.chat.engine import ChatEngine
from backend.core.security import get_current_user, limiter
from backend.core.telemetry import telemetry
from pydantic import BaseModel
from typing import Optional
import uuid
import logging
import time

logger = logging.getLogger(__name__)
router = APIRouter()

class LegalSectionDetail(BaseModel):
    id: uuid.UUID
    act_name: str
    section_number: str
    chapter: Optional[str] = None
    clause: Optional[str] = None
    explanation_text: Optional[str] = None
    full_text: str
    source_url: Optional[str] = None

@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(get_current_user)])
@limiter.limit("5/minute")
async def chat_endpoint(
    request: Request,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    chat_engine: ChatEngine = Depends(ChatEngine)
):
    retrieval_engine = RetrievalEngine(db)
    
    t_start = time.perf_counter()
    metrics = {"failed": False}
    
    try:
        # Phase 2: Retrieve context and fines
        t_retrieval_start = time.perf_counter()
        result = await retrieval_engine.retrieve(
            query=chat_request.query, 
            violation_code=chat_request.violation_code,
            jurisdiction_id=chat_request.jurisdiction_id
        )
        t_retrieval_end = time.perf_counter()
        metrics["retrieval_latency"] = t_retrieval_end - t_retrieval_start
        metrics["retrieved_chunks_count"] = len(result.chunks)
        metrics["retrieved_citations_count"] = len(result.citations)
        
        # Phase 3: Inject context into LLM
        t_llm_start = time.perf_counter()
        chat_response = await chat_engine.generate_response(
            query=chat_request.query, 
            retrieval_result=result,
            session_id=chat_request.session_id
        )
        t_llm_end = time.perf_counter()
        metrics["llm_latency"] = t_llm_end - t_llm_start
        metrics["final_citations_count"] = len(chat_response.citations)
        
        # IDK detection
        metrics["is_idk"] = "I don't know based on the provided legal data" in chat_response.reply
        
        metrics["total_latency"] = time.perf_counter() - t_start
        await telemetry.log_event("rag_trace", metrics)
        
        return chat_response
    except Exception as e:
        metrics["failed"] = True
        metrics["total_latency"] = time.perf_counter() - t_start
        await telemetry.log_event("rag_trace", metrics)
        
        error_id = str(uuid.uuid4())
        logger.error(f"[{error_id}] Unhandled exception: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error. Ref: {error_id}")

def _section_to_detail(section) -> LegalSectionDetail:
    return LegalSectionDetail(
        id=section.id,
        act_name=section.act_name,
        section_number=section.section_number,
        chapter=section.chapter,
        clause=section.clause,
        explanation_text=section.explanation_text,
        full_text=section.full_text,
        source_url=section.source_url,
    )


@router.get("/legal_sections/lookup", response_model=LegalSectionDetail, dependencies=[Depends(get_current_user)])
async def lookup_legal_section(
    act_name: str,
    section: str,
    db: AsyncSession = Depends(get_db),
):
    from backend.models.legal_section import LegalSection

    section = section.strip()
    act_name = act_name.strip()
    if not section or not act_name:
        raise HTTPException(status_code=400, detail="act_name and section are required")

    stmt = (
        select(LegalSection)
        .where(LegalSection.section_number == section)
        .limit(20)
    )
    result = await db.execute(stmt)
    candidates = result.scalars().all()
    if not candidates:
        raise HTTPException(status_code=404, detail="Legal section not found")

    act_lower = act_name.lower()
    matched = next(
        (s for s in candidates if s.act_name.lower() in act_lower or act_lower in s.act_name.lower()),
        candidates[0],
    )
    return _section_to_detail(matched)


@router.get("/legal_sections/{section_id}", response_model=LegalSectionDetail, dependencies=[Depends(get_current_user)])
async def get_legal_section(
    section_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    from backend.models.legal_section import LegalSection
    stmt = select(LegalSection).where(LegalSection.id == section_id)
    result = await db.execute(stmt)
    section = result.scalars().first()
    if not section:
        raise HTTPException(status_code=404, detail="Legal section not found")
    return _section_to_detail(section)

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "DriveLegal HHA-VRAG+ Engine"}
