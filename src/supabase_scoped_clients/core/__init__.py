"""Core domain modules for supabase_scoped_clients.

This subpackage contains the fundamental domain logic:
- Configuration loading and validation
- Exception hierarchy
- JWT token generation
"""

from .config import Config, load_config
from .exceptions import (
    ClientError,
    ConfigurationError,
    SupabaseScopedClientsError,
    TokenError,
)
from .token import generate_token

__all__ = [
    "Config",
    "load_config",
    "generate_token",
    "SupabaseScopedClientsError",
    "ConfigurationError",
    "TokenError",
    "ClientError",
]
