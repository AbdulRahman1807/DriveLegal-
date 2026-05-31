from fastapi import APIRouter, Depends
from backend.core.security import verify_api_key
from backend.core.telemetry import telemetry

router = APIRouter()

@router.get("/metrics", dependencies=[Depends(verify_api_key)])
async def get_metrics():
    """
    Returns aggregated telemetry statistics for the RAG pipeline.
    Protected by MASTER_API_KEY.
    """
    return telemetry.get_aggregated_stats()
