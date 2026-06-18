"""
Main entrypoint for the Document Copilot FastAPI backend.

Startup sequence
----------------
1. Settings are validated on import (fail-fast on missing env vars).
2. The ``lifespan`` context manager runs once: it verifies the DB connection
   so we surface connection errors at boot, not mid-request.
3. Routers are registered after lifespan so the app never serves traffic
   before connectivity is confirmed.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: startup / shutdown hooks
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application startup and shutdown.

    On startup:
    - Pings the Postgres database to surface config / connectivity errors
      early, before the first request arrives.

    On shutdown:
    - Disposes the SQLAlchemy connection pool cleanly.
    """
    # --- Startup ---
    logger.info("startup.begin", supabase_url=settings.SUPABASE_URL)

    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("startup.db_ok")

    yield  # application runs here

    # --- Shutdown ---
    await engine.dispose()
    logger.info("shutdown.complete")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Document Copilot Backend",
    description="Backend API for the Document Copilot research assistant.",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS using origins validated by settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health", tags=["ops"])
async def health_check() -> dict[str, str]:
    """
    Return a shallow liveness signal.

    Does **not** re-probe the database on every call — the startup
    lifespan already verified connectivity.  Use this endpoint only to
    confirm the process is alive and settings loaded correctly.

    Returns:
        A dictionary with API status and non-secret configuration details.
    """
    return {
        "status": "healthy",
        "supabase_url": settings.SUPABASE_URL,
        "gemini_embedding_model": settings.GEMINI_EMBEDDING_MODEL,
        "openai_embedding_model": settings.OPENAI_EMBEDDING_MODEL,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
