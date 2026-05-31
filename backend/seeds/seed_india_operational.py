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

async def seed_india_operational(session: AsyncSession):
    # Get India jurisdiction
    stmt = select(Jurisdiction).where(Jurisdiction.code == "IN")
    result = await session.execute(stmt)
    india = result.scalars().first()
    
    if not india:
        logger.error("National jurisdiction (IN) not found. Run seed_jurisdictions first.")
        return

    # Load dataset india.json
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'data', 'india.json')
    if not os.path.exists(data_path):
        logger.error(f"Dataset file not found at {data_path}")
        return

    with open(data_path, 'r') as f:
        dataset = json.load(f)

    proc_data = dataset.get("drivelegal_operational_procedures", {})
    meta = proc_data.get("meta", {})
    doc_title = meta.get("document_title", "Traffic Direction and Control — Standard Operating Procedures")
    sections = proc_data.get("sections", [])

    logger.info(f"Loaded {len(sections)} sections from india.json. Seeding...")

    count = 0
    for sec in sections:
        sec_id = sec.get("section_id")
        sec_code = sec.get("section_code", "")
        title = sec.get("title", "")
        rules = sec.get("rules", [])
        
        full_text_parts = [
            f"Document: {doc_title}",
            f"Section {sec_code}: {title}",
            "\nRules:"
        ]
        
        for rule in rules:
            r_id = rule.get("rule_id", "")
            r_title = rule.get("title", "")
            desc = rule.get("description", "")
            sub = rule.get("sub_rules", [])
            steps = rule.get("procedure_steps", [])
            contingency = rule.get("contingency_plan_elements", [])
            
            rule_str = f"- Rule {r_id}"
            if r_title:
                rule_str += f" ({r_title})"
            rule_str += f": {desc}"
            
            if sub:
                rule_str += "\n  Sub-rules:\n" + "\n".join([f"    * {s.get('sub_id')}: {s.get('description')}" + (f"\n      Details: {json.dumps(s.get('sub_sub_rules'))}" if s.get('sub_sub_rules') else "") for s in sub])
            if steps:
                rule_str += "\n  Procedure Steps:\n" + "\n".join([f"    * {step}" for step in steps])
            if contingency:
                rule_str += "\n  Contingency Elements:\n" + "\n".join([f"    * {item}" for item in contingency])
                
            full_text_parts.append(rule_str)

        full_text = "\n".join(full_text_parts)
        page_index = f"india-op:{sec_id}"
        
        defaults = {
            "act_name": doc_title,
            "section_number": f"TDC-{sec_code}",
            "chapter": "Traffic Direction & Control",
            "explanation_text": f"SOP Section {sec_code}: {title}",
            "full_text": full_text,
            "jurisdiction_id": india.id,
        }

        if EMBEDDING_MODEL:
            try:
                content_to_embed = f"India Traffic Control SOP Section {sec_code} - {title}: {full_text[:500]}"
                embedding = EMBEDDING_MODEL.encode(content_to_embed).tolist()
                defaults["embedding"] = embedding
            except Exception as e:
                logger.warning(f"Failed to generate embedding for {page_index}: {e}")

        instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
        if not instance.keywords:
            instance.keywords = instance.full_text
            session.add(instance)
            await session.commit()
        count += 1

    logger.info(f"Successfully seeded {count} India operational sections.")
