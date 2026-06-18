"""
Database package for the Document Copilot backend.

Exports the async engine, session factory, and ``get_db`` dependency
so downstream code can import from a single, stable location.
"""

from app.database.db import AsyncSessionLocal, engine, get_db

__all__ = [
    "engine",
    "AsyncSessionLocal",
    "get_db",
]
