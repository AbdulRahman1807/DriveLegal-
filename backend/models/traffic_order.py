import uuid
from datetime import date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.models.base import Base

class TrafficOrder(Base):
    __tablename__ = "traffic_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jurisdictions.id"), nullable=False)
    
    order_type: Mapped[str] = mapped_column(String(100), index=True) # e.g., 'SPEED_LIMIT', 'ONE_WAY', 'PARKING_RESTRICTION'
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    
    conditions: Mapped[dict | None] = mapped_column(JSONB) # e.g., {"vehicle_types": ["HMV"], "time_from": "08:00", "time_to": "20:00"}
    
    # Relationships
    jurisdiction = relationship("Jurisdiction")
