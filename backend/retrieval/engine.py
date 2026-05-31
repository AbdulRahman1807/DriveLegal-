import asyncio
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from backend.retrieval.sql_retriever import SQLRetriever
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.vector_retriever import VectorRetriever
from backend.retrieval.fusion import FusionEngine
from backend.retrieval.query_parser import QueryParser
from backend.schemas.retrieval import RetrievalResult, Citation

logger = structlog.get_logger(__name__)


class RetrievalEngine:
    """
    HHA-VRAG+ Orchestrator.

    Query flow:
      1. QueryParser  — infers violation_code + jurisdiction_id from natural language
                        when the caller did not supply them explicitly.
      2. SQL path     — deterministic fine lookup (hierarchy-aware).
      3. BM25 path    — keyword retrieval over legal section corpus.
      4. Vector path  — semantic retrieval via pgvector cosine distance.
      5. FusionEngine — deduplicates and scores combined results.
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
            logger.info("retrieval_engine.init", detail="Building BM25 index")
            await self.bm25_retriever.initialize()
            self._is_initialized = True

    async def retrieve(
        self,
        query: str,
        violation_code: str = None,
        jurisdiction_id: str = None,
    ) -> RetrievalResult:
        await self.initialize()

        # ── Step 1: NLP inference ────────────────────────────────────────────
        # When the caller sends only free text (the common case for chat), infer
        # the structured fields from the query so the SQL path can function.
        # Explicitly-provided values always take precedence.
        if not violation_code or not jurisdiction_id:
            # Run sequentially — AsyncSession does not permit concurrent operations
            # on the same connection; asyncio.gather() here would raise
            # InvalidRequestError("This session is provisioning a new connection").
            parser = QueryParser(self.session)
            parse_vc = await parser.infer_violation_code(query)
            parse_jid = await parser.infer_jurisdiction_id(query)
            effective_violation_code = violation_code or parse_vc
            effective_jurisdiction_id = jurisdiction_id or parse_jid
        else:
            effective_violation_code = violation_code
            effective_jurisdiction_id = jurisdiction_id

        logger.info(
            "retrieval_engine.retrieve",
            violation_code=effective_violation_code,
            jurisdiction_id=effective_jurisdiction_id,
        )

        # ── Step 2: Parallel retrieval ───────────────────────────────────────
        sql_task = asyncio.create_task(
            self.sql_retriever.search_fines(effective_violation_code, effective_jurisdiction_id)
        )
        bm25_task = asyncio.create_task(self.bm25_retriever.search(query, top_k=5))
        vector_task = asyncio.create_task(self.vector_retriever.search(query, top_k=5))

        sql_results, bm25_results, vector_results = await asyncio.gather(
            sql_task, bm25_task, vector_task
        )

        # ── Step 3: Fuse semantic results ────────────────────────────────────
        # Deduplicate BM25 + vector chunks by ID, preserving first occurrence.
        seen_ids: set = set()
        fused_chunks = []
        for chunk in bm25_results + vector_results:
            if chunk.id not in seen_ids:
                seen_ids.add(chunk.id)
                fused_chunks.append(chunk)

        if not sql_results and not fused_chunks:
            return RetrievalResult(
                chunks=[],
                fines=[],
                citations=[],
                confidence_score=0.0,
                metadata={
                    "source": "HHA-VRAG+",
                    "error": "No results found. Corpus may not be seeded or query has no match.",
                    "inferred_violation_code": effective_violation_code,
                    "inferred_jurisdiction_id": effective_jurisdiction_id,
                },
            )

        # ── Step 4: Build citations from chunks ──────────────────────────────
        citations = [
            Citation(
                id=chunk.id,
                act_name=chunk.act_name,
                section=chunk.section_number,
                clause=chunk.clause,
                relevance_score=1.0,
            )
            for chunk in fused_chunks
        ]

        # ── Step 5: Fusion scoring ───────────────────────────────────────────
        result = self.fusion.fuse_results(
            sql_results=sql_results,
            bm25_results=fused_chunks,
        )

        return result
