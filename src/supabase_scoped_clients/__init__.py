"""Supabase Scoped Clients - Create user-scoped Supabase clients using self-signed JWTs."""

__version__ = "0.1.0"

from .async_factory import get_async_client
from .config import Config, load_config
from .exceptions import (
    ClientError,
    ConfigurationError,
    SupabaseScopedClientsError,
    TokenError,
)
from .factory import get_client
from .jwt import generate_token

__all__ = [
    "Config",
    "load_config",
    "generate_token",
    "get_client",
    "get_async_client",
    "SupabaseScopedClientsError",
    "ConfigurationError",
    "TokenError",
    "ClientError",
]
