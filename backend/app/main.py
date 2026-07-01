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
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import contextlib
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database.session import engine
from app.api.chat import router as chat_router

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown lifespan events.
    Verifies database connection on startup before accepting requests.
    """
    logger.info("Initializing application lifespan...")
    try:
        # Run a simple query to verify connection
        async with engine.begin() as conn:
            logger.info("Verifying database connection...")
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified successfully.")
    except Exception as exc:
        logger.critical("Database connection verification failed on startup!", error=str(exc))
        raise exc
    
    yield
    
    logger.info("Disposing database connection pool...")
    await engine.dispose()
    logger.info("Application lifespan shutdown completed.")


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


from fastapi import Depends
from app.auth.dependencies import get_current_user, CurrentUser

# Register Chat Router
app.include_router(chat_router)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/api/test-auth", tags=["auth"])
async def test_auth(user: CurrentUser = Depends(get_current_user)) -> dict[str, str]:
    """
    Test endpoint to verify that a client's Supabase JWT token is parsed
    and verified correctly by the backend auth dependency.
    """
    return {
        "status": "authenticated",
        "user_id": str(user.id),
        "email": user.email,
    }


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
