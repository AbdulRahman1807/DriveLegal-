"""
Citation Integrity Audit — DriveLegal Backend
==============================================
Diagnoses the pre-LLM citation-assembly bug:
  citations = [chunk for chunk in ALL_retrieved_chunks]
before the LLM is called, so every retrieved section becomes a citation.

Does NOT call Gemini.  Only exercises:
  QueryParser → SQLRetriever → BM25Retriever
"""

import asyncio
import os
import sys

# ── Make backend importable without installing the package ──────────────────
sys.path.insert(0, "/Users/abdul/Desktop/DriveLegal-")

from dotenv import load_dotenv
load_dotenv("/Users/abdul/Desktop/DriveLegal-/.env")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from backend.retrieval.query_parser import QueryParser
from backend.retrieval.sql_retriever import SQLRetriever
from backend.retrieval.bm25_retriever import BM25Retriever, _tokenize, _MIN_TOP_SCORE
from rank_bm25 import BM25Okapi

DATABASE_URL = os.environ["DATABASE_URL"]

# ── Test cases ───────────────────────────────────────────────────────────────
TEST_CASES = [
    {
        "query":    "What is the penalty for drunk driving in India?",
        "expected": ["185"],
        "label":    "drunk_driving",
    },
    {
        "query":    "What is the fine for no helmet on a motorcycle?",
        "expected": ["194D", "129"],
        "label":    "no_helmet",
    },
    {
        "query":    "What is the speeding fine?",
        "expected": ["183"],
        "label":    "speeding",
    },
    {
        "query":    "What happens if I drive without a licence?",
        "expected": [],           # not seeded
        "label":    "no_licence",
    },
    {
        "query":    "What is pizza?",
        "expected": [],           # off-topic
        "label":    "pizza",
    },
]

# Sections clearly unrelated to drunk-driving that should NOT be cited for it
DRUNK_DRIVING_FALSE_POSITIVE_SECTIONS = {"194D", "129", "183", "194", "177"}


# ── Helpers ──────────────────────────────────────────────────────────────────
def banner(text: str):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def section_label(chunk) -> str:
    return f"§{chunk.section_number} ({chunk.act_name})"


# ── Raw BM25 scores — bypass the BM25Retriever.search() threshold so we can
#    show ALL raw scores before filtering.
async def raw_bm25_scores(bm25_retriever: BM25Retriever, query: str):
    """Returns list of (score, document) sorted descending."""
    await bm25_retriever.initialize()
    if not bm25_retriever.bm25:
        return []
    tokenized_query = _tokenize(query)
    if not tokenized_query:
        return []
    doc_scores = bm25_retriever.bm25.get_scores(tokenized_query)
    paired = sorted(
        zip(doc_scores, bm25_retriever.documents),
        key=lambda x: x[0],
        reverse=True,
    )
    return paired


# ── Main audit ───────────────────────────────────────────────────────────────
async def run_audit():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    all_pass = True

    async with async_session() as session:
        # Initialise retrieval components once (BM25 index is expensive)
        bm25_retriever = BM25Retriever(session)
        await bm25_retriever.initialize()

        corpus_size = len(bm25_retriever.documents)
        print(f"\nBM25 corpus size: {corpus_size} documents")
        if corpus_size == 0:
            print("  ⚠  Corpus is EMPTY — seed the database before running this audit.")

        for tc in TEST_CASES:
            query   = tc["query"]
            label   = tc["label"]
            expected = tc["expected"]

            banner(f"TEST: {label}")
            print(f"  Query    : {query!r}")
            print(f"  Expected : {expected or '(empty)'}")

            # ── Step 1: QueryParser ──────────────────────────────────────────
            parser = QueryParser(session)
            inferred_vc  = await parser.infer_violation_code(query)
            inferred_jid = await parser.infer_jurisdiction_id(query)
            print(f"\n  [QueryParser]")
            print(f"    inferred_violation_code  = {inferred_vc!r}")
            print(f"    inferred_jurisdiction_id = {inferred_jid!r}")

            # ── Step 2: SQLRetriever ─────────────────────────────────────────
            sql_ret = SQLRetriever(session)
            sql_results = await sql_ret.search_fines(inferred_vc, inferred_jid)
            print(f"\n  [SQLRetriever]")
            if sql_results:
                for fr in sql_results:
                    print(f"    violation={fr.violation_code} | "
                          f"vehicle={fr.vehicle_category} | "
                          f"base_fine={fr.base_fine} | "
                          f"total={fr.total_fine} | "
                          f"jur={fr.jurisdiction_name}")
            else:
                print("    (no SQL fine results)")

            # ── Step 3: Raw BM25 scores (ALL docs) ──────────────────────────
            all_scored = await raw_bm25_scores(bm25_retriever, query)
            max_score  = all_scored[0][0] if all_scored else 0.0
            threshold  = max_score * 0.1 if max_score >= _MIN_TOP_SCORE else None
            tokenized_q = _tokenize(query)

            print(f"\n  [BM25 — raw scores]")
            print(f"    Tokenized query : {tokenized_q}")
            print(f"    Max score       : {max_score:.4f}")
            print(f"    Min-top guard   : {_MIN_TOP_SCORE}  →  "
                  f"{'PASSES' if max_score >= _MIN_TOP_SCORE else 'FAILS (returns empty)'}")
            if threshold is not None:
                print(f"    Relative threshold (10% of max): {threshold:.4f}")

            print(f"\n    Top-10 documents by BM25 score:")
            print(f"    {'Score':>8}  {'Pass?':>5}  Section")
            print(f"    {'-'*8}  {'-'*5}  {'-'*40}")
            for score, doc in all_scored[:10]:
                if max_score < _MIN_TOP_SCORE:
                    passes = "NO"
                elif threshold is not None and score >= threshold:
                    passes = "YES"
                else:
                    passes = "no"
                print(f"    {score:8.4f}  {passes:>5}  §{doc.section_number} ({doc.act_name})")

            # ── Step 4: Sections BM25Retriever.search() returns ─────────────
            bm25_chunks = await bm25_retriever.search(query, top_k=5)
            print(f"\n  [BM25Retriever.search() — chunks returned (top_k=5)]")
            if bm25_chunks:
                for chunk in bm25_chunks:
                    print(f"    {section_label(chunk)}")
            else:
                print("    (none — filtered out by threshold)")

            # ── Step 5: Citations assembled BEFORE LLM (the bug) ────────────
            # engine.py lines 108-117: citations = [Citation(...) for chunk in fused_chunks]
            # where fused_chunks = bm25_results + vector_results (vector not audited here)
            print(f"\n  [Citations assembled PRE-LLM (engine.py §108-117)]")
            print(f"  ** BUG LOCATION: citations built from ALL retrieved chunks, "
                  f"not from LLM answer **")
            if bm25_chunks:
                for chunk in bm25_chunks:
                    print(f"    → Citation: §{chunk.section_number} | {chunk.act_name} "
                          f"| relevance_score=1.0 (hardcoded)")
            else:
                print("    (no citations — BM25 returned nothing)")

            # ── Step 6: PASS / FAIL ─────────────────────────────────────────
            retrieved_sections = {chunk.section_number for chunk in bm25_chunks}

            if not expected:
                # Expected empty
                passed = len(retrieved_sections) == 0
                verdict = "PASS" if passed else "FAIL"
                print(f"\n  Expected EMPTY citations.")
                if not passed:
                    print(f"  FAIL: got non-empty citations: {retrieved_sections}")
                    all_pass = False
            else:
                # At least one expected section should appear; no blatant FP
                missing = [s for s in expected if s not in retrieved_sections]
                passed = len(missing) == 0
                verdict = "PASS" if passed else "FAIL"
                if missing:
                    print(f"\n  FAIL: expected section(s) missing from citations: {missing}")
                    all_pass = False
                else:
                    print(f"\n  Expected sections {expected} all present in citations.")

            print(f"\n  >>> {verdict} <<<")

            # ── Step 7: Drunk-driving specific false-positive proof ──────────
            if label == "drunk_driving":
                banner("BUG PROOF — drunk-driving query false-positive analysis")
                fp = retrieved_sections & DRUNK_DRIVING_FALSE_POSITIVE_SECTIONS
                print(f"  Query: {query!r}")
                print(f"  Sections in citations: {retrieved_sections}")
                print(f"  Sections NOT related to drunk driving: {DRUNK_DRIVING_FALSE_POSITIVE_SECTIONS}")
                print(f"  False-positive sections found in citations: {fp}")
                print()
                print("  ENGINE.PY BUG TRACE:")
                print("  ─────────────────────────────────────────────────────────────")
                print("  Line 77 : bm25_task = asyncio.create_task(bm25_retriever.search(query, top_k=5))")
                print("  Line 80 : sql_results, bm25_results, vector_results = await asyncio.gather(...)")
                print("  Line 88 : fused_chunks = bm25_results + vector_results  (ALL chunks)")
                print("  Lines 108-117: citations = [Citation(...) for chunk in fused_chunks]")
                print("  ─────────────────────────────────────────────────────────────")
                print("  The LLM has NOT been called yet at this point.")
                print("  citations[] is assembled from the full retrieval pool,")
                print("  NOT from what the LLM answer actually references.")
                if fp:
                    print(f"\n  CONFIRMED: sections {fp} appear as citations for the")
                    print(f"  drunk-driving query but are unrelated to alcohol impairment.")
                    print(f"  These are guaranteed false citations.")
                else:
                    print("\n  No cross-topic false positives detected in BM25 results.")
                    print("  Note: vector_retriever results (not audited here) may add more.")

    banner("AUDIT SUMMARY")
    for tc in TEST_CASES:
        print(f"  {tc['label']:<20} expected={str(tc['expected']):<20}")
    print()
    print(f"  Overall result: {'ALL PASS' if all_pass else 'ONE OR MORE FAILURES'}")
    print()
    print("  KNOWN BUG (engine.py lines 108-117):")
    print("  Citations are assembled from ALL BM25/vector-retrieved chunks")
    print("  BEFORE the LLM is called.  The LLM answer is never consulted")
    print("  to verify which sections it actually used.  Every section the")
    print("  retrieval layer returns becomes a citation, producing false")
    print("  citations whenever top-k > 1 and the query is ambiguous.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_audit())
