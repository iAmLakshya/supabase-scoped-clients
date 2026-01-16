"""ScopedClient wrapper with automatic token refresh for sync Supabase clients."""

import threading
import time
from typing import Any

from supabase import Client, create_client
from supabase.lib.client_options import SyncClientOptions

from .config import Config, load_config
from .exceptions import ClientError
from .jwt import generate_token
from .proxy import create_proxy


class ScopedClient:
    """Wrapper for Supabase Client with automatic token refresh.

    ScopedClient wraps a Supabase Client and automatically refreshes the JWT token
    before it expires, ensuring seamless operation without manual token management.

    The wrapper uses a single-flight pattern (threading.Lock) to ensure that
    concurrent operations don't cause multiple token refreshes.

    Args:
        user_id: The UUID of the user to impersonate.
        config: Configuration for Supabase connection. If not provided,
            loads from environment variables.
        role: The Supabase role for the token (default: "authenticated").
        expiry_seconds: Token validity in seconds (default: 3600 = 1 hour).
        custom_claims: Additional claims to include in the JWT token.
        refresh_threshold_seconds: Seconds before expiry to trigger refresh
            (default: 60). Token will be refreshed when
            current_time + threshold >= token_exp.

    Example:
        >>> scoped = ScopedClient(user_id, config)
        >>> # Token auto-refreshes when needed
        >>> scoped.table("items").select("*").execute()
    """

    def __init__(
        self,
        user_id: str,
        config: Config | None = None,
        *,
        role: str = "authenticated",
        expiry_seconds: int = 3600,
        custom_claims: dict[str, Any] | None = None,
        refresh_threshold_seconds: int = 60,
    ) -> None:
        if not user_id or not user_id.strip():
            raise ClientError("user_id cannot be empty")

        self._user_id = user_id
        self._config = config if config is not None else load_config()
        self._role = role
        self._expiry_seconds = expiry_seconds
        self._custom_claims = custom_claims
        self._refresh_threshold = refresh_threshold_seconds
        self._lock = threading.Lock()
        self._token_exp: int = 0
        self._client: Client | None = None
        self._proxied_client: Client | None = None

        self._create_client()

    def _create_client(self) -> None:
        """Generate token and create the underlying Supabase client."""
        token = generate_token(
            self._config,
            self._user_id,
            role=self._role,
            expiry_seconds=self._expiry_seconds,
            custom_claims=self._custom_claims,
        )

        self._token_exp = int(time.time()) + self._expiry_seconds

        options = SyncClientOptions(
            headers={"Authorization": f"Bearer {token}"},
        )

        self._client = create_client(
            str(self._config.supabase_url),
            self._config.supabase_key,
            options=options,
        )

        self._proxied_client = create_proxy(self._client, self)

    def ensure_valid_token(self) -> None:
        """Check if token refresh is needed and refresh if so.

        Uses double-checked locking pattern to minimize lock contention
        while ensuring only one refresh happens for concurrent operations.
        """
        current_time = int(time.time())

        if current_time + self._refresh_threshold < self._token_exp:
            return

        with self._lock:
            current_time = int(time.time())
            if current_time + self._refresh_threshold >= self._token_exp:
                self._create_client()

    @property
    def client(self) -> Client:
        """Get the proxied client with automatic token refresh.

        Returns:
            The proxied Supabase client that auto-refreshes tokens.
        """
        if self._proxied_client is None:
            raise ClientError("Client not initialized")
        return self._proxied_client

    def __getattr__(self, name: str) -> Any:
        """Delegate all attribute access to the proxied client with auto-refresh.

        Automatically refreshes the token before delegating, ensuring seamless
        operation regardless of which Supabase Client method/property is accessed.

        Args:
            name: Attribute name to access on the underlying client.

        Returns:
            The attribute from the proxied Supabase client.

        Raises:
            AttributeError: If attribute doesn't exist on the client.
        """
        if self._proxied_client is None:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        self.ensure_valid_token()
        return getattr(self._proxied_client, name)
