import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.models.base import Base

class Jurisdiction(Base):
    __tablename__ = "jurisdictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False) # 'NATIONAL', 'STATE', 'DISTRICT', 'CITY'
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("jurisdictions.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True) # e.g., 'IN', 'IN-KA', 'BLR'
    coordinates_bounds: Mapped[dict | None] = mapped_column(JSONB, nullable=True) # For GPS resolution
    active: Mapped[bool] = mapped_column(default=True)
    
    # Relationships
    parent = relationship("Jurisdiction", remote_side=[id], backref="children")
