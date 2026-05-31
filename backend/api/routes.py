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

# ── Global Intelligence Layer + RXL hook ─────────────────────────────────────
try:
    from backend.global_layer import (
        build_global_context,
        evaluate_and_fallback,
        sanitize_reply,
        build_offline_response,
        rxl_prepare,
        rxl_finalize,
    )
    _ENHANCEMENT_AVAILABLE = True
except Exception:
    _ENHANCEMENT_AVAILABLE = False
# ─────────────────────────────────────────────────────────────────────────────

_SAFE_GENERIC_REPLY = (
    "I wasn't able to find specific information for your query right now. "
    "For accurate and up-to-date traffic law guidance, please check with your "
    "local transport authority or official government website."
)

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
        # ── Global Intelligence Layer pre-flight ──────────────────────────────
        _gl_context = None
        if _ENHANCEMENT_AVAILABLE:
            try:
                _gl_context = await build_global_context(query=chat_request.query)
            except Exception as _gl_err:
                logger.warning("global_layer.preflight_failed — bypassing: %s", _gl_err)

        # ── Offline mode early return ─────────────────────────────────────────
        if (
            _gl_context is not None
            and not _gl_context.bypass
            and _gl_context.connectivity.is_offline
            and _gl_context.offline_safe_reply
        ):
            offline_reply = build_offline_response(_gl_context.offline_safe_reply)
            if _ENHANCEMENT_AVAILABLE:
                try:
                    _rxl_off = rxl_prepare(chat_request.query, offline_reply)
                    _rxl_off = rxl_finalize(_rxl_off, offline_reply, [], [])
                    offline_reply = _rxl_off.reply
                except Exception:
                    pass
            return ChatResponse(reply=offline_reply, citations=[], fines=[])

        # ── RAG retrieval ─────────────────────────────────────────────────────
        t_retrieval_start = time.perf_counter()
        result = await retrieval_engine.retrieve(
            query=chat_request.query,
            violation_code=chat_request.violation_code,
            jurisdiction_id=chat_request.jurisdiction_id
        )
        metrics["retrieval_latency"] = time.perf_counter() - t_retrieval_start
        metrics["retrieved_chunks_count"] = len(result.chunks)
        metrics["retrieved_citations_count"] = len(result.citations)

        # ── Confidence evaluation → Global Fallback Mode ──────────────────────
        if _ENHANCEMENT_AVAILABLE and _gl_context is not None and not _gl_context.bypass:
            try:
                decision = await evaluate_and_fallback(
                    query=chat_request.query,
                    confidence_score=result.confidence_score,
                    chunk_count=len(result.chunks),
                    country=_gl_context.country,
                )
                if decision.needs_fallback:
                    raw_reply = decision.fallback_reply or _SAFE_GENERIC_REPLY
                    try:
                        _rxl = rxl_prepare(chat_request.query, raw_reply)
                        _rxl = rxl_finalize(_rxl, raw_reply, [], [])
                        raw_reply = _rxl.reply
                    except Exception:
                        pass
                    return ChatResponse(reply=raw_reply, citations=[], fines=[])
            except Exception as _fe_err:
                logger.warning("global_layer.fallback_evaluator_failed — continuing: %s", _fe_err)

        # ── System instructions (jurisdiction context + RXL Phase 1) ──────────
        system_instructions = ""
        if _gl_context is not None and not _gl_context.bypass and _gl_context.hidden_context_block:
            system_instructions = _gl_context.hidden_context_block

        _rxl_result = None
        if _ENHANCEMENT_AVAILABLE:
            try:
                _rxl_result = rxl_prepare(chat_request.query, system_instructions)
                system_instructions = _rxl_result.formatted_query
            except Exception as _rxl_err:
                logger.warning("rxl.prepare_failed — skipping Phase 1: %s", _rxl_err)

        # ── LLM ───────────────────────────────────────────────────────────────
        t_llm_start = time.perf_counter()
        chat_response = await chat_engine.generate_response(
            query=chat_request.query,
            retrieval_result=result,
            session_id=chat_request.session_id,
            system_instructions=system_instructions,
        )
        metrics["llm_latency"] = time.perf_counter() - t_llm_start
        metrics["final_citations_count"] = len(chat_response.citations)

        # ── RXL Phase 2 — post-process reply ──────────────────────────────────
        if _ENHANCEMENT_AVAILABLE:
            try:
                if _rxl_result is not None:
                    _rxl_result = rxl_finalize(
                        rxl_result=_rxl_result,
                        raw_reply=chat_response.reply,
                        citations=chat_response.citations,
                        fines=chat_response.fines,
                    )
                    chat_response.reply     = _rxl_result.reply
                    chat_response.citations = _rxl_result.citations
                    chat_response.fines     = _rxl_result.fines
                else:
                    chat_response.reply = sanitize_reply(chat_response.reply)
            except Exception as _rxl2_err:
                logger.warning("rxl.finalize_failed — skipping Phase 2: %s", _rxl2_err)
                try:
                    chat_response.reply = sanitize_reply(chat_response.reply)
                except Exception:
                    pass

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
