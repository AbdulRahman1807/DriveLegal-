from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional

class CalculatorRequest(BaseModel):
    violation_id: UUID
    jurisdiction_id: UUID
    vehicle_category: str = Field(default="ALL", description="Vehicle category e.g. LMV, HMV, 2W, ALL")
    is_repeat_offence: bool = Field(default=False)

class ViolationMetadata(BaseModel):
    id: UUID
    violation_code: str
    name: str

class JurisdictionMetadata(BaseModel):
    id: UUID
    name: str
    type: str
    parent_id: Optional[UUID] = None

class CalculatorMetadataResponse(BaseModel):
    violations: List[ViolationMetadata]
    jurisdictions: List[JurisdictionMetadata]
