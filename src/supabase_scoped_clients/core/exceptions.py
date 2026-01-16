"""Exception hierarchy for supabase_scoped_clients."""

from typing import Any


class SupabaseScopedClientsError(Exception):
    """Base exception for all library errors.

    Provides helpful __str__ that includes exception name and message.
    """

    def __init__(self, message: str, **context: Any) -> None:
        self.message = message
        self.context = context
        super().__init__(message)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message}"


class ConfigurationError(SupabaseScopedClientsError):
    """Raised for invalid configuration.

    Includes field_name and reason for clear error messages.
    """

    def __init__(self, field_name: str, reason: str) -> None:
        self.field_name = field_name
        self.reason = reason
        message = f"{field_name} - {reason}"
        super().__init__(message, field_name=field_name, reason=reason)


class TokenError(SupabaseScopedClientsError):
    """Raised for JWT generation/validation errors."""

    pass


class ClientError(SupabaseScopedClientsError):
    """Raised for client creation errors."""

    pass
