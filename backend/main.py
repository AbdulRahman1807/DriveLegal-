from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router as api_router
from backend.api.health import router as health_router
from backend.api.vision_routes import router as vision_router
from backend.api.monitoring_routes import router as monitoring_router
from contextlib import asynccontextmanager
from backend.database import async_session_maker
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.core.security import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-warm BM25
    logger.info("Pre-warming BM25 corpus on startup...")
    async with async_session_maker() as db:
        bm25 = BM25Retriever(db)
        await bm25.initialize()
    yield

app = FastAPI(
    title="DriveLegal AI Core",
    description="HHA-VRAG+ Backend API for Traffic Law Intelligence",
    version="2.0",
    lifespan=lifespan
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Allow Flutter app and Web frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "https://drivelegal.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(vision_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1/monitoring")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
