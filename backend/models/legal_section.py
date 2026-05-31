import uuid
from datetime import date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from pgvector.sqlalchemy import Vector
from backend.models.base import Base

class LegalSection(Base):
    __tablename__ = "legal_sections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    act_name: Mapped[str] = mapped_column(String(255), nullable=False) # e.g., "Motor Vehicles (Amendment) Act, 2019"
    section_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    chapter: Mapped[str | None] = mapped_column(String(100))
    clause: Mapped[str | None] = mapped_column(String(50))
    explanation_text: Mapped[str | None] = mapped_column(Text)
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    jurisdiction_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("jurisdictions.id"))
    effective_date: Mapped[date | None] = mapped_column(Date)
    gazette_reference: Mapped[str | None] = mapped_column(String(255))
    source_url: Mapped[str | None] = mapped_column(String(512))
    
    # PageIndex structured reference (act:chapter:section:clause)
    page_index: Mapped[str] = mapped_column(String(255), index=True)
    
    # Full text search vector (will be populated via triggers/events)
    keywords: Mapped[str | None] = mapped_column(TSVECTOR)
    
    # Dense vector embedding (384 dimensions for all-MiniLM-L6-v2)
    embedding = mapped_column(Vector(384))
    
    # Relationships
    jurisdiction = relationship("Jurisdiction")

# Create GIN index for full-text search
Index('ix_legal_sections_keywords_gin', LegalSection.keywords, postgresql_using='gin')

# Create HNSW index for fast vector search
Index('ix_legal_sections_embedding_hnsw', LegalSection.embedding,
      postgresql_using='hnsw',
      postgresql_with={'m': 16, 'ef_construction': 64},
      postgresql_ops={'embedding': 'vector_cosine_ops'})
