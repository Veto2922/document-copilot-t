"""
Supabase client factory for the Document Copilot backend.

Two clients are available:

* **anon client** — uses the ``SUPABASE_ANON_KEY``.  Safe to call with a
  user's JWT forwarded; Supabase RLS policies still apply.
* **service-role client** — uses ``SUPABASE_SERVICE_ROLE_KEY``.  Bypasses
  RLS entirely.  Use **only** in server-side admin operations (e.g., ingest
  pipelines, webhook handlers) and **never** expose to the browser.

Both clients are module-level singletons initialised once on first access
(lazy) so that tests can swap ``app.config.settings`` before the clients
are created.

FastAPI dependencies:
    - ``get_supabase_client``  → anon client
    - ``get_supabase_admin``   → service-role client
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from supabase import AsyncClient, acreate_client

from app.config import settings

if TYPE_CHECKING:
    pass  # keep imports lightweight for type checking

# ---------------------------------------------------------------------------
# Module-level singletons (initialised on first access)
# ---------------------------------------------------------------------------
_anon_client: AsyncClient | None = None
_admin_client: AsyncClient | None = None


def _get_anon_client() -> AsyncClient:
    """
    Return the anon (public) Supabase client, creating it on first call.

    The client is thread-safe and re-entrant; it can be shared across
    concurrent requests.

    Returns:
        A ``Client`` configured with the anon key and project URL.
    """
    global _anon_client  # noqa: PLW0603
    if _anon_client is None:
        _anon_client = acreate_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_ANON_KEY,
        )
    return _anon_client


def _get_admin_client() -> AsyncClient:
    """
    Return the service-role Supabase client, creating it on first call.

    This client bypasses Row-Level Security.  Keep it strictly server-side.

    Returns:
        A ``Client`` configured with the service-role key and project URL.
    """
    global _admin_client  # noqa: PLW0603
    if _admin_client is None:
        _admin_client = acreate_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _admin_client


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------
def get_supabase_client() -> AsyncClient:
    """
    FastAPI dependency that provides the anon Supabase client.

    Suitable for operations that should respect RLS policies.
    Forward the user's JWT via ``client.auth.set_session(access_token, ...)``
    if you need to act on behalf of a specific user.

    Returns:
        The shared anon ``Client`` instance.

    Example::

        @router.get("/profile")
        async def get_profile(client: Client = Depends(get_supabase_client)):
            return client.table("profiles").select("*").execute()
    """
    return _get_anon_client()


def get_supabase_admin() -> AsyncClient:
    """
    FastAPI dependency that provides the service-role Supabase client.

    Bypasses Row-Level Security — use only for internal/admin operations
    (e.g., document ingestion, user bootstrapping, background jobs).

    Returns:
        The shared service-role ``Client`` instance.

    Example::

        @router.post("/ingest")
        async def ingest_doc(admin: Client = Depends(get_supabase_admin)):
            admin.table("source_documents").insert({...}).execute()
    """
    return _get_admin_client()
