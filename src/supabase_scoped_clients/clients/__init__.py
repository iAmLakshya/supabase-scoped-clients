"""Client wrappers for supabase_scoped_clients.

This subpackage contains the client wrapper classes that provide
automatic token refresh around Supabase clients:
- ScopedClient: sync client wrapper
- AsyncScopedClient: async client wrapper
"""

from .async_client import AsyncScopedClient
from .sync import ScopedClient

__all__ = [
    "ScopedClient",
    "AsyncScopedClient",
]
