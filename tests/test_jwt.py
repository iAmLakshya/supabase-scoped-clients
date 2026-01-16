"""Tests for JWT token generation."""

import time
from typing import Any

import jwt
import pytest

from supabase_scoped_clients import Config, TokenError
from supabase_scoped_clients.jwt import generate_token


@pytest.fixture
def config() -> Config:
    """Create a test config with valid values."""
    return Config(
        supabase_url="https://test.supabase.co",
        supabase_key="test-key-12345",
        supabase_jwt_secret="test-jwt-secret-at-least-32-chars-long",
    )


class TestGenerateTokenBasic:
    """Tests for basic token generation."""

    def test_returns_valid_jwt_string(self, config: Config) -> None:
        """Generated token should be a decodable JWT."""
        token = generate_token(config, "user-uuid-123")

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert decoded is not None

    def test_token_contains_sub_claim_with_user_id(self, config: Config) -> None:
        """Token sub claim should contain the user UUID."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = generate_token(config, user_id)

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert decoded["sub"] == user_id

    def test_token_contains_role_claim_default_authenticated(
        self, config: Config
    ) -> None:
        """Token should have role='authenticated' by default."""
        token = generate_token(config, "user-123")

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert decoded["role"] == "authenticated"

    def test_token_contains_aud_claim_authenticated(self, config: Config) -> None:
        """Token should have aud='authenticated'."""
        token = generate_token(config, "user-123")

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert decoded["aud"] == "authenticated"

    def test_token_contains_iss_claim_from_config(self, config: Config) -> None:
        """Token iss claim should be the Supabase URL."""
        token = generate_token(config, "user-123")

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert decoded["iss"] == str(config.supabase_url)

    def test_token_contains_iat_claim(self, config: Config) -> None:
        """Token should have an iat (issued at) timestamp."""
        before = int(time.time())
        token = generate_token(config, "user-123")
        after = int(time.time())

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert before <= decoded["iat"] <= after

    def test_token_contains_exp_claim(self, config: Config) -> None:
        """Token should have an exp (expiration) timestamp."""
        token = generate_token(config, "user-123")

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert "exp" in decoded


class TestGenerateTokenExpiry:
    """Tests for token expiry configuration."""

    def test_default_expiry_is_one_hour(self, config: Config) -> None:
        """Default expiry should be 3600 seconds (1 hour) from iat."""
        token = generate_token(config, "user-123")

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert decoded["exp"] == decoded["iat"] + 3600

    def test_custom_expiry_seconds(self, config: Config) -> None:
        """expiry_seconds parameter should set custom expiry."""
        token = generate_token(config, "user-123", expiry_seconds=300)

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert decoded["exp"] == decoded["iat"] + 300

    def test_negative_expiry_raises_token_error(self, config: Config) -> None:
        """Negative expiry_seconds should raise TokenError."""
        with pytest.raises(TokenError) as exc_info:
            generate_token(config, "user-123", expiry_seconds=-1)

        assert "expiry must be positive" in str(exc_info.value).lower()

    def test_zero_expiry_raises_token_error(self, config: Config) -> None:
        """Zero expiry_seconds should raise TokenError."""
        with pytest.raises(TokenError) as exc_info:
            generate_token(config, "user-123", expiry_seconds=0)

        assert "expiry must be positive" in str(exc_info.value).lower()


class TestGenerateTokenRole:
    """Tests for role configuration."""

    def test_custom_role(self, config: Config) -> None:
        """role parameter should override default 'authenticated'."""
        token = generate_token(config, "user-123", role="admin")

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert decoded["role"] == "admin"

    def test_service_role(self, config: Config) -> None:
        """Should support service_role as a valid role."""
        token = generate_token(config, "user-123", role="service_role")

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert decoded["role"] == "service_role"


class TestGenerateTokenCustomClaims:
    """Tests for custom claims injection."""

    def test_custom_claims_added_to_token(self, config: Config) -> None:
        """custom_claims should be added to the token payload."""
        token = generate_token(
            config, "user-123", custom_claims={"tenant_id": "tenant-abc"}
        )

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert decoded["tenant_id"] == "tenant-abc"

    def test_multiple_custom_claims(self, config: Config) -> None:
        """Multiple custom claims should all be present."""
        custom: dict[str, Any] = {
            "tenant_id": "t1",
            "org_id": "o1",
            "permissions": ["read", "write"],
        }
        token = generate_token(config, "user-123", custom_claims=custom)

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert decoded["tenant_id"] == "t1"
        assert decoded["org_id"] == "o1"
        assert decoded["permissions"] == ["read", "write"]

    def test_custom_claims_do_not_override_required_claims(
        self, config: Config
    ) -> None:
        """Custom claims should not be able to override required claims."""
        malicious_claims: dict[str, Any] = {
            "sub": "hacker-id",
            "role": "hacked",
            "aud": "hacked",
        }
        token = generate_token(
            config, "real-user-123", role="authenticated", custom_claims=malicious_claims
        )

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert decoded["sub"] == "real-user-123"
        assert decoded["role"] == "authenticated"
        assert decoded["aud"] == "authenticated"

    def test_none_custom_claims_works(self, config: Config) -> None:
        """custom_claims=None should work (default behavior)."""
        token = generate_token(config, "user-123", custom_claims=None)

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert decoded["sub"] == "user-123"


class TestGenerateTokenValidation:
    """Tests for input validation."""

    def test_empty_user_id_raises_token_error(self, config: Config) -> None:
        """Empty user_id should raise TokenError."""
        with pytest.raises(TokenError) as exc_info:
            generate_token(config, "")

        assert "user_id cannot be empty" in str(exc_info.value).lower()

    def test_whitespace_user_id_raises_token_error(self, config: Config) -> None:
        """Whitespace-only user_id should raise TokenError."""
        with pytest.raises(TokenError) as exc_info:
            generate_token(config, "   ")

        assert "user_id cannot be empty" in str(exc_info.value).lower()


class TestGenerateTokenSigning:
    """Tests for token signing."""

    def test_token_signed_with_hs256(self, config: Config) -> None:
        """Token should be signed with HS256 algorithm."""
        token = generate_token(config, "user-123")

        header = jwt.get_unverified_header(token)
        assert header["alg"] == "HS256"

    def test_token_verifiable_with_secret(self, config: Config) -> None:
        """Token should be verifiable with the config JWT secret."""
        token = generate_token(config, "user-123")

        decoded = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        assert decoded["sub"] == "user-123"

    def test_token_not_verifiable_with_wrong_secret(self, config: Config) -> None:
        """Token should not verify with a wrong secret."""
        token = generate_token(config, "user-123")

        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(
                token,
                "wrong-secret",
                algorithms=["HS256"],
                audience="authenticated",
            )
