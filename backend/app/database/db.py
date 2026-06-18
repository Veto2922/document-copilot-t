"""
Database session management for the Document Copilot backend.
Defines the SQLAlchemy engine, session maker, and dependency injection helpers.
"""

from typing import Generator

# from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings

# Use settings.DATABASE_URL for connection.
# SQLAlchemy 2.0 resolves 'postgresql://' to use psycopg (v3) when installed.
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Create session factory
SessionLocal = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[AsyncSession, None, None]:
    """
    FastAPI dependency that provides a thread-safe database session.
    Closes the session automatically after the request lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
