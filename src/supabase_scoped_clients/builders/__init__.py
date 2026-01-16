"""Builder classes for supabase_scoped_clients.

This subpackage contains fluent builder classes for configuring
and creating client instances:
- ScopedClientBuilder: sync builder with chainable API
- AsyncScopedClientBuilder: async builder with chainable API
"""

from .async_builder import AsyncScopedClientBuilder
from .sync import ScopedClientBuilder

__all__ = [
    "ScopedClientBuilder",
    "AsyncScopedClientBuilder",
]
