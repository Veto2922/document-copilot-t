"""Document chunk database model."""

from datetime import datetime
from uuid import UUID
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import (
    String, Integer, ForeignKey, DateTime, Text, Computed, Index, func
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.database.models.base import Base

if TYPE_CHECKING:
    from app.database.models.document import SourceDocument
    from app.database.models.citation import MessageCitation


class DocumentChunk(Base):
    """
    Represents a specific chunk/passage of text from a source document.
    Includes pgvector embedding and generated tsvector for full-text search.
    """
    __tablename__ = "document_chunks"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # TSVector for full text search (generated column)
    search_vector: Mapped[Optional[TSVECTOR]] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', content)", persisted=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    document: Mapped["SourceDocument"] = relationship(back_populates="chunks")
    citations: Mapped[List["MessageCitation"]] = relationship(
        back_populates="chunk", cascade="all, delete-orphan"
    )

    # Table arguments for custom postgresql indexes
    __table_args__ = (
        Index("ix_document_chunks_search_vector", "search_vector", postgresql_using="gin"),
        Index(
            "ix_document_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
    )
