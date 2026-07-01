"""
Database session management module.

Establishes the asynchronous SQLAlchemy connection to the Postgres database
and defines the FastAPI dependency for request-scoped database sessions.
"""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Create database engine for async connection using postgresql+psycopg dialect
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

# Async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding a new SQLAlchemy AsyncSession.

    Yields:
        An active AsyncSession instance.
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
