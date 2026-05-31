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

async def seed_gujarat_penalties(session: AsyncSession):
    # Get Gujarat jurisdiction
    stmt = select(Jurisdiction).where(Jurisdiction.code == "IN-GJ")
    result = await session.execute(stmt)
    gujarat = result.scalars().first()
    
    if not gujarat:
        logger.error("Gujarat jurisdiction (IN-GJ) not found. Run seed_jurisdictions first.")
        return

    # Load dataset
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'data', 'gujurat.json')
    if not os.path.exists(data_path):
        logger.error(f"Dataset file not found at {data_path}")
        return

    with open(data_path, 'r') as f:
        data = json.load(f)

    penalties = data.get("gujarat_transport_penalty_structure", {}).get("penalties", [])
    logger.info(f"Loaded {len(penalties)} Gujarat penalty structures from {data_path}. Seeding...")

    count = 0
    for item in penalties:
        sr_no = item.get("sr_no")
        section = item.get("section", "")
        enforcing = item.get("enforcing_officers", [])
        description = item.get("description", "")
        offences_list = item.get("offences", [])
        
        # Build nice text for offences
        offences_text = []
        for o in offences_list:
            if isinstance(o, dict):
                offences_text.append(f"- {o.get('offence', '')} (First offence fine: {o.get('first_offence_inr_by_vehicle', '')})")
            else:
                offences_text.append(f"- {o}")
        offences_joined = "\n".join(offences_text)

        # Build fine structure description
        fine_details = []
        if "first_offence_inr" in item:
            fine_details.append(f"First offence fine: INR {item.get('first_offence_inr')}")
        if "second_or_subsequent_offence_inr" in item:
            fine_details.append(f"Second or subsequent offence fine: {item.get('second_or_subsequent_offence_inr')}")
        if "first_offence_inr_by_vehicle" in item:
            fine_details.append(f"First offence fine by vehicle category: {item.get('first_offence_inr_by_vehicle')}")
        if "second_or_subsequent_offence_by_vehicle" in item:
            fine_details.append(f"Second or subsequent offence by vehicle category: {item.get('second_or_subsequent_offence_by_vehicle')}")
        if "first_offence" in item:
            fine_details.append(f"First offence penalty: {item.get('first_offence')}")
            
        fine_text = ", ".join(fine_details)

        page_index = f"gj-penalty:{sr_no}"
        
        defaults = {
            "act_name": "Motor Vehicles Act and Gujarat Rules",
            "section_number": section,
            "chapter": "Penalties",
            "explanation_text": f"Description: {description}\nEnforcing Officers: {', '.join(enforcing)}",
            "full_text": f"Gujarat Traffic Penalty Section {section}:\nDescription: {description}\nOffences:\n{offences_joined}\nPenalties: {fine_text}\nEnforcing Officers: {', '.join(enforcing)}",
            "jurisdiction_id": gujarat.id,
        }

        # Generate embedding if model is loaded
        if EMBEDDING_MODEL:
            try:
                content_to_embed = f"Gujarat Traffic Penalty: Section {section}. {description} {offences_joined} {fine_text}"
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

    logger.info(f"Successfully seeded {count} Gujarat traffic penalties.")
