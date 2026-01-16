"""Supabase Scoped Clients - Create user-scoped Supabase clients using self-signed JWTs."""

__version__ = "0.1.0"

from .config import Config, load_config
from .exceptions import (
    ClientError,
    ConfigurationError,
    SupabaseScopedClientsError,
    TokenError,
)

__all__ = [
    "Config",
    "load_config",
    "SupabaseScopedClientsError",
    "ConfigurationError",
    "TokenError",
    "ClientError",
]
