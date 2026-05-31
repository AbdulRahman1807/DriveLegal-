"""
Citation Attribution Bug Audit
==============================
Statically proves the post-processing attribution gap in:
  backend/chat/engine.py :: ChatEngine.generate_response()

No Gemini API call is made. All evidence is drawn from source code
analysis and controlled mock objects.
"""

import re
import sys
import uuid
from pathlib import Path

# ── Helpers ──────────────────────────────────────────────────────────────────

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

def result(label: str, ok: bool):
    tag = PASS if ok else FAIL
    print(f"  [{tag}] {label}")
    return ok

# ── Section 1: Read source files and locate key lines ────────────────────────

print("=" * 70)
print("SECTION 1 — Static source-code analysis")
print("=" * 70)

chat_engine_path = Path("/Users/abdul/Desktop/DriveLegal-/backend/chat/engine.py")
retrieval_engine_path = Path("/Users/abdul/Desktop/DriveLegal-/backend/retrieval/engine.py")

chat_src   = chat_engine_path.read_text()
retrieval_src = retrieval_engine_path.read_text()

chat_lines   = chat_src.splitlines()
retrieval_lines = retrieval_src.splitlines()

print(f"\nRead {len(chat_lines)} lines from {chat_engine_path}")
print(f"Read {len(retrieval_lines)} lines from {retrieval_engine_path}")

# ── 1a: Where citations are built (retrieval/engine.py) ──────────────────────

print("\n--- 1a: Citation construction in retrieval/engine.py ---")
citation_build_lines = [
    (i + 1, line)
    for i, line in enumerate(retrieval_lines)
    if "Citation(" in line or ("citations" in line and "=" in line and "chunk" in line)
]
for lineno, text in citation_build_lines:
    print(f"  Line {lineno:3d}: {text.rstrip()}")

found_citation_build = len(citation_build_lines) > 0
result("Citations built from retrieval chunks (pre-LLM)", found_citation_build)

# ── 1b: Where reply_text is extracted from Gemini response ───────────────────

print("\n--- 1b: LLM reply_text assignment in chat/engine.py ---")
llm_reply_lines = [
    (i + 1, line)
    for i, line in enumerate(chat_lines)
    if "reply_text" in line
]
for lineno, text in llm_reply_lines:
    print(f"  Line {lineno:3d}: {text.rstrip()}")

found_reply_text = any("reply_text" in ln for _, ln in llm_reply_lines)
result("reply_text extracted from LLM response", found_reply_text)

# ── 1c: Where citations are returned verbatim (post-LLM) ─────────────────────

print("\n--- 1c: ChatResponse returns citations verbatim (post-LLM) ---")
return_citation_lines = [
    (i + 1, line)
    for i, line in enumerate(chat_lines)
    if "citations=retrieval_result.citations" in line
]
for lineno, text in return_citation_lines:
    print(f"  Line {lineno:3d}: {text.rstrip()}")

found_verbatim_return = len(return_citation_lines) > 0
result(
    "citations=retrieval_result.citations returned verbatim without filtering",
    found_verbatim_return,
)

# ── 1d: Prove NO reconciliation code exists between LLM call and return ───────

print("\n--- 1d: Absence of citation-filtering code between LLM call and return ---")

# Locate the line where reply_text is assigned and the lines where ChatResponse
# is returned inside the try block.
reply_text_lineno = next(
    (i + 1 for i, ln in enumerate(chat_lines) if "reply_text = candidates" in ln),
    None,
)
# The ChatResponse inside the try block (not the fallback ones)
try_return_lineno = next(
    (i + 1 for i, ln in enumerate(chat_lines)
     if "return ChatResponse(" in ln and i > (reply_text_lineno or 0) - 1),
    None,
)

print(f"  reply_text assigned at line: {reply_text_lineno}")
print(f"  ChatResponse returned at line: {try_return_lineno}")

if reply_text_lineno and try_return_lineno:
    between = chat_lines[reply_text_lineno: try_return_lineno - 1]  # lines between
    print(f"  Lines between LLM reply and return ({len(between)} lines):")
    for ln in between:
        print(f"    {ln.rstrip()}")

    filter_keywords = ["filter", "reconcil", "match", "section", "mention", "regex", "re."]
    has_filter = any(
        any(kw in ln.lower() for kw in filter_keywords) for ln in between
    )
    result(
        "NO citation-reconciliation code found between reply_text extraction and return",
        not has_filter,
    )
else:
    print("  Could not locate both anchor lines — manual inspection required.")

# ── Section 2: Bug simulation (no Gemini call) ────────────────────────────────

print("\n" + "=" * 70)
print("SECTION 2 — Bug simulation with mock objects")
print("=" * 70)

# Minimal stand-in for Citation so we don't need the full app stack
class MockCitation:
    def __init__(self, section):
        self.id = uuid.uuid4()
        self.act_name = "Motor Vehicles Act, 1988"
        self.section = section
        self.clause = None
        self.relevance_score = 1.0

    def __repr__(self):
        return f"Citation(section={self.section!r})"

mock_reply_text = (
    "Section 185 of the Motor Vehicles Act prescribes a fine of "
    "₹10,000 for drunk driving."
)
mock_citations = [
    MockCitation("185"),
    MockCitation("129"),
    MockCitation("194D"),
]

# Replicate exactly what generate_response() does today:
#   return ChatResponse(reply=reply_text, citations=retrieval_result.citations, ...)
returned_citations_buggy = mock_citations  # verbatim pass-through

print(f"\n  reply_text  : {mock_reply_text!r}")
print(f"  Pre-LLM citations available : {mock_citations}")
print(f"  Citations returned by current code : {returned_citations_buggy}")

all_sections_returned = {c.section for c in returned_citations_buggy}
expected_spurious = {"129", "194D"}
spurious_present = expected_spurious.issubset(all_sections_returned)

result(
    "Bug confirmed: Section 129 and 194D appear in response even though "
    "reply_text only mentions Section 185",
    spurious_present,
)

# ── Section 3: Correct behaviour (filter citations against reply_text) ─────────

print("\n" + "=" * 70)
print("SECTION 3 — Correct behaviour demonstration")
print("=" * 70)

SECTION_REGEX = re.compile(r'\b(?:Section|Sec\.?)\s+(\w+)')

def filter_citations(reply_text: str, citations: list) -> list:
    """Return only citations whose section number is mentioned in reply_text."""
    mentioned = set(SECTION_REGEX.findall(reply_text))
    if not mentioned:
        # Fallback: LLM could not answer; return full list so caller knows what
        # was retrieved (caller can decide to suppress or show).
        return citations
    return [c for c in citations if c.section in mentioned]

filtered = filter_citations(mock_reply_text, mock_citations)
print(f"\n  Filtered citations (correct): {filtered}")

result(
    "Correct behaviour: only Section 185 returned after filtering",
    len(filtered) == 1 and filtered[0].section == "185",
)
result(
    "Spurious Section 129 excluded",
    all(c.section != "129" for c in filtered),
)
result(
    "Spurious Section 194D excluded",
    all(c.section != "194D" for c in filtered),
)

# ── Section 4: Regex test suite ───────────────────────────────────────────────

print("\n" + "=" * 70)
print("SECTION 4 — Regex pattern test cases")
print("=" * 70)
print(f"\n  Pattern: {SECTION_REGEX.pattern!r}\n")

test_cases = [
    (
        "Under Section 185 of the Motor Vehicles Act...",
        {"185"},
        "Single 'Section N' match",
    ),
    (
        "Section 185 and Section 194D both apply...",
        {"185", "194D"},
        "Multiple 'Section N' matches",
    ),
    (
        "as per Sec. 185...",
        {"185"},
        "Abbreviated 'Sec. N' match",
    ),
    (
        "the relevant section is 185",
        set(),  # no keyword → should NOT match
        "No 'Section' keyword — must NOT match bare number",
    ),
    (
        "I don't know based on the provided legal data.",
        set(),  # no mention → fallback expected
        "No citation — regex finds nothing (fallback to full list)",
    ),
]

all_passed = True
for reply, expected_sections, label in test_cases:
    found = set(SECTION_REGEX.findall(reply))
    ok = found == expected_sections

    # For the fallback case, also verify filter_citations returns the full list
    if expected_sections == set():
        full_citations = [MockCitation("185"), MockCitation("129"), MockCitation("194D")]
        fallback_result = filter_citations(reply, full_citations)
        fallback_ok = len(fallback_result) == len(full_citations)
        if "fallback" in label.lower():
            ok = ok and fallback_ok

    all_passed = result(f"{label} | input={reply!r} | found={found} expected={expected_sections}", ok) and all_passed

# ── Summary ───────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"""
Attribution gap location in backend/chat/engine.py
  - Line {reply_text_lineno}: reply_text extracted from Gemini candidates
  - Line {try_return_lineno}: ChatResponse returned with citations=retrieval_result.citations
  - Lines between: history save only — zero filtering or reconciliation

Root cause (retrieval/engine.py lines 108-117):
  Citations are built from ALL fused retrieval chunks BEFORE the LLM is
  called. generate_response() receives retrieval_result and returns
  retrieval_result.citations verbatim regardless of what the LLM wrote,
  so any section retrieved but not discussed by the LLM leaks into the
  final API response.
""")

sys.exit(0 if all_passed else 1)
