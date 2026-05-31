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

async def seed_sikkim(session: AsyncSession):
    # Get Sikkim jurisdiction
    stmt = select(Jurisdiction).where(Jurisdiction.code == "IN-SK")
    result = await session.execute(stmt)
    sikkim = result.scalars().first()
    
    if not sikkim:
        logger.error("Sikkim jurisdiction (IN-SK) not found. Run seed_jurisdictions first.")
        return

    # Load dataset sikkim.json
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'data', 'sikkim.json')
    if not os.path.exists(data_path):
        logger.error(f"Dataset file not found at {data_path}")
        return

    with open(data_path, 'r') as f:
        dataset = json.load(f)

    dept_data = dataset.get("transport_department", {})
    overview = dept_data.get("motor_vehicle_division", {}).get("overview", "")
    functions = dept_data.get("motor_vehicle_division", {}).get("business_functions", [])
    permits = dept_data.get("permits", {})
    dl_info = dept_data.get("driving_license", {})
    penalties = dept_data.get("penalties", {})
    pollution = dept_data.get("pollution_control", {})
    facilities = dept_data.get("facilities", {})
    safety = dept_data.get("road_safety", {})
    odd_even = dept_data.get("odd_even_notification", {})

    logger.info("Seeding Sikkim Transport Department data...")
    count = 0

    # 1. Seed Overview
    page_index = "sk-overview"
    full_text = f"Sikkim Motor Vehicle Division Overview:\n{overview}\n\nFunctions:\n" + "\n".join([f"- {f}" for f in functions])
    defaults = {
        "act_name": "Sikkim Motor Vehicle Rules & Acts Overview",
        "section_number": "SK-OVERVIEW",
        "chapter": "Overview",
        "explanation_text": "Overview and core functions of the Sikkim Transport Department.",
        "full_text": full_text,
        "jurisdiction_id": sikkim.id,
    }
    if EMBEDDING_MODEL:
        try:
            embedding = EMBEDDING_MODEL.encode(full_text[:500]).tolist()
            defaults["embedding"] = embedding
        except Exception as e:
            logger.warning(f"Failed to generate embedding for {page_index}: {e}")

    instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
    if not instance.keywords:
        instance.keywords = instance.full_text
        session.add(instance)
        await session.commit()
    count += 1

    # 2. Seed Permits
    for permit_name, permit_val in permits.items():
        page_index = f"sk-permit:{permit_name}"
        series = permit_val.get("series", "")
        docs = permit_val.get("required_documents", [])
        note = permit_val.get("note", "")
        app_to = permit_val.get("applicable_to", "")
        
        full_text = f"Sikkim Permit: {permit_name.replace('_', ' ').title()}\nSeries: {series}\n"
        if note:
            full_text += f"Note: {note}\n"
        if app_to:
            full_text += f"Applicable To: {app_to}\n"
        full_text += "Required Documents:\n" + "\n".join([f"- {d}" for d in docs])
        
        defaults = {
            "act_name": "Sikkim Motor Vehicle Rules, 1991",
            "section_number": f"SK-PERMIT-{series}",
            "chapter": "Permits",
            "explanation_text": f"Requirements for obtaining {permit_name.replace('_', ' ')} in Sikkim.",
            "full_text": full_text,
            "jurisdiction_id": sikkim.id,
        }
        if EMBEDDING_MODEL:
            try:
                embedding = EMBEDDING_MODEL.encode(full_text[:500]).tolist()
                defaults["embedding"] = embedding
            except Exception as e:
                logger.warning(f"Failed to generate embedding for {page_index}: {e}")

        instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
        if not instance.keywords:
            instance.keywords = instance.full_text
            session.add(instance)
            await session.commit()
        count += 1

    # 3. Seed Driving License
    page_index = "sk-dl"
    dl_categories = dl_info.get("categories", [])
    dl_text = f"Sikkim Driving License Legal Basis: {dl_info.get('legal_basis')}\nSoftware: {dl_info.get('software')}\nIssuing Offices: {dl_info.get('issuing_offices')}\nTypes: {', '.join(dl_info.get('license_types_issued', []))}\n\nCategories:\n"
    for cat in dl_categories:
        dl_text += f"- Category: {cat.get('category')} (Age limit: {cat.get('age_limit')}) | Criteria: {cat.get('criteria')}\n"
        
    defaults = {
        "act_name": "Sikkim Motor Vehicle Rules, 1991",
        "section_number": "SK-DL-RULES",
        "chapter": "Driving License",
        "explanation_text": "Rules, age limits, and requirements for obtaining a driving license in Sikkim.",
        "full_text": dl_text,
        "jurisdiction_id": sikkim.id,
    }
    if EMBEDDING_MODEL:
        try:
            embedding = EMBEDDING_MODEL.encode(dl_text[:500]).tolist()
            defaults["embedding"] = embedding
        except Exception as e:
            logger.warning(f"Failed to generate embedding for {page_index}: {e}")

    instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
    if not instance.keywords:
        instance.keywords = instance.full_text
        session.add(instance)
        await session.commit()
    count += 1

    # 4. Seed Fines/Penalties
    page_index = "sk-penalties"
    fines = penalties.get("fines", [])
    penalties_text = f"Sikkim Traffic Fines (Legal Basis: {penalties.get('legal_basis')}, Notification: {penalties.get('notification')}):\n"
    for item in fines:
        sec = item.get("section")
        first = item.get("1st_offence")
        second = item.get("2nd_offence")
        third = item.get("3rd_offence")
        types = item.get("vehicle_types", [])
        base = item.get("base_fine")
        weight_slabs = item.get("weight_slabs", [])
        
        penalties_text += f"\nSection: {sec}\n"
        if first is not None:
            penalties_text += f"  1st Offence: Rs. {first} | 2nd: {second} | 3rd: {third}\n"
        if base is not None:
            penalties_text += f"  Base Fine: Rs. {base}\n"
        if types:
            for t in types:
                penalties_text += f"  - {t.get('type')}: 1st: {t.get('1st_offence')}, 2nd: {t.get('2nd_offence')}, 3rd: {t.get('3rd_offence')}\n"
        if weight_slabs:
            for slab in weight_slabs:
                penalties_text += f"  - Overweight slab {slab.get('excess_weight_kg')} kg: 1st: {slab.get('1st_offence')}, 2nd: {slab.get('2nd_offence')}, 3rd: {slab.get('3rd_offence')}\n"

    defaults = {
        "act_name": "Sikkim Motor Vehicles Act / Fines",
        "section_number": "SK-FINES-TABLE",
        "chapter": "Penalties",
        "explanation_text": f"Sikkim Traffic Offence Penalties Table.",
        "full_text": penalties_text,
        "jurisdiction_id": sikkim.id,
    }
    if EMBEDDING_MODEL:
        try:
            embedding = EMBEDDING_MODEL.encode(penalties_text[:500]).tolist()
            defaults["embedding"] = embedding
        except Exception as e:
            logger.warning(f"Failed to generate embedding for {page_index}: {e}")

    instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
    if not instance.keywords:
        instance.keywords = instance.full_text
        session.add(instance)
        await session.commit()
    count += 1

    # 5. Seed Odd-Even and Pollution
    page_index = "sk-odd-even"
    ex_timings = odd_even.get("restriction_timings", [])
    ex_rules = odd_even.get("rules", {})
    ex_list = odd_even.get("exemptions_from_restriction", [])
    em_ex = odd_even.get("emergency_exemptions", [])
    
    odd_even_text = f"Sikkim Odd-Even Rule Notification {odd_even.get('notification_no')} (Date: {odd_even.get('date')}):\n"
    odd_even_text += f"Effective from: {odd_even.get('effective_from')}\n"
    odd_even_text += f"Legal Authority: {odd_even.get('legal_authority')}\n"
    odd_even_text += f"Applicable Area: {odd_even.get('applicable_area')}\n"
    odd_even_text += "\nRestriction Timings:\n"
    for t in ex_timings:
        odd_even_text += f"- {t.get('period')}: {t.get('from')} to {t.get('to')}\n"
    odd_even_text += f"\nRules:\n- Odd Dates: {ex_rules.get('odd_dates')}\n- Even Dates: {ex_rules.get('even_dates')}\n"
    odd_even_text += "\nGeneral Exemptions: " + ", ".join(ex_list) + "\n"
    odd_even_text += "\nEmergency Exemptions:\n"
    for em in em_ex:
        odd_even_text += f"- {em.get('category')}: {em.get('exemption')}\n"
    odd_even_text += f"Penalty: {odd_even.get('penalty_for_violation')}\n"
    
    defaults = {
        "act_name": "Sikkim Motor Vehicles Act, 1988 (Section 115)",
        "section_number": f"SK-ODD-EVEN-{odd_even.get('notification_no')}",
        "chapter": "Odd-Even Notification",
        "explanation_text": "Rules, timings, and exemptions for the Odd-Even traffic scheme in Gangtok Municipal Area.",
        "full_text": odd_even_text,
        "jurisdiction_id": sikkim.id,
    }
    if EMBEDDING_MODEL:
        try:
            embedding = EMBEDDING_MODEL.encode(odd_even_text[:500]).tolist()
            defaults["embedding"] = embedding
        except Exception as e:
            logger.warning(f"Failed to generate embedding for {page_index}: {e}")

    instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
    if not instance.keywords:
        instance.keywords = instance.full_text
        session.add(instance)
        await session.commit()
    count += 1

    # 6. Pollution Control and Road Safety
    page_index = "sk-safety-pollution"
    safety_text = f"Sikkim Road Safety Council & Committee:\nMonitoring Body: {safety.get('monitoring_body')}\nNodal Dept: {safety.get('nodal_department')}\n"
    for comm in safety.get("committees", []):
        safety_text += f"- Committee: {comm.get('name')} | Head: {comm.get('head')} | Notification: {comm.get('notification')}\n"
    safety_text += f"Sikkim Road Safety Fund (2015-16): {safety.get('road_safety_fund', {}).get('amount_INR_lakhs')} Lakhs\nPillars: {', '.join(safety.get('five_pillars', []))}\nActions Taken:\n" + "\n".join([f"- {act}" for act in safety.get("actions_taken", [])])
    
    pollution_text = f"\n\nSikkim Pollution Control:\nOverview: {pollution.get('policy')}\nSmoke Testing Units: {pollution.get('smoke_testing_units')} at {', '.join(pollution.get('locations', []))}"
    
    full_text = safety_text + pollution_text
    defaults = {
        "act_name": "Sikkim Road Safety Policy & Pollution Control",
        "section_number": "SK-SAFETY-POLLUTION",
        "chapter": "Safety & Pollution",
        "explanation_text": "Sikkim Road Safety Council actions and environmental pollution control policies.",
        "full_text": full_text,
        "jurisdiction_id": sikkim.id,
    }
    if EMBEDDING_MODEL:
        try:
            embedding = EMBEDDING_MODEL.encode(full_text[:500]).tolist()
            defaults["embedding"] = embedding
        except Exception as e:
            logger.warning(f"Failed to generate embedding for {page_index}: {e}")

    instance = await get_or_create(session, LegalSection, page_index=page_index, defaults=defaults)
    if not instance.keywords:
        instance.keywords = instance.full_text
        session.add(instance)
        await session.commit()
    count += 1

    logger.info(f"Successfully seeded {count} Sikkim sections.")
