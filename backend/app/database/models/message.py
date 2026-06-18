"""Chat message database model."""

from datetime import datetime
from uuid import UUID
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import String, ForeignKey, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base

if TYPE_CHECKING:
    from app.database.models.thread import ChatThread
    from app.database.models.citation import MessageCitation


class ChatMessage(Base):
    """
    Represents an individual message (user or assistant) within a chat thread.
    """
    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    thread_id: Mapped[UUID] = mapped_column(
        ForeignKey("chat_threads.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user', 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    thread: Mapped["ChatThread"] = relationship(back_populates="messages")
    citations: Mapped[List["MessageCitation"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )
