from rank_bm25 import BM25Okapi
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.legal_section import LegalSection
from backend.schemas.retrieval import LegalChunk
import asyncio

def build_bm25_index(documents):
    tokenized_corpus = []
    for doc in documents:
        text = doc.full_text or doc.explanation_text or ""
        tokens = text.lower().split()
        tokenized_corpus.append(tokens)
    if tokenized_corpus:
        return BM25Okapi(tokenized_corpus)
    return None

import time

class BM25Retriever:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.bm25 = None
        self.corpus = []
        self.documents = []
        self.last_indexed = 0

    async def initialize(self):
        # Implement a naive TTL cache invalidation (e.g., 30 mins)
        if self.bm25 and time.time() - self.last_indexed < 1800:
            return
            
        stmt = select(LegalSection).execution_options(yield_per=1000)
        result = await self.session.stream_scalars(stmt)
        
        self.documents = []
        async for doc in result:
            self.documents.append(doc)
            
        if self.documents:
            self.bm25 = await asyncio.to_thread(build_bm25_index, self.documents)
            self.last_indexed = time.time()
            
    async def search(self, query: str, top_k: int = 5) -> list[LegalChunk]:
        await self.initialize()
        if not self.bm25:
            return []
                
        tokenized_query = query.strip().lower().split()
        if not tokenized_query:
            return []
            
        doc_scores = self.bm25.get_scores(tokenized_query)
        
        if not len(doc_scores):
            return []
            
        max_score = max(doc_scores) if max(doc_scores) > 0 else 1.0
        threshold = max_score * 0.1
        
        scored_docs = list(zip(doc_scores, self.documents))
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        top_docs = scored_docs[:top_k]
        
        results = []
        for score, doc in top_docs:
            if score < threshold: continue
            results.append(LegalChunk(
                id=doc.id,
                act_name=doc.act_name,
                section_number=doc.section_number,
                chapter=doc.chapter,
                clause=doc.clause,
                text=doc.full_text or doc.explanation_text or "",
                jurisdiction_id=doc.jurisdiction_id,
                source_url=doc.source_url
            ))
            
        return results
