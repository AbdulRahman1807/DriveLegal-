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

async def seed_drivelegal_db(session: AsyncSession):
    # Get jurisdictions
    stmt_in = select(Jurisdiction).where(Jurisdiction.code == "IN")
    result_in = await session.execute(stmt_in)
    india = result_in.scalars().first()

    stmt_tg = select(Jurisdiction).where(Jurisdiction.code == "IN-TG")
    result_tg = await session.execute(stmt_tg)
    telangana = result_tg.scalars().first()

    if not india or not telangana:
        logger.error("Jurisdictions IN or IN-TG not found. Run seed_jurisdictions first.")
        return

    # Load drivelegal.json
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'data', 'drivelegal.json')
    if not os.path.exists(data_path):
        logger.error(f"drivelegal.json not found at {data_path}")
        return

    with open(data_path, 'r') as f:
        data = json.load(f)

    db_data = data.get("drivelegal_database", {})
    acts = db_data.get("acts", {})
    
    count = 0

    # 1. Seed acts and rules under "IN"
    for act_key, act_val in acts.items():
        title = act_val.get("short_title", act_key.replace("_", " ").title())
        logger.info(f"Seeding act data: {title}...")

        # Create act overview section
        page_index = f"dl-act-overview:{act_key}"
        full_text = f"Act: {title}\n"
        for key in ["act_number", "enacted", "in_force", "signed_by", "extent", "last_amended", "objective", "status", "superseded_by", "effective_supersession", "parent_section", "parent_act", "notification"]:
            if key in act_val:
                full_text += f"{key.replace('_', ' ').title()}: {act_val[key]}\n"
        
        defaults = {
            "act_name": title,
            "section_number": "OVERVIEW",
            "chapter": "Overview",
            "explanation_text": act_val.get("objective", f"Overview of {title}"),
            "full_text": full_text,
            "jurisdiction_id": india.id,
        }
        if EMBEDDING_MODEL:
            try:
                defaults["embedding"] = EMBEDDING_MODEL.encode(full_text[:500]).tolist()
            except Exception as e:
                logger.warning(f"Failed embedding for {page_index}: {e}")

        instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
        if not instance.keywords:
            instance.keywords = instance.full_text
            session.add(instance)
            await session.commit()
        count += 1

        # Seed chapters if any
        if "chapters" in act_val:
            for ch in act_val["chapters"]:
                ch_no = ch.get("chapter", "")
                ch_title = ch.get("title", "")
                ch_sec = ch.get("sections", "")
                ch_desc = ch.get("description", "")
                page_index = f"dl-act-chapter:{act_key}:{ch_no}"
                full_text = f"Act: {title}\nChapter {ch_no}: {ch_title}\nSections: {ch_sec}\nDescription: {ch_desc}"
                
                defaults = {
                    "act_name": title,
                    "section_number": f"CH-{ch_no}",
                    "chapter": ch_title,
                    "explanation_text": ch_desc,
                    "full_text": full_text,
                    "jurisdiction_id": india.id,
                }
                if EMBEDDING_MODEL:
                    try:
                        defaults["embedding"] = EMBEDDING_MODEL.encode(full_text[:500]).tolist()
                    except Exception as e:
                        logger.warning(f"Failed embedding for {page_index}: {e}")

                instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
                if not instance.keywords:
                    instance.keywords = instance.full_text
                    session.add(instance)
                    await session.commit()
                count += 1

        # Seed key sections or key rules or rules
        for item_key in ["key_sections", "key_rules", "rules"]:
            if item_key in act_val:
                for item in act_val[item_key]:
                    item_no = item.get("section") or item.get("rule")
                    item_title = item.get("title", "")
                    item_desc = item.get("description", "")
                    page_index = f"dl-act-item:{act_key}:{item_no}"
                    full_text = f"Act: {title}\nItem/Section/Rule {item_no}: {item_title}\nDescription: {item_desc}"
                    
                    defaults = {
                        "act_name": title,
                        "section_number": f"SEC-{item_no}",
                        "chapter": item_title,
                        "explanation_text": item_desc,
                        "full_text": full_text,
                        "jurisdiction_id": india.id,
                    }
                    if EMBEDDING_MODEL:
                        try:
                            defaults["embedding"] = EMBEDDING_MODEL.encode(full_text[:500]).tolist()
                        except Exception as e:
                            logger.warning(f"Failed embedding for {page_index}: {e}")

                    instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
                    if not instance.keywords:
                        instance.keywords = instance.full_text
                        session.add(instance)
                        await session.commit()
                    count += 1

        # Seed key provisions / exemptions if any
        for prov_key in ["key_provisions", "exemptions"]:
            if prov_key in act_val:
                for idx, prov in enumerate(act_val[prov_key]):
                    page_index = f"dl-act-prov:{act_key}:{idx}"
                    if isinstance(prov, str):
                        full_text = f"Act/Regulation: {title}\nProvision:\n{prov}"
                        exp_text = prov[:150]
                    else:
                        prov_title = prov.get("provision") or prov.get("category") or ""
                        prov_desc = prov.get("description") or ""
                        full_text = f"Act/Regulation: {title}\nProvision Category: {prov_title}\nDescription:\n{prov_desc}"
                        exp_text = f"{prov_title}: {prov_desc[:150]}"
                    
                    defaults = {
                        "act_name": title,
                        "section_number": f"PROV-{idx}",
                        "chapter": "Key Provisions",
                        "explanation_text": exp_text,
                        "full_text": full_text,
                        "jurisdiction_id": india.id,
                    }
                    if EMBEDDING_MODEL:
                        try:
                            defaults["embedding"] = EMBEDDING_MODEL.encode(full_text[:500]).tolist()
                        except Exception as e:
                            logger.warning(f"Failed embedding for {page_index}: {e}")

                    instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
                    if not instance.keywords:
                        instance.keywords = instance.full_text
                        session.add(instance)
                        await session.commit()
                    count += 1

        # Seed solatium scheme special details
        if act_key == "solatium_scheme_1989":
            for detail_key in ["original_compensation", "current_scheme_2022", "claim_procedure"]:
                if detail_key in act_val:
                    page_index = f"dl-act-solatium:{detail_key}"
                    full_text = f"Act/Scheme: {title}\nDetails of {detail_key.replace('_', ' ').title()}:\n{json.dumps(act_val[detail_key], indent=2)}"
                    defaults = {
                        "act_name": title,
                        "section_number": f"SOLAT-{detail_key.upper()}",
                        "chapter": detail_key.replace('_', ' ').title(),
                        "explanation_text": f"Compensation and claim procedures under {title}",
                        "full_text": full_text,
                        "jurisdiction_id": india.id,
                    }
                    if EMBEDDING_MODEL:
                        try:
                            defaults["embedding"] = EMBEDDING_MODEL.encode(full_text[:500]).tolist()
                        except Exception as e:
                            logger.warning(f"Failed embedding for {page_index}: {e}")

                    instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
                    if not instance.keywords:
                        instance.keywords = instance.full_text
                        session.add(instance)
                        await session.commit()
                    count += 1

    # 2. Seed state-specific provisions for Telangana
    tg_provs = db_data.get("telangana_provisions", {})
    if tg_provs:
        title = tg_provs.get("title", "Telangana Traffic Provisions")
        desc = tg_provs.get("description", "")
        # Overview
        page_index = "dl-tg-prov:overview"
        full_text = f"Telangana Specific Traffic Provisions Overview:\n{desc}\nState Transport Authority: {tg_provs.get('state_transport_authority')}"
        defaults = {
            "act_name": title,
            "section_number": "TG-OVERVIEW",
            "chapter": "Overview",
            "explanation_text": desc,
            "full_text": full_text,
            "jurisdiction_id": telangana.id,
        }
        if EMBEDDING_MODEL:
            try:
                defaults["embedding"] = EMBEDDING_MODEL.encode(full_text[:500]).tolist()
            except Exception as e:
                logger.warning(f"Failed embedding for {page_index}: {e}")
        instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
        if not instance.keywords:
            instance.keywords = instance.full_text
            session.add(instance)
            await session.commit()
        count += 1

        # Key provisions
        for idx, item in enumerate(tg_provs.get("key_state_specific_provisions", [])):
            prov_title = item.get("provision", "")
            details = item.get("details", "")
            referred = item.get("rules_referred", "")
            page_index = f"dl-tg-prov:item:{idx}"
            full_text = f"Telangana Provision: {prov_title}\nDetails: {details}\nRules Referred: {referred}"
            defaults = {
                "act_name": title,
                "section_number": f"TG-PROV-{idx}",
                "chapter": prov_title,
                "explanation_text": details[:150],
                "full_text": full_text,
                "jurisdiction_id": telangana.id,
            }
            if EMBEDDING_MODEL:
                try:
                    defaults["embedding"] = EMBEDDING_MODEL.encode(full_text[:500]).tolist()
                except Exception as e:
                    logger.warning(f"Failed embedding for {page_index}: {e}")
            instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
            if not instance.keywords:
                instance.keywords = instance.full_text
                session.add(instance)
                await session.commit()
            count += 1

    # 3. Seed other lookup metrics (speed limits, registration marks, categories, axle weight, no fault) under IN
    metrics_to_seed = {
        "speed_limits": "National Speed Limits",
        "vehicle_categories": "Vehicle Categories (CMVR)",
        "registration_marks": "State Registration Marks",
        "axle_weight_limits": "Axle Weight Limits",
        "no_fault_compensation": "No Fault Compensation",
        "penalties_table": "National Penalties Reference"
    }

    for key, name in metrics_to_seed.items():
        if key in db_data:
            page_index = f"dl-metric:{key}"
            full_text = f"Metric Resource: {name}\nDetails:\n{json.dumps(db_data[key], indent=2)}"
            defaults = {
                "act_name": "Motor Vehicles Act Reference Tables",
                "section_number": f"REF-{key.upper()}",
                "chapter": "Reference Schedules",
                "explanation_text": f"National reference tables for {name}",
                "full_text": full_text,
                "jurisdiction_id": india.id,
            }
            if EMBEDDING_MODEL:
                try:
                    defaults["embedding"] = EMBEDDING_MODEL.encode(full_text[:500]).tolist()
                except Exception as e:
                    logger.warning(f"Failed embedding for {page_index}: {e}")

            instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
            if not instance.keywords:
                instance.keywords = instance.full_text
                session.add(instance)
                await session.commit()
            count += 1

    # 4. Seed FAQs
    faqs = db_data.get("common_faqs", [])
    for idx, faq in enumerate(faqs):
        page_index = f"dl-faq:{idx}"
        q = faq.get("question", "")
        a = faq.get("answer", "")
        ref = faq.get("legal_reference", "")
        full_text = f"FAQ: {q}\nAnswer: {a}\nLegal Reference: {ref}"
        
        defaults = {
            "act_name": "Common Traffic FAQs",
            "section_number": f"FAQ-{idx}",
            "chapter": "Frequently Asked Questions",
            "explanation_text": q[:150],
            "full_text": full_text,
            "jurisdiction_id": india.id,
        }
        if EMBEDDING_MODEL:
            try:
                defaults["embedding"] = EMBEDDING_MODEL.encode(full_text[:500]).tolist()
            except Exception as e:
                logger.warning(f"Failed embedding for {page_index}: {e}")

        instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
        if not instance.keywords:
            instance.keywords = instance.full_text
            session.add(instance)
            await session.commit()
        count += 1

    logger.info(f"Successfully seeded {count} sections/FAQ records from drivelegal.json.")
