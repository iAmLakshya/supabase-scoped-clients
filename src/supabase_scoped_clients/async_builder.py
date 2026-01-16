"""Fluent builder API for creating async AsyncScopedClient instances."""

from typing import Any, Self

from .async_scoped_client import AsyncScopedClient
from .config import Config


class AsyncScopedClientBuilder:
    """Fluent builder for configuring and creating AsyncScopedClient instances.

    Provides a chainable API for setting client options before creation.
    All configuration methods return self to enable method chaining.
    The build() method is async since AsyncScopedClient requires async creation.

    Example:
        client = await (AsyncScopedClientBuilder(user_id, config)
            .with_role("admin")
            .with_expiry(7200)
            .with_claims({"tenant_id": "abc"})
            .with_refresh_threshold(120)
            .build())
    """

    def __init__(self, user_id: str, config: Config | None = None) -> None:
        """Initialize the builder with required user_id.

        Args:
            user_id: The UUID of the user to impersonate.
            config: Configuration for Supabase connection. If not provided,
                loads from environment variables when build() is called.
        """
        self._user_id = user_id
        self._config = config
        self._role: str = "authenticated"
        self._expiry_seconds: int = 3600
        self._custom_claims: dict[str, Any] | None = None
        self._refresh_threshold_seconds: int = 60

    def with_role(self, role: str) -> Self:
        """Set the Supabase role for the token.

        Args:
            role: The role to use (e.g., "authenticated", "service_role").

        Returns:
            Self for method chaining.
        """
        self._role = role
        return self

    def with_expiry(self, seconds: int) -> Self:
        """Set token validity duration in seconds.

        Args:
            seconds: Token validity in seconds.

        Returns:
            Self for method chaining.
        """
        self._expiry_seconds = seconds
        return self

    def with_claims(self, claims: dict[str, Any]) -> Self:
        """Set additional custom claims to include in the JWT.

        Args:
            claims: Dictionary of custom claims.

        Returns:
            Self for method chaining.
        """
        self._custom_claims = claims
        return self

    def with_refresh_threshold(self, seconds: int) -> Self:
        """Set seconds before expiry to trigger automatic refresh.

        Args:
            seconds: Seconds before expiry to refresh token.

        Returns:
            Self for method chaining.
        """
        self._refresh_threshold_seconds = seconds
        return self

    async def build(self) -> AsyncScopedClient:
        """Create and return the configured AsyncScopedClient.

        This is an async method because AsyncScopedClient requires async creation.

        Returns:
            An AsyncScopedClient instance with the configured options.

        Raises:
            ClientError: If user_id is empty.
            ConfigurationError: If configuration is invalid or missing.
        """
        return await AsyncScopedClient.create(
            self._user_id,
            config=self._config,
            role=self._role,
            expiry_seconds=self._expiry_seconds,
            custom_claims=self._custom_claims,
            refresh_threshold_seconds=self._refresh_threshold_seconds,
        )
