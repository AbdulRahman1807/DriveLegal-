from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from backend.schemas.retrieval import Citation, FineResult

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    session_id: Optional[str] = None
    violation_code: Optional[str] = None
    jurisdiction_id: Optional[str] = None

    @field_validator('query')
    def strip_whitespace(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Query cannot be empty or whitespace')
        return v

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatResponse(BaseModel):
    reply: str
    citations: List[Citation]
    fines: List[FineResult]
