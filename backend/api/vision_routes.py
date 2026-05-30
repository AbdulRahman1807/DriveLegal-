from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from backend.vision.scanner import TicketScanner, TicketAnalysisResult
from backend.core.security import verify_api_key, limiter
from backend.core.telemetry import telemetry
import logging
import base64
import httpx
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()

class TicketUploadRequest(BaseModel):
    image_base64: str
    mime_type: str = "image/jpeg"

@router.post("/analyze_ticket", response_model=TicketAnalysisResult, dependencies=[Depends(verify_api_key)])
@limiter.limit("2/minute")
async def analyze_ticket_endpoint(
    request: Request,
    upload: TicketUploadRequest,
    scanner: TicketScanner = Depends(TicketScanner)
):
    """
    Analyzes an uploaded traffic ticket image (base64) using Gemini Vision,
    extracting text, violation, and fine amounts.
    """
    try:
        # Prevent massive payload abuse
        if len(upload.image_base64) > 5_000_000: # Rough 5MB base64 cap
            raise HTTPException(status_code=413, detail="Image payload too large. Max 5MB.")
            
        # BUG-V1, BUG-V2: Base64 Integrity Check (Async offloaded)
        try:
            await asyncio.to_thread(base64.b64decode, upload.image_base64, validate=True)
        except Exception:
            raise ValueError("Malformed Base64 payload provided.")
            
        if not upload.mime_type.startswith("image/"):
            raise ValueError("Invalid MIME type. Must be an image.")

        result = await scanner.scan_ticket(upload.image_base64, upload.mime_type)
        
        # Async telemetry log (non-blocking)
        await telemetry.log_event("ticket_scanned", {
            "inferred_violation": result.inferred_violation,
            "detected_fine": result.detected_fine,
            "confidence": result.confidence
        })
        
        return result
    except ValueError as e:
        logger.error(f"Vision analysis failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPStatusError as e:
        logger.error(f"Gemini API returned an HTTP error: {e}")
        raise HTTPException(status_code=400, detail="Gemini API rejected the request payload.")
    except Exception as e:
        logger.error(f"Unhandled error in analyze_ticket: {e}")
        raise HTTPException(status_code=500, detail="Internal server error analyzing ticket.")
