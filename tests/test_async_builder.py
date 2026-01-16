"""Tests for the AsyncScopedClientBuilder fluent API."""

import uuid

import pytest

from supabase_scoped_clients.builders.async_builder import AsyncScopedClientBuilder
from supabase_scoped_clients.clients.async_client import AsyncScopedClient
from supabase_scoped_clients.core.config import Config
from supabase_scoped_clients.core.exceptions import ClientError

LOCAL_SUPABASE_URL = "http://127.0.0.1:54331"
LOCAL_SUPABASE_KEY = "sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH"
LOCAL_JWT_SECRET = "super-secret-jwt-token-with-at-least-32-characters-long"


@pytest.fixture
def config():
    """Create a test config for local Supabase."""
    return Config(
        supabase_url=LOCAL_SUPABASE_URL,
        supabase_key=LOCAL_SUPABASE_KEY,
        supabase_jwt_secret=LOCAL_JWT_SECRET,
    )


class TestAsyncScopedClientBuilder:
    """Tests for AsyncScopedClientBuilder fluent API."""

    @pytest.mark.asyncio
    async def test_build_minimal(self, config):
        """Builder can create AsyncScopedClient with just user_id."""
        user_id = str(uuid.uuid4())
        client = await AsyncScopedClientBuilder(user_id, config).build()

        assert isinstance(client, AsyncScopedClient)

    @pytest.mark.asyncio
    async def test_build_with_all_options(self, config):
        """Builder can chain all configuration methods."""
        user_id = str(uuid.uuid4())
        client = await (
            AsyncScopedClientBuilder(user_id, config)
            .with_role("admin")
            .with_expiry(7200)
            .with_claims({"tenant_id": "abc"})
            .with_refresh_threshold(120)
            .build()
        )

        assert isinstance(client, AsyncScopedClient)
        assert client._role == "admin"
        assert client._expiry_seconds == 7200
        assert client._custom_claims == {"tenant_id": "abc"}
        assert client._refresh_threshold == 120

    def test_fluent_chaining_returns_self(self, config):
        """Each fluent method returns the builder instance."""
        user_id = str(uuid.uuid4())
        builder = AsyncScopedClientBuilder(user_id, config)

        assert builder.with_role("admin") is builder
        assert builder.with_expiry(7200) is builder
        assert builder.with_claims({"key": "value"}) is builder
        assert builder.with_refresh_threshold(120) is builder

    @pytest.mark.asyncio
    async def test_build_validates_user_id(self, config):
        """Empty user_id raises ClientError on build."""
        with pytest.raises(ClientError) as excinfo:
            await AsyncScopedClientBuilder("", config).build()
        assert "user_id" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_build_validates_whitespace_user_id(self, config):
        """Whitespace-only user_id raises ClientError on build."""
        with pytest.raises(ClientError) as excinfo:
            await AsyncScopedClientBuilder("   ", config).build()
        assert "user_id" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_default_values(self, config):
        """Builder uses sensible defaults when options not specified."""
        user_id = str(uuid.uuid4())
        client = await AsyncScopedClientBuilder(user_id, config).build()

        assert client._role == "authenticated"
        assert client._expiry_seconds == 3600
        assert client._custom_claims is None
        assert client._refresh_threshold == 60

    @pytest.mark.asyncio
    async def test_built_client_works(self, config):
        """Client built with builder can perform operations."""
        user_id = str(uuid.uuid4())
        client = await AsyncScopedClientBuilder(user_id, config).build()

        response = await (
            client.table("test_user_data")
            .insert({"user_id": user_id, "content": "async builder test"})
            .execute()
        )

        assert len(response.data) == 1
        assert response.data[0]["user_id"] == user_id
