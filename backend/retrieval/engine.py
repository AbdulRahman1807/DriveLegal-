from sqlalchemy.ext.asyncio import AsyncSession
from backend.retrieval.sql_retriever import SQLRetriever
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.vector_retriever import VectorRetriever
from backend.retrieval.fusion import FusionEngine
from backend.schemas.retrieval import RetrievalResult, Citation
import logging
import asyncio

logger = logging.getLogger(__name__)

class RetrievalEngine:
    """
    HHA-VRAG+ Orchestrator.
    Coordinates all retrievers and applies fusion logic.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.sql_retriever = SQLRetriever(session)
        self.bm25_retriever = BM25Retriever(session)
        self.vector_retriever = VectorRetriever(session)
        self.fusion = FusionEngine()
        self._is_initialized = False
        
    async def initialize(self):
        if not self._is_initialized:
            logger.info("Initializing BM25 Index...")
            await self.bm25_retriever.initialize()
            self._is_initialized = True
            
    async def retrieve(self, query: str, violation_code: str = None, jurisdiction_id: str = None) -> RetrievalResult:
        await self.initialize()
        
        # We can run SQL and (BM25 + Vector) in parallel
        # Note: bm25 and vector search are CPU bound/async-friendly now.
        sql_task = asyncio.create_task(self.sql_retriever.search_fines(violation_code, jurisdiction_id))
        bm25_task = asyncio.create_task(self.bm25_retriever.search(query, top_k=5))
        vector_task = asyncio.create_task(self.vector_retriever.search(query, top_k=5))
        
        sql_results, bm25_results, vector_results = await asyncio.gather(sql_task, bm25_task, vector_task)

        # Fuse BM25 and Vector chunks together
        fused_chunks = {chunk.id: chunk for chunk in bm25_results + vector_results}.values()
        
        if not sql_results and not fused_chunks:
            # Handle empty corpus or no results at all
            return RetrievalResult(
                chunks=[],
                fines=[],
                citations=[],
                confidence_score=0.0,
                metadata={"source": "HHA-VRAG+", "error": "System not seeded or no results found"}
            )
        
        # Generate citations mapped directly from fused_chunks
        citations = []
        for chunk in fused_chunks:
            citations.append(Citation(
                id=chunk.id,
                act_name=chunk.act_name,
                section=chunk.section_number,
                relevance_score=1.0 # Could be derived from fusion score
            ))
        
        # Fuse results
        result = self.fusion.fuse_results(
            sql_results=sql_results,
            bm25_results=list(fused_chunks)
        )
        
        return result
