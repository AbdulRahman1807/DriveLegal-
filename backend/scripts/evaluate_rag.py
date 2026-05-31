import asyncio
import json
import time
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.database import async_session_maker
from backend.retrieval.engine import RetrievalEngine
from backend.chat.engine import ChatEngine
from backend.schemas.retrieval import RetrievalResult

def compute_recall_at_k(expected: list, retrieved: list, k: int) -> float:
    if not expected:
        return 1.0 if not retrieved else 0.0
    
    retrieved_k = retrieved[:k]
    hits = sum(1 for e in expected if e in retrieved_k)
    return hits / len(expected)

async def evaluate():
    print("Starting RAG Evaluation...")
    data_path = Path(__file__).resolve().parent.parent.parent / "data" / "eval_golden_set.json"
    
    if not data_path.exists():
        print(f"Golden dataset not found at {data_path}")
        return
        
    with open(data_path, "r") as f:
        dataset = json.load(f)
        
    results = []
    
    async with async_session_maker() as db:
        retrieval_engine = RetrievalEngine(db)
        chat_engine = ChatEngine()
        
        for item in dataset:
            query = item["query"]
            print(f"\nEvaluating: '{query}'")
            
            t_start = time.perf_counter()
            retrieval_result = await retrieval_engine.retrieve(query)
            t_retrieval = time.perf_counter() - t_start
            
            t_start = time.perf_counter()
            chat_response = await chat_engine.generate_response(query, retrieval_result)
            t_llm = time.perf_counter() - t_start
            
            # Extract retrieved sections
            retrieved_sections = [chunk.section_number for chunk in retrieval_result.chunks]
            final_citations = [citation.section for citation in chat_response.citations]
            expected_sections = item["expected_sections"]
            
            # Metrics
            recall = compute_recall_at_k(expected_sections, retrieved_sections, k=5)
            
            # Faithfulness: All final citations must be in retrieved chunks
            faithfulness = 1.0
            if final_citations:
                valid_citations = sum(1 for c in final_citations if c in retrieved_sections)
                faithfulness = valid_citations / len(final_citations)
                
            # Precision of expected vs final citations
            citation_precision = 1.0
            if expected_sections and final_citations:
                hits = sum(1 for c in final_citations if c in expected_sections)
                citation_precision = hits / len(final_citations)
            elif expected_sections and not final_citations:
                citation_precision = 0.0
                
            metrics = {
                "query": query,
                "retrieval_latency": t_retrieval,
                "llm_latency": t_llm,
                "recall_at_5": recall,
                "faithfulness": faithfulness,
                "citation_precision": citation_precision,
                "retrieved_chunks": len(retrieval_result.chunks),
                "is_idk": "I don't know based on the provided legal data" in chat_response.reply
            }
            results.append(metrics)
            print(f"  Recall@5: {recall:.2f} | Faithfulness: {faithfulness:.2f} | Precision: {citation_precision:.2f}")

    # Summary
    avg_recall = sum(r["recall_at_5"] for r in results) / len(results)
    avg_faithfulness = sum(r["faithfulness"] for r in results) / len(results)
    avg_precision = sum(r["citation_precision"] for r in results) / len(results)
    
    print("\n" + "="*40)
    print("EVALUATION SUMMARY")
    print("="*40)
    print(f"Total Queries: {len(results)}")
    print(f"Mean Recall@5: {avg_recall:.2f}")
    print(f"Mean Faithfulness: {avg_faithfulness:.2f}")
    print(f"Mean Citation Precision: {avg_precision:.2f}")
    print("="*40)
    
    # Write report
    report_path = Path(__file__).resolve().parent.parent.parent / "data" / "eval_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Detailed report saved to {report_path}")

if __name__ == "__main__":
    asyncio.run(evaluate())
