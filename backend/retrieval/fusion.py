from typing import List, Dict, Any
from backend.schemas.retrieval import RetrievalResult, LegalChunk, FineResult, Citation

class FusionEngine:
    def fuse_results(self, sql_results: List[FineResult], bm25_results: List[LegalChunk]) -> RetrievalResult:
        """
        Normalizes and deduplicates results into a single RetrievalResult object.
        """
        # Deduplicate chunks
        unique_chunks = {}
        for chunk in bm25_results:
            key = f"{chunk.act_name}_{chunk.section_number}"
            if key not in unique_chunks:
                unique_chunks[key] = chunk
                
        # In a real fusion engine, confidence score would be calculated based on BM25 scores + exact matches
        has_fines = bool(sql_results)
        has_chunks = bool(bm25_results)
        if has_fines and has_chunks:
            confidence = 1.0
        elif has_fines:
            confidence = 0.7
        elif has_chunks:
            confidence = 0.5
        else:
            confidence = 0.0
        
        citations = []
        for chunk in unique_chunks.values():
            citations.append(Citation(
                id=chunk.id,
                act_name=chunk.act_name,
                section=chunk.section_number,
                clause=chunk.clause,
                relevance_score=confidence
            ))
            
        return RetrievalResult(
            chunks=list(unique_chunks.values()),
            fines=sql_results,
            citations=citations,
            confidence_score=confidence,
            metadata={"source": "HHA-VRAG+"}
        )
