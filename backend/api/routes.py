from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.retrieval.engine import RetrievalEngine
from backend.chat.engine import ChatEngine
from backend.core.security import verify_api_key, limiter
import uuid
import logging

# ── Global Intelligence Layer + Response Experience Layer hook ────────────────
# Wrapped in a single try/except so any import failure disables the whole
# enhancement stack gracefully — the core pipeline always works unaffected.
try:
    from backend.global_layer import (
        # Global Intelligence Layer
        build_global_context,
        evaluate_and_fallback,
        sanitize_reply,
        build_offline_response,
        # Response Experience Layer (RXL)
        rxl_prepare,
        rxl_finalize,
    )
    _ENHANCEMENT_AVAILABLE = True
except Exception:  # pragma: no cover
    _ENHANCEMENT_AVAILABLE = False
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)
router = APIRouter()

# Safe generic reply — used when fallback mode is needed but Gemini is down.
_SAFE_GENERIC_REPLY = (
    "I wasn't able to find specific information for your query right now. "
    "For accurate and up-to-date traffic law guidance, I recommend checking "
    "with your local transport authority or official government website. "
    "If this is an emergency, please call your local emergency services immediately."
)


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
        # ── STEP 1: Global Intelligence Layer pre-flight ──────────────────────
        # Detects country, checks connectivity, builds hidden metadata context.
        # Fails silently — _gl_context = None means this layer is bypassed.
        _gl_context = None
        if _ENHANCEMENT_AVAILABLE:
            try:
                _gl_context = await build_global_context(query=chat_request.query)
            except Exception as _gl_err:
                logger.warning("global_layer.preflight_failed — bypassing: %s", _gl_err)

        # ── STEP 2: Offline mode early return ─────────────────────────────────
        # If offline AND the query needs live legal data → return safe factual
        # metadata response immediately (no RAG, no LLM call needed).
        # The reply is routed through RXL Phase 2 for consistent formatting.
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
                except Exception as _off_rxl_err:
                    logger.warning("rxl.offline_phase2_failed — using raw reply: %s", _off_rxl_err)
            return ChatResponse(reply=offline_reply, citations=[], fines=[])


        # ── STEP 3: RAG retrieval (existing pipeline — untouched) ────────────
        result = await retrieval_engine.retrieve(
            query=chat_request.query,
            violation_code=chat_request.violation_code,
            jurisdiction_id=chat_request.jurisdiction_id
        )

        # ── STEP 4: Confidence evaluation → Global Fallback Mode ─────────────
        # LOW confidence (score=0.0 or chunks=0) → global_answer_engine takes
        # over and calls Gemini with a jurisdiction-aware prompt.
        # On any failure → falls through to the existing ChatEngine.
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
                    # Run the fallback reply through RXL Phase 2 so it gets
                    # the same formatting/citation treatment as all other replies.
                    if _ENHANCEMENT_AVAILABLE:
                        try:
                            _rxl = rxl_prepare(chat_request.query, raw_reply)
                            _rxl = rxl_finalize(_rxl, raw_reply, [], [])
                            raw_reply = _rxl.reply
                        except Exception:
                            pass  # guardrail below will still run
                    return ChatResponse(reply=raw_reply, citations=[], fines=[])
            except Exception as _fe_err:
                logger.warning(
                    "global_layer.fallback_evaluator_failed — continuing to ChatEngine: %s",
                    _fe_err,
                )
        # ── End Global Fallback Mode ──────────────────────────────────────────

        # ── STEP 5: Build system instructions (jurisdiction context) ──────────
        system_instructions = ""
        if (
            _gl_context is not None
            and not _gl_context.bypass
            and _gl_context.hidden_context_block
        ):
            system_instructions = _gl_context.hidden_context_block

        # ── STEP 6: RXL Phase 1 — inject formatting instructions ─────────────
        # Classifies query intent and prepends invisible formatting instructions
        # to the system_instructions so Gemini produces well-structured output.
        # Fails silently — system_instructions falls back to the unmodified value.
        _rxl_result = None
        if _ENHANCEMENT_AVAILABLE:
            try:
                _rxl_result = rxl_prepare(
                    query=chat_request.query,
                    enriched_query=system_instructions,
                )
                system_instructions = _rxl_result.formatted_query
            except Exception as _rxl_err:
                logger.warning("rxl.prepare_failed — skipping Phase 1: %s", _rxl_err)

        # ── STEP 7: ChatEngine — existing LLM reasoning pipeline ─────────────
        chat_response = await chat_engine.generate_response(
            query=chat_request.query,
            retrieval_result=result,
            session_id=chat_request.session_id,
            system_instructions=system_instructions
        )

        # ── STEP 8: RXL Phase 2 — post-process the reply ─────────────────────
        # Controls citation visibility, strips internal markers, enforces
        # length limits, and ensures the reply is always user-facing.
        if _ENHANCEMENT_AVAILABLE:
            try:
                if _rxl_result is not None:
                    _rxl_result = rxl_finalize(
                        rxl_result=_rxl_result,
                        raw_reply=chat_response.reply,
                        citations=chat_response.citations,
                        fines=chat_response.fines,
                    )
                    chat_response.reply      = _rxl_result.reply
                    chat_response.citations  = _rxl_result.citations
                    chat_response.fines      = _rxl_result.fines
                else:
                    # RXL Phase 1 was skipped; still run the guardrail
                    chat_response.reply = sanitize_reply(chat_response.reply)
            except Exception as _rxl2_err:
                logger.warning("rxl.finalize_failed — skipping Phase 2: %s", _rxl2_err)
                # Fallback: guardrail only
                try:
                    chat_response.reply = sanitize_reply(chat_response.reply)
                except Exception:
                    pass

        return chat_response

    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.error(f"[{error_id}] Unhandled exception: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error. Ref: {error_id}")


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "DriveLegal HHA-VRAG+ Engine"}
