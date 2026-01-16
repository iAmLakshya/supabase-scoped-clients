"""Factory functions for supabase_scoped_clients.

This subpackage contains factory functions that create one-shot
user-scoped Supabase clients (without automatic token refresh):
- get_client: sync factory function
- get_async_client: async factory function
"""

from .async_factory import get_async_client
from .sync import get_client

__all__ = [
    "get_client",
    "get_async_client",
]
