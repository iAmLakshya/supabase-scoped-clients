"""Asynchronous client factory for user-scoped Supabase clients."""

from typing import Any

from supabase.lib.client_options import AsyncClientOptions

from supabase import AsyncClient, acreate_client

from ..clients.async_client import AsyncScopedClient
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
    auto_refresh: bool = True,
    refresh_threshold_seconds: int = 60,
) -> AsyncClient:
    """Create an async Supabase client that operates as the specified user.

    The returned client has an Authorization header set with a JWT token
    that identifies the user, allowing RLS policies to work correctly.

    By default, automatic token refresh is enabled. The client will refresh
    its token before expiry, ensuring seamless operation for long-running
    processes without manual token management.

    Args:
        user_id: The UUID of the user to impersonate.
        config: Configuration for Supabase connection. If not provided,
            loads from environment variables.
        role: The Supabase role for the token (default: "authenticated").
        expiry_seconds: Token validity in seconds (default: 3600 = 1 hour).
        custom_claims: Additional claims to include in the JWT token.
        auto_refresh: Whether to automatically refresh the token before expiry
            (default: True). Set to False for short-lived operations.
        refresh_threshold_seconds: Seconds before expiry to trigger refresh
            (default: 60). Only used when auto_refresh=True.

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

    if auto_refresh:
        scoped = await AsyncScopedClient.create(
            user_id,
            config=config,
            role=role,
            expiry_seconds=expiry_seconds,
            custom_claims=custom_claims,
            refresh_threshold_seconds=refresh_threshold_seconds,
        )
        return scoped.client

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
