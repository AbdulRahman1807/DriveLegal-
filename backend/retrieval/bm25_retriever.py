import re
import time
import asyncio
from rank_bm25 import BM25Okapi
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.legal_section import LegalSection
from backend.schemas.retrieval import LegalChunk

# Pairs of (regex, canonical form).  Applied symmetrically: corpus text and
# query text both go through the same normalization so surface-form differences
# ("motorcycle" vs "motor cycle") don't block matching.
_NORMALIZATIONS: list[tuple[re.Pattern, str]] = [
    (re.compile(r'\bmotorcycle\b', re.I), 'motor cycle'),
    (re.compile(r'\btwo[\s-]?wheeler\b', re.I), 'two wheeler'),
    (re.compile(r'\bseatbelt\b', re.I), 'seat belt'),
    (re.compile(r'\bheadgear\b', re.I), 'helmet headgear'),  # expand synonym
    (re.compile(r'\bdrunk[\s-]?driving\b', re.I), 'drunk driving'),
    (re.compile(r'\bhit[\s-]?and[\s-]?run\b', re.I), 'hit and run'),
]

# Common English stop words that carry no discriminating signal in a legal corpus.
# Keeping them causes BM25 to match every query that contains "is", "the", "a", etc.
# against sections that happen to use those words — producing false citations.
_STOP_WORDS: frozenset[str] = frozenset({
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'shall', 'can', 'not', 'no', 'it',
    'its', 'this', 'that', 'these', 'those', 'what', 'which', 'who', 'how',
    'when', 'where', 'why', 'i', 'me', 'my', 'he', 'she', 'we', 'they',
    'you', 'your', 'his', 'her', 'our', 'their', 'as', 'if', 'so', 'than',
    'then', 'there', 'here', 'all', 'any', 'each', 'both', 'into', 'about',
    'such', 'per', 'more', 'also', 'while', 'under', 'over',
})

# Absolute minimum score for the top-ranked document.  The stop-word filter
# handles most noise (off-topic queries reduce to unknown tokens that score 0),
# but this catches the residual case where a single low-IDF domain word (e.g.
# "fine" in "wine and fine dining") produces a weak non-zero match.
# Set low deliberately — the stop-word filter is the primary defence; this is
# just a backstop for degenerate single-token overlaps.
_MIN_TOP_SCORE: float = 0.05


def _normalize_text(text: str) -> str:
    for pattern, replacement in _NORMALIZATIONS:
        text = pattern.sub(replacement, text)
    return text


def _tokenize(text: str) -> list[str]:
    """Lowercase, normalize compound words, split on non-alpha-numeric, strip stop words."""
    text = _normalize_text(text.lower())
    tokens = re.split(r'[^a-z0-9]+', text)
    return [t for t in tokens if t and t not in _STOP_WORDS]


def _build_bm25_index(documents: list) -> BM25Okapi | None:
    tokenized_corpus = []
    for doc in documents:
        text = doc.full_text or doc.explanation_text or ""
        tokenized_corpus.append(_tokenize(text))
    if tokenized_corpus:
        return BM25Okapi(tokenized_corpus)
    return None


class BM25Retriever:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.bm25: BM25Okapi | None = None
        self.documents: list = []
        self.last_indexed: float = 0

    async def initialize(self):
        # Rebuild index at most every 30 minutes.
        if self.bm25 and time.time() - self.last_indexed < 1800:
            return

        stmt = select(LegalSection).execution_options(yield_per=1000)
        result = await self.session.stream_scalars(stmt)

        self.documents = []
        async for doc in result:
            self.documents.append(doc)

        if self.documents:
            self.bm25 = await asyncio.to_thread(_build_bm25_index, self.documents)
            self.last_indexed = time.time()

    async def search(self, query: str, top_k: int = 5) -> list[LegalChunk]:
        await self.initialize()
        if not self.bm25:
            return []

        tokenized_query = _tokenize(query)
        tokenized_query = [t for t in tokenized_query if t]  # drop empty tokens
        if not tokenized_query:
            return []

        doc_scores = self.bm25.get_scores(tokenized_query)
        if not len(doc_scores):
            return []

        max_score = max(doc_scores)

        # Absolute floor: if even the best-matching document scores below this,
        # every match is noise (stop words, single low-IDF tokens).  Return nothing
        # rather than surface irrelevant citations with a misleading "legal" label.
        if max_score < _MIN_TOP_SCORE:
            return []

        # Relative floor: within the passing set, drop anything scoring less than
        # 25% of the top result to prune weak secondary matches.
        # 10% was too permissive — high-frequency domain words like "driving" and
        # "fine" caused unrelated sections to score ~12-18% of the top result and
        # enter the citation list.  25% eliminates these while retaining genuinely
        # relevant secondary sections (e.g. Section 129 for a helmet query where
        # both 129 and 194D score close to each other).
        threshold = max_score * 0.25

        scored_docs = sorted(zip(doc_scores, self.documents), key=lambda x: x[0], reverse=True)
        top_docs = scored_docs[:top_k]

        results = []
        for score, doc in top_docs:
            if score < threshold:
                continue
            results.append(LegalChunk(
                id=doc.id,
                act_name=doc.act_name,
                section_number=doc.section_number,
                chapter=doc.chapter,
                clause=doc.clause,
                text=doc.full_text or doc.explanation_text or "",
                jurisdiction_id=doc.jurisdiction_id,
                source_url=doc.source_url,
            ))

        return results
