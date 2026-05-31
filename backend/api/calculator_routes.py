from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from backend.database import get_db
from backend.core.security import verify_api_key
from backend.schemas.calculator import CalculatorRequest, CalculatorMetadataResponse, ViolationMetadata, JurisdictionMetadata
from backend.schemas.retrieval import FineResult
from backend.rules.engine import RuleEngine
from backend.models.violation import Violation
from backend.models.jurisdiction import Jurisdiction

import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/metadata", response_model=CalculatorMetadataResponse, dependencies=[Depends(verify_api_key)])
async def get_calculator_metadata(db: AsyncSession = Depends(get_db)):
    try:
        violation_stmt = select(Violation).order_by(Violation.name)
        jurisdiction_stmt = select(Jurisdiction).order_by(Jurisdiction.name)
        violation_result = await db.execute(violation_stmt)
        jurisdiction_result = await db.execute(jurisdiction_stmt)
        violations = violation_result.scalars().all()
        jurisdictions = jurisdiction_result.scalars().all()
        return CalculatorMetadataResponse(
            violations=[ViolationMetadata(id=v.id, violation_code=v.violation_code, name=v.name) for v in violations],
            jurisdictions=[JurisdictionMetadata(id=j.id, name=j.name, type=j.type, parent_id=j.parent_id) for j in jurisdictions]
        )
    except Exception as e:
        logger.error(f"Failed to fetch calculator metadata: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while fetching metadata.")

@router.post("/calculate", response_model=List[FineResult], dependencies=[Depends(verify_api_key)])
async def calculate_fine(request: CalculatorRequest, db: AsyncSession = Depends(get_db)):
    try:
        engine = RuleEngine(db)
        results = await engine.process_fines(
            violation_id=request.violation_id,
            jurisdiction_id=request.jurisdiction_id,
            vehicle_category=request.vehicle_category,
            is_repeat=request.is_repeat_offence
        )
        return results
    except Exception as e:
        logger.error(f"Failed to calculate fine: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while calculating fine.")
