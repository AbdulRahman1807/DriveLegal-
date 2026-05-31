import asyncio
import logging
from backend.database import async_session_maker
from backend.seeds.seed_jurisdictions import seed_jurisdictions
from backend.seeds.seed_violations import seed_violations
from backend.seeds.seed_legal_sections import seed_legal_sections
from backend.seeds.seed_fines import seed_fines
from backend.ingest.pipeline import run_ingest_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_all_seeds():
    logger.info("Starting database seeding...")
    async with async_session_maker() as session:
        try:
            logger.info("Seeding jurisdictions...")
            await seed_jurisdictions(session)

            logger.info("Seeding violations...")
            await seed_violations(session)

            logger.info("Seeding legal sections...")
            await seed_legal_sections(session)

            logger.info("Seeding fine schedules...")
            await seed_fines(session)

            logger.info("Running JSON ingest pipeline (Phase 1)...")
            await run_ingest_pipeline(session)

            logger.info("Database seeding completed successfully.")
        except Exception as e:
            logger.error(f"Error during seeding: {e}", exc_info=True)
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(run_all_seeds())
