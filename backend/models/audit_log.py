import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.models.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False) # e.g., 'UPDATE_FINE', 'CREATE_USER'
    
    entity_type: Mapped[str] = mapped_column(String(100)) # e.g., 'fine_schedules', 'users'
    entity_id: Mapped[str] = mapped_column(String(255))
    
    metadata_log: Mapped[dict | None] = mapped_column(JSONB) # Store previous/new values
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User")
