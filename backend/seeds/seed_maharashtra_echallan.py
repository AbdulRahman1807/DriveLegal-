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

async def seed_maharashtra_echallan(session: AsyncSession):
    # Get Maharashtra jurisdiction
    stmt = select(Jurisdiction).where(Jurisdiction.code == "IN-MH")
    result = await session.execute(stmt)
    maharashtra = result.scalars().first()
    
    if not maharashtra:
        logger.error("Maharashtra jurisdiction (IN-MH) not found. Run seed_jurisdictions first.")
        return

    # Load dataset
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'data', 'maharashtra_traffic_echallan.json')
    if not os.path.exists(data_path):
        logger.error(f"Dataset file not found at {data_path}")
        return

    with open(data_path, 'r') as f:
        dataset = json.load(f)

    content = dataset.get("content", {})
    act_title = dataset.get("title", "Traffic E-Challan: Enhancing Road Safety in Maharashtra")

    # Define sections to insert
    sections_to_seed = [
        {
            "page_index": "mh-echallan:intro",
            "defaults": {
                "act_name": act_title,
                "section_number": "MH-ECHALLAN-INTRO",
                "chapter": "Introduction",
                "explanation_text": "Introduction and definition of the Traffic E-Challan system in Maharashtra.",
                "full_text": f"{content.get('introduction', '')}\n\nDefinition: {content.get('what_is_echallan', {}).get('definition', '')}",
                "jurisdiction_id": maharashtra.id,
            }
        },
        {
            "page_index": "mh-echallan:how-works",
            "defaults": {
                "act_name": act_title,
                "section_number": "MH-ECHALLAN-HOW-WORKS",
                "chapter": "How it Works",
                "explanation_text": "Information on violation detection and common traffic violations in Maharashtra.",
                "full_text": f"How violation detection works: {content.get('how_it_works', {}).get('violation_detection', {}).get('description', '')}\n\nCommon violations: " + ", ".join(content.get('how_it_works', {}).get('violation_detection', {}).get('common_violations', [])),
                "jurisdiction_id": maharashtra.id,
            }
        },
        {
            "page_index": "mh-echallan:issuance-dispute",
            "defaults": {
                "act_name": act_title,
                "section_number": "MH-ECHALLAN-ISSUANCE-DISPUTE",
                "chapter": "How it Works",
                "explanation_text": "Challan generation, notifications, details included, and dispute redressal.",
                "full_text": f"Challan Issuance: {content.get('how_it_works', {}).get('challan_issuance', {}).get('description', '')}\n\nChallan details: " + ", ".join(content.get('how_it_works', {}).get('challan_issuance', {}).get('challan_details', [])) + f"\n\nDispute redressal: {content.get('how_it_works', {}).get('dispute_redressal', {}).get('description', '')}",
                "jurisdiction_id": maharashtra.id,
            }
        },
        {
            "page_index": "mh-echallan:payment",
            "defaults": {
                "act_name": act_title,
                "section_number": "MH-ECHALLAN-PAYMENT",
                "chapter": "Payment Options and Process",
                "explanation_text": "Online/offline payment methods and step-by-step payment process for Maharashtra Traffic E-Challan.",
                "full_text": "Online Payment Options: " + ", ".join(content.get('how_it_works', {}).get('payment_options', {}).get('online', [])) + "\nOffline Payment Options: " + ", ".join(content.get('how_it_works', {}).get('payment_options', {}).get('offline', [])) + "\n\nStep-by-step Payment Process:\n" + "\n".join([f"Step {step.get('step')}: {step.get('title')} - {step.get('description')}" for step in content.get('payment_process', [])]),
                "jurisdiction_id": maharashtra.id,
            }
        },
        {
            "page_index": "mh-echallan:benefits-vision",
            "defaults": {
                "act_name": act_title,
                "section_number": "MH-ECHALLAN-BENEFITS-VISION",
                "chapter": "Benefits and Vision",
                "explanation_text": "Benefits of E-Challan (Ease of payment, Transparency, Efficiency, Accountability) and Government Vision.",
                "full_text": "Benefits:\n- Ease of Payment: " + ", ".join(content.get('benefits', {}).get('ease_of_payment', [])) + "\n- Transparency: " + ", ".join(content.get('benefits', {}).get('transparency', [])) + "\n- Efficiency: " + ", ".join(content.get('benefits', {}).get('efficiency', [])) + "\n- Accountability: " + ", ".join(content.get('benefits', {}).get('accountability', [])) + f"\n\nVision: {content.get('vision', '')}",
                "jurisdiction_id": maharashtra.id,
            }
        }
    ]

    for s_data in sections_to_seed:
        # Generate embedding if model is loaded
        if EMBEDDING_MODEL:
            try:
                content_to_embed = f"{s_data['defaults']['act_name']} Section {s_data['defaults']['section_number']}: {s_data['defaults']['explanation_text']} {s_data['defaults']['full_text']}"
                embedding = EMBEDDING_MODEL.encode(content_to_embed).tolist()
                s_data["defaults"]["embedding"] = embedding
            except Exception as ex:
                logger.warning(f"Failed to generate embedding for {s_data['page_index']}: {ex}")

        instance = await get_or_create(session, LegalSection, page_index=s_data["page_index"], defaults=s_data["defaults"])
        
        # Populate TSVECTOR
        if not instance.keywords:
            if session.bind.dialect.name == 'sqlite':
                instance.keywords = instance.full_text
            else:
                instance.keywords = func.to_tsvector('english', instance.full_text)
            session.add(instance)
            await session.commit()

    logger.info(f"Successfully seeded {len(sections_to_seed)} Maharashtra Traffic E-Challan sections.")
