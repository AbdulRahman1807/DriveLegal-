import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from backend.models.legal_section import LegalSection
from backend.schemas.retrieval import LegalChunk
import structlog

logger = structlog.get_logger(__name__)

class VectorRetriever:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = None

    async def initialize(self):
        # Load the sentence transformer model in a background thread to prevent blocking
        if not self.model:
            def load_model():
                from sentence_transformers import SentenceTransformer
                return SentenceTransformer('all-MiniLM-L6-v2')
            
            try:
                self.model = await asyncio.to_thread(load_model)
                logger.info("VectorRetriever initialized with all-MiniLM-L6-v2.")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {str(e)}")
                self.model = None

    async def search(self, query: str, top_k: int = 5) -> list[LegalChunk]:
        if not self.model:
            await self.initialize()
            
        if not self.model:
            return []
            
        try:
            # Generate embedding in a background thread
            def encode_query():
                return self.model.encode(query).tolist()
                
            query_vector = await asyncio.to_thread(encode_query)
            
            # Using pgvector <=> operator for cosine distance
            # Postgres cosine distance is 0 for identical vectors, so score is 1 - distance
            stmt = select(LegalSection, LegalSection.embedding.cosine_distance(query_vector).label('distance')) \
                .filter(LegalSection.embedding.is_not(None)) \
                .order_by(text('distance')) \
                .limit(top_k)
                
            result = await self.session.execute(stmt)
            rows = result.all()
            
            chunks = []
            for row in rows:
                doc = row.LegalSection
                distance = row.distance
                score = 1.0 - float(distance) if distance is not None else 0.0
                
                # Thresholding
                if score < 0.3:
                    continue
                    
                chunks.append(LegalChunk(
                    id=doc.id,
                    act_name=doc.act_name,
                    section_number=doc.section_number,
                    chapter=doc.chapter,
                    clause=doc.clause,
                    text=doc.full_text or doc.explanation_text or "",
                    jurisdiction_id=doc.jurisdiction_id,
                    source_url=doc.source_url
                ))
            return chunks
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            # Might fail in SQLite tests since it lacks <=> operator, return empty list gracefully
            return []
