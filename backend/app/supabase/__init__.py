"""
Supabase package for the Document Copilot backend.

Exports FastAPI dependencies and the underlying factory functions so
other modules can import from a single stable location::

    from app.supabase import get_supabase_client, get_supabase_admin
"""

from app.supabase.client import (
    get_supabase_admin,
    get_supabase_client,
)

__all__ = [
    "get_supabase_client",
    "get_supabase_admin",
]
