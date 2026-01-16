"""Tests for configuration module."""

import pytest

from supabase_scoped_clients import Config, ConfigurationError, load_config


class TestConfigEnvVars:
    """Tests for loading config from environment variables."""

    def test_loads_from_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "test-key")
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")

        config = load_config()

        assert str(config.supabase_url) == "https://example.supabase.co/"
        assert config.supabase_key == "test-key"
        assert config.supabase_jwt_secret == "test-secret"

    def test_env_prefix_is_supabase(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "key")
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "secret")

        config = load_config()
        assert config.supabase_key == "key"


class TestConfigProgrammaticOverride:
    """Tests for programmatic configuration override."""

    def test_programmatic_override_works(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SUPABASE_URL", "https://env.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "env-key")
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "env-secret")

        config = load_config(
            supabase_url="https://override.supabase.co",
            supabase_key="override-key",
        )

        assert str(config.supabase_url) == "https://override.supabase.co/"
        assert config.supabase_key == "override-key"
        assert config.supabase_jwt_secret == "env-secret"

    def test_all_values_can_be_overridden(self) -> None:
        config = load_config(
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
            supabase_jwt_secret="test-secret",
        )

        assert str(config.supabase_url) == "https://test.supabase.co/"
        assert config.supabase_key == "test-key"
        assert config.supabase_jwt_secret == "test-secret"


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_invalid_url_raises_configuration_error(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(
                supabase_url="not-a-valid-url",
                supabase_key="key",
                supabase_jwt_secret="secret",
            )

        assert exc_info.value.field_name == "supabase_url"
        assert "supabase_url" in str(exc_info.value)

    def test_empty_key_raises_configuration_error(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(
                supabase_url="https://test.supabase.co",
                supabase_key="",
                supabase_jwt_secret="secret",
            )

        assert exc_info.value.field_name == "supabase_key"

    def test_whitespace_only_key_raises_configuration_error(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(
                supabase_url="https://test.supabase.co",
                supabase_key="   ",
                supabase_jwt_secret="secret",
            )

        assert exc_info.value.field_name == "supabase_key"

    def test_empty_jwt_secret_raises_configuration_error(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(
                supabase_url="https://test.supabase.co",
                supabase_key="key",
                supabase_jwt_secret="",
            )

        assert exc_info.value.field_name == "supabase_jwt_secret"

    def test_missing_url_raises_configuration_error(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(
                supabase_key="key",
                supabase_jwt_secret="secret",
            )

        assert "supabase_url" in exc_info.value.field_name


class TestConfigErrorMessages:
    """Tests for helpful error messages."""

    def test_error_message_includes_field_name(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(
                supabase_url="invalid",
                supabase_key="key",
                supabase_jwt_secret="secret",
            )

        error_msg = str(exc_info.value)
        assert "ConfigurationError" in error_msg
        assert "supabase_url" in error_msg

    def test_error_message_includes_reason(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(
                supabase_url="https://test.supabase.co",
                supabase_key="key",
                supabase_jwt_secret="",
            )

        assert exc_info.value.reason is not None
        assert len(exc_info.value.reason) > 0
