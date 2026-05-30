import asyncio
from sqlalchemy import select
from sqlalchemy.schema import CreateTable
from backend.models.user import User
from backend.models.jurisdiction import Jurisdiction
from backend.models.violation import Violation
from backend.models.legal_section import LegalSection
from backend.models.fine_schedule import FineSchedule
from backend.models.traffic_order import TrafficOrder
from backend.models.chat_models import ChatSession, ChatMessage
from backend.models.audit_log import AuditLog
from backend.database import engine

print(CreateTable(User.__table__).compile(engine))
print(CreateTable(Jurisdiction.__table__).compile(engine))
print(CreateTable(LegalSection.__table__).compile(engine))

