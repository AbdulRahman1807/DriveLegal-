import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.models.base import Base

class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    violation_code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False) # e.g., "SPEEDING"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True) # e.g., 'DOCUMENT', 'SAFETY', 'PARKING'
    keywords: Mapped[str] = mapped_column(Text) # Comma-separated for simple search
    aliases: Mapped[list[str]] = mapped_column(JSONB, default=list) # e.g., ["overspeeding", "driving fast"]
