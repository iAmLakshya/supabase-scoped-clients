"""Infrastructure modules for supabase_scoped_clients.

This subpackage contains cross-cutting infrastructure concerns:
- TokenRefreshProxy: automatic token refresh via proxy pattern
- Protocol definitions for token managers
"""

from .proxy import (
    AsyncTokenManager,
    TokenManager,
    TokenRefreshProxy,
    create_proxy,
)

__all__ = [
    "TokenRefreshProxy",
    "create_proxy",
    "TokenManager",
    "AsyncTokenManager",
]
