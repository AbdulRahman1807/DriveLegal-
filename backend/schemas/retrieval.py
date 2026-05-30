from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID

class LegalChunk(BaseModel):
    id: UUID
    act_name: str
    section_number: str
    chapter: Optional[str] = None
    clause: Optional[str] = None
    text: str
    jurisdiction_id: Optional[UUID] = None
    source_url: Optional[str] = None

class Citation(BaseModel):
    id: UUID
    act_name: str
    section: str
    clause: Optional[str] = None
    relevance_score: float

class FineResult(BaseModel):
    violation_id: UUID
    violation_code: str
    violation_name: str
    vehicle_category: str
    base_fine: float
    surcharges: float
    total_fine: float
    imprisonment_months: int
    license_suspension_months: int
    compoundable: bool
    jurisdiction_name: str
    legal_section_id: UUID
    note: Optional[str] = None

class RetrievalResult(BaseModel):
    chunks: List[LegalChunk]
    fines: List[FineResult] = Field(default_factory=list)
    citations: List[Citation]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
