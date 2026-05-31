import re
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.violation import Violation
from backend.models.jurisdiction import Jurisdiction

logger = structlog.get_logger(__name__)

# Compound-word normalization: "motorcycle" → "motor cycle" and vice versa,
# applied before matching so surface form differences don't cause misses.
_COMPOUND_NORMALIZATIONS = [
    (r'\bmotorcycle\b', 'motor cycle'),
    (r'\btwo[\s-]?wheeler\b', 'two wheeler'),
    (r'\bseatbelt\b', 'seat belt'),
    (r'\bdrunk[\s-]?driving\b', 'drunk driving'),
    (r'\bhit[\s-]?and[\s-]?run\b', 'hit and run'),
]


def _normalize(text: str) -> str:
    text = text.lower()
    for pattern, replacement in _COMPOUND_NORMALIZATIONS:
        text = re.sub(pattern, replacement, text)
    return text


class QueryParser:
    """
    Infers structured retrieval fields (violation_code, jurisdiction_id) from a
    natural language query by scoring against DB-stored keywords, aliases, and names.

    This is intentionally a lightweight lexical layer — not an LLM call — so it
    adds negligible latency and has no external failure surface.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def infer_violation_code(self, query: str) -> str | None:
        q = _normalize(query)

        result = await self.session.execute(select(Violation))
        violations = result.scalars().all()

        best_code: str | None = None
        best_score = 0

        for v in violations:
            score = 0

            # Name: high weight (3pts) — "Driving without helmet"
            if v.name and _normalize(v.name) in q:
                score += 3

            # Aliases: medium weight (2pts each) — ["no helmet", "without helmet"]
            if v.aliases:
                for alias in v.aliases:
                    if alias and _normalize(alias) in q:
                        score += 2

            # Keywords: low weight (1pt each) — "helmet, headgear, without helmet"
            if v.keywords:
                for kw in [k.strip() for k in v.keywords.split(',')]:
                    if kw and _normalize(kw) in q:
                        score += 1

            if score > best_score:
                best_score = score
                best_code = v.violation_code

        if best_score > 0:
            logger.info("query_parser.violation_inferred",
                        violation_code=best_code, score=best_score)
            return best_code

        logger.debug("query_parser.no_violation_inferred", query=query)
        return None

    async def infer_jurisdiction_id(self, query: str) -> str | None:
        q = _normalize(query)

        result = await self.session.execute(select(Jurisdiction))
        jurisdictions = result.scalars().all()

        # Prefer the most specific (longest matching name) jurisdiction —
        # "Tamil Nadu" beats "India" if both appear in the query.
        best_id: str | None = None
        best_len = 0

        for j in jurisdictions:
            name_norm = _normalize(j.name)
            if name_norm in q and len(name_norm) > best_len:
                best_len = len(name_norm)
                best_id = str(j.id)

        if best_id:
            logger.info("query_parser.jurisdiction_inferred",
                        jurisdiction_id=best_id, match_len=best_len)
        else:
            logger.debug("query_parser.no_jurisdiction_inferred", query=query)

        return best_id
