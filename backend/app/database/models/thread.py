"""Chat thread database model."""

from datetime import datetime
from uuid import UUID
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base

if TYPE_CHECKING:
    from app.database.models.user import User
    from app.database.models.message import ChatMessage


class ChatThread(Base):
    """
    Represents a chat conversation thread containing multiple messages.
    """
    __tablename__ = "chat_threads"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="threads")
    messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )
