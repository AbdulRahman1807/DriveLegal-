import asyncio
from sqlalchemy import select, func, or_
from backend.database import async_session_maker
from backend.models.legal_section import LegalSection

async def main():
    async with async_session_maker() as session:
        # User requested to match 'helmet' or 'alcohol'. We can construct this query using SQLAlchemy's op('@@') for tsvector.
        # func.to_tsquery('english', 'helmet | alcohol')
        # We can also do individual terms to be safer, or construct 'helmet | alcohol'
        # Let's do the single query with 'helmet | alcohol' as it exactly fits "matches the term 'helmet' or 'alcohol'"
        # Wait, the prompt says: "matches the term 'helmet' or 'alcohol' using `func.to_tsquery('english', 'helmet')`"
        # I'll create a single query with or_ or the TSQuery itself.
        
        query = select(LegalSection).where(
            or_(
                LegalSection.keywords.op('@@')(func.to_tsquery('english', 'helmet')),
                LegalSection.keywords.op('@@')(func.to_tsquery('english', 'alcohol'))
            )
        )
        
        print("Executing full-text search for 'helmet' or 'alcohol'...")
        result = await session.execute(query)
        sections = result.scalars().all()
        
        print(f"Found {len(sections)} matches.")
        for sec in sections:
            print(f"- Act: {sec.act_name}, Section: {sec.section_number}")

if __name__ == "__main__":
    asyncio.run(main())
