from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.retrieval.engine import RetrievalEngine
from backend.chat.engine import ChatEngine
from backend.core.security import verify_api_key, limiter
from backend.core.telemetry import telemetry
import uuid
import logging
import time

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
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

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "DriveLegal HHA-VRAG+ Engine"}
