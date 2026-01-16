"""ScopedClient wrapper with automatic token refresh for sync Supabase clients."""

import threading
import time
from typing import Any

from supabase import Client, create_client
from supabase.lib.client_options import SyncClientOptions

from .config import Config, load_config
from .exceptions import ClientError
from .jwt import generate_token


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

    def _ensure_valid_token(self) -> None:
        """Check if token refresh is needed and refresh if so.

        Uses double-checked locking pattern to minimize lock contention
        while ensuring only one refresh happens for concurrent operations.
        """
        current_time = int(time.time())

        if current_time + self._refresh_threshold < self._token_exp:
            return

        with self._lock:
            # Double-check after acquiring lock
            current_time = int(time.time())
            if current_time + self._refresh_threshold >= self._token_exp:
                self._create_client()

    def table(self, table_name: str) -> Any:
        """Access a table with automatic token refresh.

        Args:
            table_name: Name of the table to access.

        Returns:
            Table query builder from the underlying Supabase client.
        """
        self._ensure_valid_token()
        return self._client.table(table_name)

    @property
    def storage(self) -> Any:
        """Access storage with automatic token refresh.

        Returns:
            Storage client from the underlying Supabase client.
        """
        self._ensure_valid_token()
        return self._client.storage

    @property
    def functions(self) -> Any:
        """Access edge functions with automatic token refresh.

        Returns:
            Functions client from the underlying Supabase client.
        """
        self._ensure_valid_token()
        return self._client.functions

    def rpc(self, fn: str, params: dict[str, Any] | None = None) -> Any:
        """Call a stored procedure with automatic token refresh.

        Args:
            fn: Name of the stored procedure to call.
            params: Parameters to pass to the procedure.

        Returns:
            RPC query builder from the underlying Supabase client.
        """
        self._ensure_valid_token()
        if params is None:
            return self._client.rpc(fn)
        return self._client.rpc(fn, params)

    @property
    def auth(self) -> Any:
        """Access auth with automatic token refresh.

        Returns:
            Auth client from the underlying Supabase client.
        """
        self._ensure_valid_token()
        return self._client.auth

    @property
    def realtime(self) -> Any:
        """Access realtime with automatic token refresh.

        Returns:
            Realtime client from the underlying Supabase client.
        """
        self._ensure_valid_token()
        return self._client.realtime

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to underlying client with auto-refresh.

        This fallback ensures any new Supabase Client methods work automatically
        without requiring wrapper updates. Explicit methods above provide IDE
        autocomplete for common operations.

        Args:
            name: Attribute name to access on the underlying client.

        Returns:
            The attribute from the underlying Supabase client.

        Raises:
            AttributeError: If attribute doesn't exist on the client.
        """
        if self._client is None:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        self._ensure_valid_token()
        return getattr(self._client, name)
