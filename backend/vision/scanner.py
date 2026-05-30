import os
import httpx
import uuid
import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

class TicketAnalysisResult(BaseModel):
    extracted_text: str
    inferred_violation: str
    detected_fine: float
    confidence: float
    raw_response: str

class TicketScanner:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")

    async def scan_ticket(self, base64_image: str, mime_type: str = "image/jpeg") -> TicketAnalysisResult:
        if not self.api_key or self.api_key == "dummy_key":
            return TicketAnalysisResult(
                extracted_text="MOCK TICKET TEXT: Driving without helmet. Fine Rs 1000.",
                inferred_violation="NO_HELMET",
                detected_fine=1000.0,
                confidence=0.95,
                raw_response="Simulated response due to missing API key."
            )
            
        prompt = """
        Analyze this traffic e-Challan (ticket).
        Extract the text and identify:
        1. The violation being charged.
        2. The exact fine amount printed on the ticket.
        Respond in strict JSON format:
        {"extracted_text": "...", "inferred_violation": "...", "detected_fine": 1000.0}
        """

        try:
            async with httpx.AsyncClient() as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": base64_image
                                }
                            }
                        ]
                    }],
                    "generationConfig": {"response_mime_type": "application/json"}
                }
                
                response = await client.post(url, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                reply_text = data.get("candidates", [])[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
                import json
                result_json = json.loads(reply_text)
                
                return TicketAnalysisResult(
                    extracted_text=result_json.get("extracted_text", ""),
                    inferred_violation=result_json.get("inferred_violation", "UNKNOWN"),
                    detected_fine=float(result_json.get("detected_fine", 0.0)),
                    confidence=0.90,
                    raw_response=reply_text
                )
        except Exception as e:
            logger.error(f"Vision API error: {e}")
            raise ValueError(f"Failed to analyze ticket image. {e}")
