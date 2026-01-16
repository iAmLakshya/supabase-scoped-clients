"""Supabase Scoped Clients - User-scoped Supabase clients with self-signed JWTs."""

__version__ = "0.1.0"

from .core import (
    ClientError,
    Config,
    ConfigurationError,
    SupabaseScopedClientsError,
    TokenError,
    load_config,
)
from .factories import get_async_client, get_client

__all__ = [
    "Config",
    "load_config",
    "get_client",
    "get_async_client",
    "SupabaseScopedClientsError",
    "ConfigurationError",
    "TokenError",
    "ClientError",
]
