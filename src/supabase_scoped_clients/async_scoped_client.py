"""AsyncScopedClient wrapper with automatic token refresh for async Supabase clients."""

import asyncio
import time
from typing import Any

from supabase import AsyncClient, acreate_client
from supabase.lib.client_options import AsyncClientOptions

from .config import Config, load_config
from .exceptions import ClientError
from .jwt import generate_token


class AsyncScopedClient:
    """Async Supabase client wrapper with automatic token refresh.

    Wraps supabase.AsyncClient and transparently refreshes the JWT token
    before it expires. Users don't need to handle token expiry manually.

    Use the async factory method `create()` to instantiate:

        client = await AsyncScopedClient.create(user_id, config=config)

    The wrapper delegates all operations to the underlying AsyncClient
    while ensuring the token is valid before each operation.
    """

    def __init__(
        self,
        user_id: str,
        config: Config,
        client: AsyncClient,
        token_exp: int,
        role: str = "authenticated",
        expiry_seconds: int = 3600,
        custom_claims: dict[str, Any] | None = None,
        refresh_threshold_seconds: int = 60,
    ) -> None:
        """Private constructor - use create() classmethod instead."""
        self._user_id = user_id
        self._config = config
        self._client = client
        self._token_exp = token_exp
        self._role = role
        self._expiry_seconds = expiry_seconds
        self._custom_claims = custom_claims
        self._refresh_threshold = refresh_threshold_seconds
        self._lock = asyncio.Lock()

    @classmethod
    async def create(
        cls,
        user_id: str,
        *,
        config: Config | None = None,
        role: str = "authenticated",
        expiry_seconds: int = 3600,
        custom_claims: dict[str, Any] | None = None,
        refresh_threshold_seconds: int = 60,
    ) -> "AsyncScopedClient":
        """Create an AsyncScopedClient with automatic token refresh.

        Args:
            user_id: The UUID of the user to impersonate.
            config: Configuration for Supabase connection. If not provided,
                loads from environment variables.
            role: The Supabase role for the token (default: "authenticated").
            expiry_seconds: Token validity in seconds (default: 3600 = 1 hour).
            custom_claims: Additional claims to include in the JWT token.
            refresh_threshold_seconds: Seconds before expiry to refresh token
                (default: 60).

        Returns:
            An AsyncScopedClient ready for user-scoped operations.

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

        token_exp = int(time.time()) + expiry_seconds

        options = AsyncClientOptions(
            headers={"Authorization": f"Bearer {token}"},
        )

        client = await acreate_client(
            str(config.supabase_url),
            config.supabase_key,
            options=options,
        )

        return cls(
            user_id=user_id,
            config=config,
            client=client,
            token_exp=token_exp,
            role=role,
            expiry_seconds=expiry_seconds,
            custom_claims=custom_claims,
            refresh_threshold_seconds=refresh_threshold_seconds,
        )

    def _needs_refresh(self) -> bool:
        """Check if the token needs to be refreshed."""
        return time.time() + self._refresh_threshold >= self._token_exp

    async def _refresh_token(self) -> None:
        """Regenerate the token and update client headers."""
        token = generate_token(
            self._config,
            self._user_id,
            role=self._role,
            expiry_seconds=self._expiry_seconds,
            custom_claims=self._custom_claims,
        )

        self._token_exp = int(time.time()) + self._expiry_seconds

        self._client.options.headers["Authorization"] = f"Bearer {token}"

    async def _ensure_valid_token(self) -> None:
        """Ensure the token is valid, refreshing if necessary.

        Uses asyncio.Lock for single-flight pattern - concurrent operations
        share one refresh rather than triggering multiple refreshes.

        Call this before operations on long-lived clients.
        """
        if not self._needs_refresh():
            return

        async with self._lock:
            # Double-check after acquiring lock (another coroutine may have refreshed)
            if self._needs_refresh():
                await self._refresh_token()

    # Public alias
    ensure_valid_token = _ensure_valid_token

    def __getattr__(self, name: str) -> Any:
        """Delegate all attribute access to underlying client.

        For long-lived clients, call await ensure_valid_token() before operations.

        Args:
            name: Attribute name to access on the underlying client.

        Returns:
            The attribute from the underlying AsyncClient.

        Raises:
            AttributeError: If attribute doesn't exist on the client.
        """
        if self._client is None:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        return getattr(self._client, name)
