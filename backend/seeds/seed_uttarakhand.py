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

async def seed_uttarakhand(session: AsyncSession):
    # Get Uttarakhand jurisdiction
    stmt = select(Jurisdiction).where(Jurisdiction.code == "IN-UK")
    result = await session.execute(stmt)
    uttarakhand = result.scalars().first()
    
    if not uttarakhand:
        logger.error("Uttarakhand jurisdiction (IN-UK) not found. Run seed_jurisdictions first.")
        return

    # Load dataset u.json
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'data', 'u.json')
    if not os.path.exists(data_path):
        logger.error(f"Dataset file not found at {data_path}")
        return

    with open(data_path, 'r') as f:
        dataset = json.load(f)

    documents = dataset.get("documents", [])
    notifications = dataset.get("notifications", [])

    logger.info(f"Loaded {len(documents)} documents and {len(notifications)} notifications for Uttarakhand. Seeding...")

    count = 0

    # Seed documents
    for doc in documents:
        doc_id = doc.get("doc_id")
        title = doc.get("title", "")
        notif_no = doc.get("notification_no", "")
        dept = doc.get("department", "")
        signed_by = doc.get("signed_by", "")
        purpose = doc.get("purpose", "")
        legal_authority = doc.get("legal_authority", "")
        amendments = doc.get("amendments", [])
        rules = doc.get("rules", {})
        exemptions = doc.get("exemptions", [])
        
        # Build full text
        full_text_parts = [
            f"Title: {title}",
            f"Notification No: {notif_no}",
            f"Department: {dept}",
            f"Signed by: {signed_by}",
            f"Legal Authority: {legal_authority}",
            f"Purpose: {purpose}"
        ]
        
        if doc.get("amends"):
            full_text_parts.append(f"Amends: {doc.get('amends')}")
        if doc.get("commencement"):
            full_text_parts.append(f"Commencement: {doc.get('commencement')}")

        if amendments:
            full_text_parts.append("\nAmendments:")
            for amend in amendments:
                serial = amend.get("serial", "")
                change_type = amend.get("change_type", "")
                old_designation = amend.get("old_designation", "")
                new_designation = amend.get("new_designation", "")
                details = amend.get("uniform_details", {}) or amend.get("summer_uniform_new", []) or amend.get("winter_uniform_new", [])
                amend_str = f"- [{serial}] Type: {change_type} | Old: {old_designation} | New: {new_designation}"
                if details:
                    amend_str += f" | Details: {json.dumps(details)}"
                full_text_parts.append(amend_str)

        if rules:
            full_text_parts.append("\nRules:")
            for r_key, r_val in rules.items():
                if isinstance(r_val, dict):
                    full_text_parts.append(f"- {r_key}: {json.dumps(r_val)}")
                else:
                    full_text_parts.append(f"- {r_key}: {r_val}")

        if exemptions:
            full_text_parts.append("\nExemptions:")
            for ex in exemptions:
                full_text_parts.append(f"- {json.dumps(ex)}")

        full_text = "\n".join(full_text_parts)
        page_index = f"uk-doc:{doc_id}"
        
        defaults = {
            "act_name": title,
            "section_number": f"UK-DOC-{doc_id}",
            "chapter": "Documents",
            "explanation_text": f"Notification No: {notif_no}\nDepartment: {dept}\nPurpose: {purpose}",
            "full_text": full_text,
            "jurisdiction_id": uttarakhand.id,
        }

        # Generate embedding if model is loaded
        if EMBEDDING_MODEL:
            try:
                content_to_embed = f"Uttarakhand Document {title}: {purpose}. {full_text[:500]}"
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

    # Seed notifications
    for notif in notifications:
        notif_id = notif.get("notification_id")
        title = notif.get("title", "")
        notif_no = notif.get("notification_no", "")
        dept = notif.get("department", "")
        authority = notif.get("issuing_authority", "")
        summary = notif.get("summary", "")
        subject = notif.get("subject_category", "")
        amends_list = notif.get("amendments", [])
        rules_list = notif.get("key_rule_changes", [])
        definitions = notif.get("definitions_added_or_amended", []) or notif.get("definitions", {})

        full_text_parts = [
            f"Title: {title}",
            f"Notification No: {notif_no}",
            f"Department: {dept}",
            f"Issuing Authority: {authority}",
            f"Subject: {subject}",
            f"Summary: {summary}"
        ]

        if amends_list:
            full_text_parts.append("\nAmendments:")
            for a in amends_list:
                full_text_parts.append(f"- Rule/Post: {a.get('rule') or a.get('post')} | Existing: {a.get('existing_condition') or a.get('existing')} | Substituted: {a.get('substituted_condition') or a.get('substituted') or a.get('change')}")

        if rules_list:
            full_text_parts.append("\nKey Rule Changes:")
            for r in rules_list:
                full_text_parts.append(f"- Rule: {r.get('rule') or r.get('rule_no')} | Title/Change: {r.get('title') or r.get('change')} | Content: {r.get('content')}")

        if definitions:
            full_text_parts.append(f"\nDefinitions: {json.dumps(definitions)}")

        full_text = "\n".join(full_text_parts)
        page_index = f"uk-notif:{notif_id}"

        defaults = {
            "act_name": title,
            "section_number": f"UK-NOTIF-{notif_id}",
            "chapter": dept or "Notifications",
            "explanation_text": f"Notification No: {notif_no}\nSummary: {summary}",
            "full_text": full_text,
            "jurisdiction_id": uttarakhand.id,
        }

        # Generate embedding if model is loaded
        if EMBEDDING_MODEL:
            try:
                content_to_embed = f"Uttarakhand Notification {title}: {summary}. {full_text[:500]}"
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

    logger.info(f"Successfully seeded {count} Uttarakhand sections.")
