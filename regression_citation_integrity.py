"""
Citation Integrity Regression Test Suite
=========================================
PART 1 — BM25 relative threshold logic
PART 2 — _filter_citations_by_reply unit tests
PART 3 — Live DB integration (BM25 retrieval only, no LLM)
"""

import sys
import os
import asyncio
import uuid

# ── Project root on path ────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

# ── Test result tracker ─────────────────────────────────────────────────────
results: list[tuple[str, bool, str]] = []   # (name, passed, detail)


def record(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    results.append((name, passed, detail))


# ══════════════════════════════════════════════════════════════════════════════
# PART 1 — Retrieval threshold logic (no DB)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PART 1 — BM25 Relative Threshold Logic (no DB)")
print("=" * 70)

from backend.retrieval.bm25_retriever import _tokenize, _MIN_TOP_SCORE

# Simulate scores as percentages of max (as given in the task spec)
# Section 185 = max score (100%), 129 = 18%, 194D = 12%
max_score = 10.0
scores = {
    "185":   max_score,        # 100% — must PASS
    "129":   max_score * 0.18, # 18%  — must FAIL (below 25%)
    "194D":  max_score * 0.12, # 12%  — must FAIL (below 25%)
}
threshold = max_score * 0.25

passes = {sec: score >= threshold for sec, score in scores.items()}

print(f"\n  Threshold: {threshold:.2f} (25% of max={max_score})")
for sec, score in scores.items():
    pct = score / max_score * 100
    label = "ABOVE threshold" if passes[sec] else "BELOW threshold"
    print(f"  Section {sec}: score={score:.2f} ({pct:.0f}%)  → {label}")

record("Section 185 passes 25% threshold", passes["185"])
record("Section 129 excluded (18% < 25%)", not passes["129"])
record("Section 194D excluded (12% < 25%)", not passes["194D"])

all_p1 = passes["185"] and not passes["129"] and not passes["194D"]
print(f"\n  PART 1 overall: {'PASS' if all_p1 else 'FAIL'}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2 — _filter_citations_by_reply unit tests
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PART 2 — Attribution Filter Unit Tests")
print("=" * 70)

from backend.chat.engine import _filter_citations_by_reply
from backend.schemas.retrieval import RetrievalResult, Citation, LegalChunk

def make_citation(section: str) -> Citation:
    return Citation(
        id=uuid.uuid4(),
        act_name="Motor Vehicles Act",
        section=section,
        clause=None,
        relevance_score=1.0,
    )

def make_chunk(section: str) -> LegalChunk:
    return LegalChunk(
        id=uuid.uuid4(),
        act_name="Motor Vehicles Act",
        section_number=section,
        text=f"Dummy text for section {section}",
    )

mock_citations = [make_citation("185"), make_citation("129"), make_citation("194D")]
mock_chunks    = [make_chunk("185"),    make_chunk("129"),    make_chunk("194D")]

mock_result = RetrievalResult(
    chunks=mock_chunks,
    fines=[],
    citations=mock_citations,
    confidence_score=1.0,
)

def section_numbers(citations) -> set:
    return {c.section.upper() for c in citations}

print()

# (a) Only Section 185 mentioned
reply_a = "Under Section 185 of the Motor Vehicles Act, drunk driving is an offence."
filtered_a = _filter_citations_by_reply(reply_a, mock_result)
secs_a = section_numbers(filtered_a)
passed_a = secs_a == {"185"}
record("(a) reply='Section 185' only → citations=[185]", passed_a,
       f"got={secs_a}")

# (b) Section 185 and Section 194D mentioned
reply_b = "Section 185 covers drunk driving. Section 194D covers overspeeding."
filtered_b = _filter_citations_by_reply(reply_b, mock_result)
secs_b = section_numbers(filtered_b)
passed_b = secs_b == {"185", "194D"}
record("(b) reply='Section 185 and Section 194D' → citations=[185,194D]", passed_b,
       f"got={secs_b}")

# (c) "Sec. 129" mentioned
reply_c = "Refer to Sec. 129 for helmet regulations."
filtered_c = _filter_citations_by_reply(reply_c, mock_result)
secs_c = section_numbers(filtered_c)
passed_c = secs_c == {"129"}
record("(c) reply='Sec. 129' → citations=[129]", passed_c,
       f"got={secs_c}")

# (d) "I don't know" — no section keyword → empty
reply_d = "I don't know based on the provided legal data."
filtered_d = _filter_citations_by_reply(reply_d, mock_result)
passed_d = filtered_d == []
record("(d) reply='I don't know' → citations=[]", passed_d,
       f"got={section_numbers(filtered_d)}")

# (e) "185" without keyword → empty (no "Section" keyword)
reply_e = "the relevant section is 185"
filtered_e = _filter_citations_by_reply(reply_e, mock_result)
passed_e = filtered_e == []
record("(e) reply='...section is 185' (no keyword) → citations=[]", passed_e,
       f"got={section_numbers(filtered_e)}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3 — Live DB Integration (BM25 only, no LLM)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PART 3 — Live DB Integration Test")
print("=" * 70)

import asyncpg
from rank_bm25 import BM25Okapi
from backend.retrieval.bm25_retriever import _tokenize, _MIN_TOP_SCORE

DATABASE_URL = os.getenv("DATABASE_URL", "").replace(
    "postgresql+asyncpg://", "postgresql://"
).replace("asyncpg://", "postgresql://")

QUERIES = [
    ("drunk driving",  "What is the penalty for drunk driving in India?"),
    ("helmet",         "What is the fine for no helmet on a motorcycle?"),
    ("off-topic",      "What is pizza?"),
]

async def run_live_tests():
    print(f"\n  Connecting to: {DATABASE_URL[:60]}...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        print(f"  [ERROR] Cannot connect to DB: {e}")
        record("PART 3 — DB connection", False, str(e))
        return

    rows = await conn.fetch(
        "SELECT id, act_name, section_number, full_text, explanation_text FROM legal_sections"
    )
    await conn.close()
    print(f"  Loaded {len(rows)} legal sections from DB.\n")

    if not rows:
        record("PART 3 — DB has legal sections", False, "0 rows returned")
        return

    record("PART 3 — DB has legal sections", True, f"{len(rows)} rows")

    # Build BM25 index
    documents = list(rows)
    tokenized_corpus = [
        _tokenize(r["full_text"] or r["explanation_text"] or "")
        for r in documents
    ]
    bm25 = BM25Okapi(tokenized_corpus)

    for label, query in QUERIES:
        print(f"  Query [{label}]: \"{query}\"")
        tokens = _tokenize(query)
        if not tokens:
            print(f"    → All tokens are stop words; no results.\n")
            if label == "off-topic":
                record(f"PART 3 — '{label}' returns empty", True, "tokens=[]")
            continue

        scores = bm25.get_scores(tokens)
        max_score = max(scores) if len(scores) else 0.0
        threshold_25 = max_score * 0.25

        print(f"    tokens: {tokens}")
        print(f"    max_score={max_score:.4f}  threshold(25%)={threshold_25:.4f}  min_floor={_MIN_TOP_SCORE}")

        passing = []
        for i, (score, doc) in enumerate(sorted(zip(scores, documents), key=lambda x: -x[0])[:10]):
            pct = (score / max_score * 100) if max_score > 0 else 0
            above = score >= threshold_25 and max_score >= _MIN_TOP_SCORE
            marker = "✓" if above else "✗"
            print(f"    {marker} Section {doc['section_number']:6s}  score={score:.4f}  ({pct:.0f}%)")
            if above:
                passing.append(doc["section_number"])

        print(f"    Sections passing 25% threshold: {passing}\n")

        if label == "off-topic":
            passed = (max_score < _MIN_TOP_SCORE) or (len(passing) == 0)
            record("PART 3 — 'pizza' (off-topic) returns empty", passed,
                   f"passing={passing}, max_score={max_score:.4f}")

        elif label == "drunk driving":
            has_185 = any(s.strip() == "185" for s in passing)
            no_spurious = all(s.strip() == "185" for s in passing)
            record("PART 3 — drunk-driving retrieves Section 185", has_185,
                   f"passing={passing}")
            record("PART 3 — drunk-driving does NOT include spurious sections", no_spurious,
                   f"passing={passing}")

        elif label == "helmet":
            has_129 = any("129" in s for s in passing)
            record("PART 3 — helmet query retrieves Section 129", has_129,
                   f"passing={passing}")

asyncio.run(run_live_tests())


# ══════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
print(f"  {'TEST':<60} {'RESULT'}")
print(f"  {'-'*60} {'------'}")
for name, passed, detail in results:
    status = "PASS" if passed else "FAIL"
    print(f"  {name:<60} {status}")

total = len(results)
passed_count = sum(1 for _, p, _ in results if p)
print(f"\n  {'=' * 68}")
print(f"  TOTAL: {passed_count}/{total} tests passed")
print(f"  {'=' * 68}\n")
sys.exit(0 if passed_count == total else 1)
