import uuid
from datetime import date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from backend.models.base import Base

class FineSchedule(Base):
    __tablename__ = "fine_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    violation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("violations.id"), nullable=False)
    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jurisdictions.id"), nullable=False)
    legal_section_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("legal_sections.id"), nullable=False)
    
    vehicle_category: Mapped[str] = mapped_column(String(100), default="ALL") # e.g., 'ALL', '2W', '4W', 'HMV'
    
    first_offence_fine: Mapped[float] = mapped_column(Float, nullable=False)
    repeat_offence_fine: Mapped[float | None] = mapped_column(Float)
    
    imprisonment_months: Mapped[int | None] = mapped_column(Integer, default=0)
    license_suspension_months: Mapped[int | None] = mapped_column(Integer, default=0)
    
    compoundable: Mapped[bool] = mapped_column(Boolean, default=True)
    surcharge_percent: Mapped[float] = mapped_column(Float, default=0.0)
    
    effective_date: Mapped[date | None] = mapped_column(Date)
    
    # Relationships
    violation = relationship("Violation")
    jurisdiction = relationship("Jurisdiction")
    legal_section = relationship("LegalSection")
