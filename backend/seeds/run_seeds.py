import asyncio
import logging
from backend.database import async_session_maker
from backend.seeds.seed_jurisdictions import seed_jurisdictions
from backend.seeds.seed_violations import seed_violations
from backend.seeds.seed_legal_sections import seed_legal_sections
from backend.seeds.seed_fines import seed_fines
from backend.ingest.pipeline import run_ingest_pipeline
from backend.seeds.seed_maharashtra_echallan import seed_maharashtra_echallan
from backend.seeds.seed_maharashtra_offenses import seed_maharashtra_offenses
from backend.seeds.seed_gujarat_penalties import seed_gujarat_penalties
from backend.seeds.seed_uttarakhand import seed_uttarakhand
from backend.seeds.seed_kerala import seed_kerala
from backend.seeds.seed_mp import seed_mp
from backend.seeds.seed_telangana import seed_telangana
from backend.seeds.seed_rajasthan import seed_rajasthan
from backend.seeds.seed_sikkim import seed_sikkim
from backend.seeds.seed_india_operational import seed_india_operational
from backend.seeds.seed_drivelegal_db import seed_drivelegal_db

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

            logger.info("Seeding Maharashtra e-challan data...")
            await seed_maharashtra_echallan(session)

            logger.info("Seeding Maharashtra traffic offenses...")
            await seed_maharashtra_offenses(session)

            logger.info("Seeding Gujarat traffic penalties...")
            await seed_gujarat_penalties(session)

            logger.info("Seeding Uttarakhand notifications & documents...")
            await seed_uttarakhand(session)

            logger.info("Seeding Kerala regulations...")
            await seed_kerala(session)

            logger.info("Seeding Madhya Pradesh road safety policy...")
            await seed_mp(session)

            logger.info("Seeding Telangana taxation act & rules...")
            await seed_telangana(session)

            logger.info("Seeding Rajasthan Act and Rules...")
            await seed_rajasthan(session)

            logger.info("Seeding Sikkim Transport Department data...")
            await seed_sikkim(session)

            logger.info("Seeding India Traffic Control SOP/operational data...")
            await seed_india_operational(session)

            logger.info("Seeding drivelegal database details...")
            await seed_drivelegal_db(session)

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
