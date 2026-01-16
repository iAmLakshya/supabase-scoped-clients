"""Tests for exception hierarchy."""

import pytest

from supabase_scoped_clients.core.exceptions import (
    ClientError,
    ConfigurationError,
    SupabaseScopedClientsError,
    TokenError,
)


class TestSupabaseScopedClientsError:
    """Tests for base exception."""

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(SupabaseScopedClientsError) as exc_info:
            raise SupabaseScopedClientsError("test message")
        assert str(exc_info.value) == "SupabaseScopedClientsError: test message"

    def test_stores_message_as_attribute(self) -> None:
        exc = SupabaseScopedClientsError("test message")
        assert exc.message == "test message"

    def test_stores_context_as_attribute(self) -> None:
        exc = SupabaseScopedClientsError("test", key="value", other=123)
        assert exc.context == {"key": "value", "other": 123}


class TestConfigurationError:
    """Tests for configuration error."""

    def test_includes_field_name_in_message(self) -> None:
        exc = ConfigurationError("supabase_url", "URL must start with https://")
        assert str(exc) == "ConfigurationError: supabase_url - URL must start with https://"

    def test_stores_field_name_as_attribute(self) -> None:
        exc = ConfigurationError("supabase_key", "cannot be empty")
        assert exc.field_name == "supabase_key"

    def test_stores_reason_as_attribute(self) -> None:
        exc = ConfigurationError("supabase_key", "cannot be empty")
        assert exc.reason == "cannot be empty"

    def test_is_subclass_of_base_error(self) -> None:
        exc = ConfigurationError("field", "reason")
        assert isinstance(exc, SupabaseScopedClientsError)

    def test_can_be_caught_as_base_error(self) -> None:
        with pytest.raises(SupabaseScopedClientsError):
            raise ConfigurationError("field", "reason")


class TestTokenError:
    """Tests for token error."""

    def test_is_subclass_of_base_error(self) -> None:
        exc = TokenError("token generation failed")
        assert isinstance(exc, SupabaseScopedClientsError)

    def test_str_includes_class_name(self) -> None:
        exc = TokenError("token generation failed")
        assert str(exc) == "TokenError: token generation failed"


class TestClientError:
    """Tests for client error."""

    def test_is_subclass_of_base_error(self) -> None:
        exc = ClientError("client creation failed")
        assert isinstance(exc, SupabaseScopedClientsError)

    def test_str_includes_class_name(self) -> None:
        exc = ClientError("client creation failed")
        assert str(exc) == "ClientError: client creation failed"
