from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.database import get_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health", summary="Perform a Health Check", response_description="Return HTTP Status Code 200 (OK)")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Check if the API and database are up and running.
    """
    health_status = {"status": "ok", "database": "unknown"}
    
    try:
        # Simple query to check db connection
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            health_status["database"] = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status["database"] = "disconnected"
        health_status["status"] = "degraded"
        
    return health_status
