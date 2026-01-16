"""Supabase Scoped Clients - User-scoped Supabase clients with self-signed JWTs."""

__version__ = "0.1.0"

from .builders import AsyncScopedClientBuilder, ScopedClientBuilder
from .clients import AsyncScopedClient, ScopedClient
from .core import (
    ClientError,
    Config,
    ConfigurationError,
    SupabaseScopedClientsError,
    TokenError,
    generate_token,
    load_config,
)
from .factories import get_async_client, get_client

__all__ = [
    "Config",
    "load_config",
    "generate_token",
    "get_client",
    "get_async_client",
    "ScopedClient",
    "AsyncScopedClient",
    "ScopedClientBuilder",
    "AsyncScopedClientBuilder",
    "SupabaseScopedClientsError",
    "ConfigurationError",
    "TokenError",
    "ClientError",
]
