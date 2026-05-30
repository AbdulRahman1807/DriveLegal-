from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.retrieval.engine import RetrievalEngine
from backend.chat.engine import ChatEngine
from backend.core.security import verify_api_key, limiter
import uuid
import logging

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
    
    try:
        # Phase 2: Retrieve context and fines
        result = await retrieval_engine.retrieve(
            query=chat_request.query, 
            violation_code=chat_request.violation_code,
            jurisdiction_id=chat_request.jurisdiction_id
        )
        
        # Phase 3: Inject context into LLM
        chat_response = await chat_engine.generate_response(
            query=chat_request.query, 
            retrieval_result=result,
            session_id=chat_request.session_id
        )
        
        return chat_response
    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.error(f"[{error_id}] Unhandled exception: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error. Ref: {error_id}")

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "DriveLegal HHA-VRAG+ Engine"}
