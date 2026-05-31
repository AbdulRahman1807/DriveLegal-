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
        # Update existing
        if defaults:
            for k, v in defaults.items():
                setattr(instance, k, v)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
        return instance
    
    params = dict((k, v) for k, v in kwargs.items())
    if defaults:
        params.update(defaults)
    instance = model(**params)
    session.add(instance)
    await session.commit()
    await session.refresh(instance)
    return instance

async def seed_telangana(session: AsyncSession):
    # Get Telangana jurisdiction
    stmt = select(Jurisdiction).where(Jurisdiction.code == "IN-TG")
    result = await session.execute(stmt)
    telangana = result.scalars().first()
    
    if not telangana:
        logger.error("Telangana jurisdiction (IN-TG) not found. Run seed_jurisdictions first.")
        return

    # 1. Load and seed telegana.json (Act)
    act_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'data', 'telegana.json')
    if os.path.exists(act_path):
        with open(act_path, 'r') as f:
            dataset = json.load(f)

        act_data = dataset.get("act", {})
        title = act_data.get("title", "Telangana Motor Vehicles Taxation Act")
        purpose = act_data.get("purpose", "")
        sections = act_data.get("sections", [])

        logger.info(f"Loaded taxation act '{title}' with {len(sections)} sections. Seeding...")

        # Seed Act Intro
        page_index = "tg-intro"
        defaults = {
            "act_name": title,
            "section_number": "TG-TAX-INTRO",
            "chapter": "Introduction",
            "explanation_text": f"Purpose: {purpose}",
            "full_text": f"Act: {title}\nYear: {act_data.get('year')}\nPurpose: {purpose}\nJurisdiction: {act_data.get('jurisdiction')}",
            "jurisdiction_id": telangana.id,
        }

        if EMBEDDING_MODEL:
            try:
                content_to_embed = f"Telangana Motor Vehicles Taxation Act. Purpose: {purpose}"
                embedding = EMBEDDING_MODEL.encode(content_to_embed).tolist()
                defaults["embedding"] = embedding
            except Exception as ex:
                logger.warning(f"Failed to generate embedding for {page_index}: {ex}")

        instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
        if not instance.keywords:
            instance.keywords = instance.full_text
            session.add(instance)
            await session.commit()

        # Seed Sections
        for sec in sections:
            sec_no = sec.get("section")
            sec_title = sec.get("title", "")
            clauses = sec.get("clauses", [])
            definitions = sec.get("definitions", [])
            
            full_text_parts = [
                f"Section {sec_no}: {sec_title}",
            ]

            if clauses:
                full_text_parts.append("\nClauses:")
                for cl in clauses:
                    clause_no = cl.get("clause", "")
                    text = cl.get("text", "")
                    provisos = cl.get("provisos", [])
                    
                    cl_str = f"- Clause {clause_no}: {text}"
                    if provisos:
                        cl_str += f"\n  Provisos:\n" + "\n".join([f"    * {p}" for p in provisos])
                    full_text_parts.append(cl_str)

            if definitions:
                full_text_parts.append("\nDefinitions:")
                for d in definitions:
                    full_text_parts.append(f"- {d.get('term')}: {d.get('meaning')}")

            for key in ["schedules", "notes", "exceptions"]:
                if key in sec:
                    val = sec.get(key)
                    full_text_parts.append(f"\n{key.replace('_', ' ').capitalize()}: {json.dumps(val)}")

            full_text = "\n".join(full_text_parts)
            page_index = f"tg-section:{sec_no}"
            
            defaults = {
                "act_name": title,
                "section_number": f"TG-SEC-{sec_no}",
                "chapter": sec_title,
                "explanation_text": f"Section {sec_no}: {sec_title}",
                "full_text": full_text,
                "jurisdiction_id": telangana.id,
            }

            if EMBEDDING_MODEL:
                try:
                    content_to_embed = f"Telangana Motor Vehicles Taxation Act Section {sec_no} - {sec_title}: {full_text[:500]}"
                    embedding = EMBEDDING_MODEL.encode(content_to_embed).tolist()
                    defaults["embedding"] = embedding
                except Exception as ex:
                    logger.warning(f"Failed to generate embedding for {page_index}: {ex}")

            instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
            if not instance.keywords:
                instance.keywords = instance.full_text
                session.add(instance)
                await session.commit()
    else:
        logger.warning(f"Act file not found at {act_path}")

    # 2. Load and seed telegana_taxation.json (Rules)
    rules_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'data', 'telegana_taxation.json')
    if os.path.exists(rules_path):
        with open(rules_path, 'r') as f:
            rules_dataset = json.load(f)

        rules_data = rules_dataset.get("rules", {})
        rules_title = rules_data.get("title", "Telangana Motor Vehicles Taxation Rules")
        rules_list = rules_data.get("rules_list", [])

        logger.info(f"Loaded taxation rules '{rules_title}' with {len(rules_list)} rules. Seeding...")

        for r in rules_list:
            rule_no = r.get("rule")
            rule_title = r.get("title", "")
            
            full_text_parts = [
                f"Rule {rule_no}: {rule_title}",
            ]

            if "text" in r:
                full_text_parts.append(r["text"])
            
            if "clauses" in r:
                for cl in r["clauses"]:
                    clause_no = cl.get("clause", "")
                    text = cl.get("text", "")
                    full_text_parts.append(f"- Clause {clause_no}: {text}")
                    if "explanations" in cl:
                        for exp in cl["explanations"]:
                            full_text_parts.append(f"  Explanation: {exp}")
            
            if "definitions" in r:
                full_text_parts.append("Definitions:")
                for d in r["definitions"]:
                    full_text_parts.append(f"- {d.get('term')}: {d.get('meaning')}")

            if "proviso" in r:
                full_text_parts.append(f"Proviso: {r['proviso']}")
            if "provisos" in r:
                full_text_parts.append("Provisos:")
                for p in r["provisos"]:
                    full_text_parts.append(f"- {p}")

            if "sub_rules" in r:
                for sr in r["sub_rules"]:
                    sr_no = sr.get("clause", "")
                    text = sr.get("text", "")
                    full_text_parts.append(f"- Sub-rule {sr_no}: {text}")

            if "penalty_table" in r:
                full_text_parts.append("Penalty Rates:")
                for item in r["penalty_table"]:
                    full_text_parts.append(f"- {item.get('period')}: {item.get('penalty')}")

            full_text = "\n".join(full_text_parts)
            page_index = f"tg-rule:{rule_no}"

            defaults = {
                "act_name": rules_title,
                "section_number": f"TG-RULE-{rule_no}",
                "chapter": rule_title,
                "explanation_text": f"Rule {rule_no}: {rule_title}",
                "full_text": full_text,
                "jurisdiction_id": telangana.id,
            }

            if EMBEDDING_MODEL:
                try:
                    content_to_embed = f"Telangana Motor Vehicles Taxation Rules Rule {rule_no} - {rule_title}: {full_text[:500]}"
                    embedding = EMBEDDING_MODEL.encode(content_to_embed).tolist()
                    defaults["embedding"] = embedding
                except Exception as ex:
                    logger.warning(f"Failed to generate embedding for {page_index}: {ex}")

            instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
            if not instance.keywords:
                instance.keywords = instance.full_text
                session.add(instance)
                await session.commit()
    else:
        logger.warning(f"Rules file not found at {rules_path}")

    logger.info("Successfully seeded all Telangana act and rules data.")
