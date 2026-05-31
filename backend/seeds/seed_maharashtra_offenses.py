import logging
import json
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.models.legal_section import LegalSection
from backend.models.jurisdiction import Jurisdiction

# Try to import sentence_transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
except Exception:
    EMBEDDING_MODEL = None

logger = logging.getLogger(__name__)

async def get_or_create(session: AsyncSession, model, defaults=None, **kwargs):
    stmt = select(model).filter_by(**kwargs)
    result = await session.execute(stmt)
    instance = result.scalars().first()
    if instance:
        return instance
    
    params = dict((k, v) for k, v in kwargs.items())
    if defaults:
        params.update(defaults)
    instance = model(**params)
    session.add(instance)
    await session.commit()
    await session.refresh(instance)
    return instance

async def seed_maharashtra_offenses(session: AsyncSession):
    # Get Maharashtra jurisdiction
    stmt = select(Jurisdiction).where(Jurisdiction.code == "IN-MH")
    result = await session.execute(stmt)
    maharashtra = result.scalars().first()
    
    if not maharashtra:
        logger.error("Maharashtra jurisdiction (IN-MH) not found. Run seed_jurisdictions first.")
        return

    # Load dataset
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'data', 'traffic_offences.json')
    if not os.path.exists(data_path):
        logger.error(f"Dataset file not found at {data_path}")
        return

    with open(data_path, 'r') as f:
        offenses = json.load(f)

    logger.info(f"Loaded {len(offenses)} Maharashtra offenses from {data_path}. Seeding...")

    count = 0
    for item in offenses:
        sr_no = item.get("sr_no")
        section = item.get("section", "")
        offense_eng = item.get("offense_english", "")
        offense_mar = item.get("offense_marathi", "")

        page_index = f"mh-offense:{sr_no}"
        
        defaults = {
            "act_name": "Motor Vehicles Act and Maharashtra Rules",
            "section_number": section,
            "chapter": "Traffic Violations and Penalties",
            "explanation_text": f"English: {offense_eng}\nMarathi: {offense_mar}",
            "full_text": f"Offense (English): {offense_eng}\nगुन्हा (मराठी): {offense_mar}\nSection: {section}",
            "jurisdiction_id": maharashtra.id,
        }

        # Generate embedding if model is loaded
        if EMBEDDING_MODEL:
            try:
                content_to_embed = f"Maharashtra Traffic Offense: {section}. {offense_eng} {offense_mar}"
                embedding = EMBEDDING_MODEL.encode(content_to_embed).tolist()
                defaults["embedding"] = embedding
            except Exception as ex:
                logger.warning(f"Failed to generate embedding for {page_index}: {ex}")

        instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
        
        # Populate TSVECTOR
        if not instance.keywords:
            if session.bind.dialect.name == 'sqlite':
                instance.keywords = instance.full_text
            else:
                instance.keywords = func.to_tsvector('english', instance.full_text)
            session.add(instance)
            await session.commit()
            
        count += 1

    logger.info(f"Successfully seeded {count} Maharashtra traffic offenses.")
