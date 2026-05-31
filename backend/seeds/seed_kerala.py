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

async def seed_kerala(session: AsyncSession):
    # Get Kerala jurisdiction
    stmt = select(Jurisdiction).where(Jurisdiction.code == "IN-KL")
    result = await session.execute(stmt)
    kerala = result.scalars().first()
    
    if not kerala:
        logger.error("Kerala jurisdiction (IN-KL) not found. Run seed_jurisdictions first.")
        return

    # Load dataset kerala.json
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'data', 'kerala.json')
    if not os.path.exists(data_path):
        logger.error(f"Dataset file not found at {data_path}")
        return

    with open(data_path, 'r') as f:
        dataset = json.load(f)

    doc_info = dataset.get("document", {})
    circular_info = dataset.get("kerala_circular", {})
    definitions = dataset.get("definitions", {})
    regulations = dataset.get("regulations", [])

    logger.info(f"Loaded circular, definitions, and {len(regulations)} regulations for Kerala. Seeding...")

    count = 0

    # 1. Seed circular
    if circular_info:
        circular_no = circular_info.get("circular_no", "15/2018")
        purpose = circular_info.get("purpose", "")
        signed_by = circular_info.get("signed_by", "")
        penalty = circular_info.get("penalty", {})
        
        full_text = f"Circular No: {circular_no}\nReference: {circular_info.get('ref_no')}\nDate: {circular_info.get('date')}\nIssued By: {circular_info.get('issued_by')}\nPurpose: {purpose}\nSigned By: {signed_by}\nPenalties: {json.dumps(penalty)}"
        page_index = f"kl-circular:{circular_no.replace('/', '-')}"
        
        defaults = {
            "act_name": f"Kerala Police Circular {circular_no}",
            "section_number": f"KL-CIRCULAR-{circular_no}",
            "chapter": "Circulars",
            "explanation_text": f"Circular on implementation of driving regulations. Purpose: {purpose}",
            "full_text": full_text,
            "jurisdiction_id": kerala.id,
        }

        if EMBEDDING_MODEL:
            try:
                content_to_embed = f"Kerala Circular {circular_no}: {purpose}. Penalties: {json.dumps(penalty)}"
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

    # 2. Seed definitions
    if definitions:
        def_lines = []
        for term, meaning in definitions.items():
            def_lines.append(f"- {term.replace('_', ' ').capitalize()}: {meaning}")
        
        full_text = "Definitions under Motor Vehicles (Driving) Regulations:\n" + "\n".join(def_lines)
        page_index = "kl-definitions"
        
        defaults = {
            "act_name": doc_info.get("title", "Motor Vehicles (Driving) Regulations, 2017"),
            "section_number": "KL-DEFINITIONS",
            "chapter": "Definitions",
            "explanation_text": "Key terms and definitions used in the Motor Vehicles Driving Regulations.",
            "full_text": full_text,
            "jurisdiction_id": kerala.id,
        }

        if EMBEDDING_MODEL:
            try:
                content_to_embed = f"Kerala Motor Vehicles Driving Regulations Definitions. {full_text[:500]}"
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

    # 3. Seed regulations
    for reg in regulations:
        reg_no = reg.get("reg_no")
        title = reg.get("title", "")
        rules = reg.get("rules", [])
        
        full_text_parts = [f"Regulation {reg_no}: {title}", "\nRules:"]
        for rule in rules:
            full_text_parts.append(f"- {rule}")
            
        # check for other keys like left_turn, right_turn, u_turn, hand_signals, red_light, etc.
        for key in ["left_turn", "right_turn", "u_turn", "hand_signals", "red_light", "green_light", "amber_light", "minor_accidents", "major_accidents", "interacting_with_other_driver", "driver_must_know"]:
            if key in reg:
                val = reg.get(key)
                full_text_parts.append(f"\n{key.replace('_', ' ').capitalize()}:")
                if isinstance(val, list):
                    for item in val:
                        full_text_parts.append(f"- {item}")
                elif isinstance(val, dict):
                    for sub_k, sub_v in val.items():
                        full_text_parts.append(f"- {sub_k.replace('_', ' ').capitalize()}: {json.dumps(sub_v) if isinstance(sub_v, (list, dict)) else sub_v}")
                else:
                    full_text_parts.append(str(val))

        full_text = "\n".join(full_text_parts)
        page_index = f"kl-reg:{reg_no}"
        
        defaults = {
            "act_name": doc_info.get("title", "Motor Vehicles (Driving) Regulations, 2017"),
            "section_number": f"KL-REG-{reg_no}",
            "chapter": "Driving Regulations",
            "explanation_text": f"Regulation {reg_no}: {title}",
            "full_text": full_text,
            "jurisdiction_id": kerala.id,
        }

        if EMBEDDING_MODEL:
            try:
                content_to_embed = f"Kerala Motor Vehicles Driving Regulation {reg_no} - {title}: {full_text[:500]}"
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

    logger.info(f"Successfully seeded {count} Kerala sections.")
