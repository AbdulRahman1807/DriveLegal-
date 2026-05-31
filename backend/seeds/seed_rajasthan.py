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

async def seed_rajasthan(session: AsyncSession):
    # Get Rajasthan jurisdiction
    stmt = select(Jurisdiction).where(Jurisdiction.code == "IN-RJ")
    result = await session.execute(stmt)
    rajasthan = result.scalars().first()
    
    if not rajasthan:
        logger.error("Rajasthan jurisdiction (IN-RJ) not found. Run seed_jurisdictions first.")
        return

    # Load dataset rajasthan.json
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'data', 'rajasthan.json')
    if not os.path.exists(data_path):
        logger.error(f"Dataset file not found at {data_path}")
        return

    with open(data_path, 'r') as f:
        dataset = json.load(f)

    documents = dataset.get("documents", [])

    logger.info(f"Loaded {len(documents)} documents for Rajasthan. Seeding...")

    count = 0

    # Seed documents and sections
    for doc in documents:
        doc_id = doc.get("doc_id")
        title = doc.get("title", "")
        purpose = doc.get("purpose", "")
        
        # If it's a simple document with only meta info
        if "sections" not in doc and "chapters" not in doc:
            page_index = f"rj-doc:{doc_id}"
            full_text = f"Title: {title}\nPurpose: {purpose}"
            defaults = {
                "act_name": title,
                "section_number": doc_id,
                "chapter": "Overview",
                "explanation_text": purpose,
                "full_text": full_text,
                "jurisdiction_id": rajasthan.id,
            }
            if EMBEDDING_MODEL:
                try:
                    embedding = EMBEDDING_MODEL.encode(full_text).tolist()
                    defaults["embedding"] = embedding
                except Exception as ex:
                    logger.warning(f"Failed to generate embedding for {page_index}: {ex}")

            instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
            if not instance.keywords:
                if session.bind.dialect.name == 'sqlite':
                    instance.keywords = instance.full_text
                else:
                    instance.keywords = func.to_tsvector('english', instance.full_text)
                session.add(instance)
                await session.commit()
            count += 1
            continue

        # If it has chapters
        if "chapters" in doc:
            for ch in doc["chapters"]:
                ch_title = ch.get("title", "")
                ch_no = ch.get("chapter", "")
                page_index = f"rj-chapter:{doc_id}:{ch_no}"
                full_text = f"Act: {title}\nChapter {ch_no}: {ch_title}"
                defaults = {
                    "act_name": title,
                    "section_number": f"RJ-CH-{ch_no}",
                    "chapter": ch_title,
                    "explanation_text": f"Chapter {ch_no} of {title}",
                    "full_text": full_text,
                    "jurisdiction_id": rajasthan.id,
                }
                if EMBEDDING_MODEL:
                    try:
                        embedding = EMBEDDING_MODEL.encode(full_text).tolist()
                        defaults["embedding"] = embedding
                    except Exception as ex:
                        logger.warning(f"Failed to generate embedding for {page_index}: {ex}")

                instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
                if not instance.keywords:
                    if session.bind.dialect.name == 'sqlite':
                        instance.keywords = instance.full_text
                    else:
                        instance.keywords = func.to_tsvector('english', instance.full_text)
                    session.add(instance)
                    await session.commit()
                count += 1
            continue

        # If it has sections
        sections = doc.get("sections", [])
        for sec in sections:
            sec_no = sec.get("section")
            sec_title = sec.get("title", "")
            
            full_text_parts = [
                f"Act: {title}",
                f"Section {sec_no}: {sec_title}"
            ]
            
            if "text" in sec:
                full_text_parts.append(sec["text"])
            if "description" in sec:
                full_text_parts.append(sec["description"])
            if "definitions" in sec:
                full_text_parts.append("Definitions:")
                for d in sec["definitions"]:
                    full_text_parts.append(f"- {d.get('term')}: {d.get('meaning')}")
            if "sub_sections" in sec:
                full_text_parts.append("Sub-sections:")
                for sub in sec["sub_sections"]:
                    full_text_parts.append(f"- Sub-section {sub.get('sub_section')}: {sub.get('description')}")
                    if "rate_limits" in sub:
                        full_text_parts.append(f"  Rate limits: {json.dumps(sub.get('rate_limits'))}")
            if "green_tax_table" in sec:
                full_text_parts.append(f"Green Tax Details: {json.dumps(sec.get('green_tax_table'))}")
            if "offences" in sec:
                full_text_parts.append("Offences and Penalties:")
                for off in sec["offences"]:
                    full_text_parts.append(f"- Offence: {off.get('offence')} | Punishment: {off.get('punishment')}")

            full_text = "\n".join(full_text_parts)
            page_index = f"rj-section:{doc_id}:{sec_no}"
            
            defaults = {
                "act_name": title,
                "section_number": f"RJ-SEC-{sec_no}",
                "chapter": sec_title,
                "explanation_text": f"Section {sec_no} of {title}",
                "full_text": full_text,
                "jurisdiction_id": rajasthan.id,
            }
            if EMBEDDING_MODEL:
                try:
                    content_to_embed = f"Rajasthan transport law Section {sec_no} - {sec_title}: {full_text[:500]}"
                    embedding = EMBEDDING_MODEL.encode(content_to_embed).tolist()
                    defaults["embedding"] = embedding
                except Exception as ex:
                    logger.warning(f"Failed to generate embedding for {page_index}: {ex}")

            instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
            if not instance.keywords:
                if session.bind.dialect.name == 'sqlite':
                    instance.keywords = instance.full_text
                else:
                    instance.keywords = func.to_tsvector('english', instance.full_text)
                session.add(instance)
                await session.commit()
            count += 1

    # Also seed Key definitions and tax payment rules from Rule 001 if exists
    key_defs = doc.get("key_definitions", [])
    if key_defs:
        page_index = f"rj-rule:key-definitions"
        full_text = "Rajasthan Motor Vehicles Taxation Rules - Key Definitions:\n" + "\n".join([f"- {d.get('term')}: {d.get('meaning')}" for d in key_defs])
        defaults = {
            "act_name": "The Rajasthan Motor Vehicles Taxation Rules, 1951",
            "section_number": "RJ-RULE-DEFS",
            "chapter": "Definitions",
            "explanation_text": "Key definitions under Rajasthan Motor Vehicles Taxation Rules",
            "full_text": full_text,
            "jurisdiction_id": rajasthan.id,
        }
        if EMBEDDING_MODEL:
            try:
                embedding = EMBEDDING_MODEL.encode(full_text).tolist()
                defaults["embedding"] = embedding
            except Exception as ex:
                logger.warning(f"Failed to generate embedding for {page_index}: {ex}")

        instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
        if not instance.keywords:
            if session.bind.dialect.name == 'sqlite':
                instance.keywords = instance.full_text
            else:
                instance.keywords = func.to_tsvector('english', instance.full_text)
            session.add(instance)
            await session.commit()
        count += 1

    logger.info(f"Successfully seeded {count} Rajasthan sections.")
