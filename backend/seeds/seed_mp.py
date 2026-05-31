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

async def seed_mp(session: AsyncSession):
    # Get MP jurisdiction
    stmt = select(Jurisdiction).where(Jurisdiction.code == "IN-MP")
    result = await session.execute(stmt)
    mp = result.scalars().first()
    
    if not mp:
        logger.error("Madhya Pradesh jurisdiction (IN-MP) not found. Run seed_jurisdictions first.")
        return

    # Load dataset mp.json
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'data', 'mp.json')
    if not os.path.exists(data_path):
        logger.error(f"Dataset file not found at {data_path}")
        return

    with open(data_path, 'r') as f:
        dataset = json.load(f)

    title = dataset.get("title", "Madhya Pradesh State Road Safety Policy 2015")
    slogan = dataset.get("slogan", "")
    framework = dataset.get("framework", "")
    four_es = dataset.get("four_es", [])
    vision = dataset.get("vision", [])
    mission = dataset.get("mission", [])
    pillars = dataset.get("pillars", [])

    logger.info(f"Loaded road safety policy '{title}' with {len(pillars)} pillars. Seeding...")

    count = 0

    # 1. Seed Policy Intro
    intro_parts = [
        f"Title: {title}",
        f"Slogan: {slogan}",
        f"Framework: {framework}",
        f"Four Es: {', '.join(four_es)}",
        "\nVision:",
    ]
    for v in vision:
        intro_parts.append(f"- {v}")
    intro_parts.append("\nMission:")
    for m in mission:
        intro_parts.append(f"- {m}")
        
    full_text = "\n".join(intro_parts)
    page_index = "mp-intro"
    
    defaults = {
        "act_name": title,
        "section_number": "MP-POLICY-INTRO",
        "chapter": "Introduction",
        "explanation_text": f"Introduction, Vision, and Mission of Madhya Pradesh State Road Safety Policy.",
        "full_text": full_text,
        "jurisdiction_id": mp.id,
    }

    if EMBEDDING_MODEL:
        try:
            content_to_embed = f"Madhya Pradesh Road Safety Policy Intro. Vision: {', '.join(vision)}. Mission: {', '.join(mission)}"
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

    # 2. Seed Pillars
    for p in pillars:
        pillar_no = p.get("pillar")
        p_title = p.get("title", "")
        policy_statement = p.get("policy_statement", "")
        
        full_text_parts = [
            f"Pillar {pillar_no}: {p_title}",
            f"Policy Statement: {policy_statement}",
        ]

        # Strategies by department
        if "strategies_by_department" in p:
            full_text_parts.append("\nStrategies by Department:")
            for dept, strats in p["strategies_by_department"].items():
                full_text_parts.append(f"\n{dept}:")
                for s in strats:
                    full_text_parts.append(f"- {s}")

        # Key Institutions
        if "key_institutions" in p:
            full_text_parts.append("\nKey Institutions:")
            for inst in p["key_institutions"]:
                name = inst.get("name", "")
                desc = inst.get("description", "")
                members = inst.get("members", [])
                inst_str = f"- {name}"
                if desc:
                    inst_str += f": {desc}"
                if members:
                    inst_str += f" (Members: {', '.join(members)})"
                full_text_parts.append(inst_str)

        # Strategies (plain dict)
        if "strategies" in p:
            full_text_parts.append("\nStrategies:")
            for s_key, s_val in p["strategies"].items():
                full_text_parts.append(f"\n{s_key}:")
                if isinstance(s_val, list):
                    for val in s_val:
                        full_text_parts.append(f"- {val}")
                else:
                    full_text_parts.append(f"- {s_val}")

        # Other measures / lists
        for key in ["SRSTRDC_tasks", "State_Road_Safety_Fund_sources", "new_measures", "pilot_phase", "road_side_regulation", "commercial_tax", "enforcement", "measures", "key_measures", "key_provisions", "State_Trauma_System_Plan", "Police_measures"]:
            if key in p:
                val = p.get(key)
                full_text_parts.append(f"\n{key.replace('_', ' ').capitalize()}:")
                if isinstance(val, list):
                    for item in val:
                        full_text_parts.append(f"- {item}")
                elif isinstance(val, dict):
                    for sub_k, sub_v in val.items():
                        full_text_parts.append(f"- {sub_k}: {sub_v}")
                else:
                    full_text_parts.append(str(val))

        full_text = "\n".join(full_text_parts)
        page_index = f"mp-pillar:{pillar_no}"
        
        defaults = {
            "act_name": title,
            "section_number": f"MP-PILLAR-{pillar_no}",
            "chapter": f"Pillar {pillar_no}",
            "explanation_text": f"Pillar {pillar_no}: {p_title}. Policy Statement: {policy_statement}",
            "full_text": full_text,
            "jurisdiction_id": mp.id,
        }

        if EMBEDDING_MODEL:
            try:
                content_to_embed = f"Madhya Pradesh Road Safety Policy Pillar {pillar_no} - {p_title}: {policy_statement}. {full_text[:500]}"
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

    logger.info(f"Successfully seeded {count} Madhya Pradesh sections.")
