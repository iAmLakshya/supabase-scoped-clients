"""Asynchronous client factory for user-scoped Supabase clients."""

from typing import Any

from supabase.lib.client_options import AsyncClientOptions

from supabase import AsyncClient, acreate_client

from ..core.config import Config, load_config
from ..core.exceptions import ClientError
from ..core.token import generate_token


async def get_async_client(
    user_id: str,
    *,
    config: Config | None = None,
    role: str = "authenticated",
    expiry_seconds: int = 3600,
    custom_claims: dict[str, Any] | None = None,
) -> AsyncClient:
    """Create an async Supabase client that operates as the specified user.

    The returned client has an Authorization header set with a JWT token
    that identifies the user, allowing RLS policies to work correctly.

    Args:
        user_id: The UUID of the user to impersonate.
        config: Configuration for Supabase connection. If not provided,
            loads from environment variables.
        role: The Supabase role for the token (default: "authenticated").
        expiry_seconds: Token validity in seconds (default: 3600 = 1 hour).
        custom_claims: Additional claims to include in the JWT token.

    Returns:
        A configured AsyncClient ready for user-scoped operations.

    Raises:
        ClientError: If user_id is empty.
        ConfigurationError: If configuration is invalid or missing.
    """
    if not user_id or not user_id.strip():
        raise ClientError("user_id cannot be empty")

    if config is None:
        config = load_config()

    token = generate_token(
        config,
        user_id,
        role=role,
        expiry_seconds=expiry_seconds,
        custom_claims=custom_claims,
    )

    options = AsyncClientOptions(
        headers={"Authorization": f"Bearer {token}"},
    )

    return await acreate_client(
        str(config.supabase_url),
        config.supabase_key,
        options=options,
    )
