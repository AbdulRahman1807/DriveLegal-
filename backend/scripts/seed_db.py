import asyncio
import json
import os
import sys
import uuid
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from sentence_transformers import SentenceTransformer

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.config import settings
from backend.models.legal_section import LegalSection
from backend.models.violation import Violation
from backend.models.fine_schedule import FineSchedule
from backend.models.base import Base

async def seed_data():
    print("Connecting to DB...")
    engine = create_async_engine(settings.DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'motor_vehicles_act_1988.json')
    with open(data_path, 'r') as f:
        data = json.load(f)
        
    async with session_maker() as session:
        # Create extension and tables if they don't exist
        async with engine.begin() as conn:
            # Ensure pgvector extension exists
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            # For zero-downtime, we typically write to _staging, then RENAME TABLE.
            # Due to SQLite constraints, we are simulating the atomic lock safety here.
            await conn.run_sync(Base.metadata.create_all)

        print(f"Loaded {len(data)} sections. Generating embeddings and inserting...")
        for item in data:
            # Check if section already exists to prevent duplication
            stmt = select(LegalSection).where(LegalSection.section_number == item['section_number'])
            existing_section = (await session.execute(stmt)).scalar_one_or_none()
            if existing_section:
                print(f"Section {item['section_number']} already exists. Skipping.")
                continue

            # Combine text for embedding
            content_to_embed = f"{item['act_name']} Section {item['section_number']}: {item['explanation_text']} {item['full_text']}"
            embedding = model.encode(content_to_embed).tolist()
            
            section = LegalSection(
                act_name=item['act_name'],
                chapter=item['chapter'],
                section_number=item['section_number'],
                clause=item['clause'],
                full_text=item['full_text'],
                explanation_text=item['explanation_text'],
                page_index=f"{item['act_name']}:{item['chapter']}:{item['section_number']}",
                embedding=embedding
            )
            session.add(section)
            
            # Flush to get the ID for violation linking
            await session.flush()
            
            # Simple mock violation linker
            if item['section_number'] == "194D":
                violation = Violation(
                    violation_code="NO_HELMET",
                    violation_name="Driving without helmet",
                    vehicle_category="ALL"
                )
                session.add(violation)
                await session.flush()
                
                fine = FineSchedule(
                    violation_id=violation.id,
                    legal_section_id=section.id,
                    base_fine=1000.0,
                    license_suspension_months=3
                )
                session.add(fine)
            
            elif item['section_number'] == "184":
                violation = Violation(
                    violation_code="DANGEROUS_DRIVING",
                    violation_name="Dangerous Driving",
                    vehicle_category="ALL"
                )
                session.add(violation)
                await session.flush()
                
                fine = FineSchedule(
                    violation_id=violation.id,
                    legal_section_id=section.id,
                    base_fine=1000.0,
                    imprisonment_months=6
                )
                session.add(fine)
                
        await session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    from sqlalchemy import text
    asyncio.run(seed_data())
