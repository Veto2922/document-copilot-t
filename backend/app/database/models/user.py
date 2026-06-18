"""User database model."""

from datetime import datetime
from uuid import UUID
from typing import TYPE_CHECKING, List
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base

if TYPE_CHECKING:
    from app.database.models.thread import ChatThread


class User(Base):
    """
    Represents an authenticated user in the system.
    Renamed from 'profiles' to 'users'. Keyed by the Supabase auth.users.id.
    """
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    threads: Mapped[List["ChatThread"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
