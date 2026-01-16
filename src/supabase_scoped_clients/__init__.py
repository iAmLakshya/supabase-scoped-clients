"""Supabase Scoped Clients - Create user-scoped Supabase clients using self-signed JWTs."""

__version__ = "0.1.0"

from .config import Config
from .exceptions import (
    ClientError,
    ConfigurationError,
    SupabaseScopedClientsError,
    TokenError,
)

__all__ = [
    "Config",
    "SupabaseScopedClientsError",
    "ConfigurationError",
    "TokenError",
    "ClientError",
]
