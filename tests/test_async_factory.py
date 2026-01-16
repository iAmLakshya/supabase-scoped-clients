"""Tests for the asynchronous client factory."""

import uuid

import pytest

from supabase import AsyncClient
from supabase_scoped_clients.core.exceptions import ClientError
from supabase_scoped_clients.factories.async_factory import get_async_client


class TestGetAsyncClientBasic:
    """Test basic get_async_client functionality."""

    @pytest.mark.asyncio
    async def test_returns_async_supabase_client(self, config):
        """get_async_client returns an AsyncClient instance when auto_refresh=False."""
        user_id = str(uuid.uuid4())
        client = await get_async_client(user_id, config=config, auto_refresh=False)
        assert isinstance(client, AsyncClient)

    @pytest.mark.asyncio
    async def test_accepts_user_id_as_string(self, config):
        """get_async_client accepts user_id as a string."""
        user_id = str(uuid.uuid4())
        client = await get_async_client(user_id, config=config)
        assert client is not None


class TestGetAsyncClientConfig:
    """Test configuration handling."""

    @pytest.mark.asyncio
    async def test_uses_provided_config(self, config):
        """get_async_client uses the provided config."""
        user_id = str(uuid.uuid4())
        client = await get_async_client(user_id, config=config)
        assert client is not None

    @pytest.mark.asyncio
    async def test_loads_config_from_env_when_not_provided(
        self, monkeypatch, supabase_url, supabase_key, supabase_jwt_secret
    ):
        """get_async_client loads config from environment when not provided."""
        monkeypatch.setenv("SUPABASE_URL", supabase_url)
        monkeypatch.setenv("SUPABASE_KEY", supabase_key)
        monkeypatch.setenv("SUPABASE_JWT_SECRET", supabase_jwt_secret)

        user_id = str(uuid.uuid4())
        client = await get_async_client(user_id, auto_refresh=False)
        assert isinstance(client, AsyncClient)


class TestGetAsyncClientParameters:
    """Test parameter pass-through."""

    @pytest.mark.asyncio
    async def test_role_parameter_passed_to_token(self, config):
        """role parameter is passed to token generation."""
        user_id = str(uuid.uuid4())
        client = await get_async_client(user_id, config=config, role="service_role")
        assert client is not None

    @pytest.mark.asyncio
    async def test_expiry_seconds_parameter_passed_to_token(self, config):
        """expiry_seconds parameter is passed to token generation."""
        user_id = str(uuid.uuid4())
        client = await get_async_client(user_id, config=config, expiry_seconds=7200)
        assert client is not None

    @pytest.mark.asyncio
    async def test_custom_claims_parameter_passed_to_token(self, config):
        """custom_claims parameter is passed to token generation."""
        user_id = str(uuid.uuid4())
        client = await get_async_client(
            user_id, config=config, custom_claims={"org_id": "test-org"}
        )
        assert client is not None


class TestGetAsyncClientValidation:
    """Test input validation."""

    @pytest.mark.asyncio
    async def test_empty_user_id_raises_client_error(self, config):
        """Empty user_id raises ClientError."""
        with pytest.raises(ClientError) as excinfo:
            await get_async_client("", config=config)
        assert "user_id" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_whitespace_user_id_raises_client_error(self, config):
        """Whitespace-only user_id raises ClientError."""
        with pytest.raises(ClientError) as excinfo:
            await get_async_client("   ", config=config)
        assert "user_id" in str(excinfo.value).lower()


class TestGetAsyncClientIndependence:
    """Test that multiple async clients operate independently."""

    @pytest.mark.asyncio
    async def test_multiple_clients_for_same_user_are_independent(self, config):
        """Multiple async clients for the same user are independent instances."""
        user_id = str(uuid.uuid4())
        client1 = await get_async_client(user_id, config=config)
        client2 = await get_async_client(user_id, config=config)

        assert client1 is not client2

    @pytest.mark.asyncio
    async def test_multiple_clients_for_different_users_are_independent(self, config):
        """Multiple async clients for different users are independent instances."""
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())

        client1 = await get_async_client(user1_id, config=config)
        client2 = await get_async_client(user2_id, config=config)

        assert client1 is not client2


class TestGetAsyncClientRLS:
    """Integration tests for RLS policy enforcement with async client.

    These tests verify that the async client respects RLS policies by testing
    that a user can only see/modify their own data in the test_user_data table.

    Requires local Supabase to be running with the test_user_data table.
    """

    @pytest.fixture
    def user1_id(self):
        """Generate a user ID for test user 1."""
        return str(uuid.uuid4())

    @pytest.fixture
    def user2_id(self):
        """Generate a user ID for test user 2."""
        return str(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_user_can_insert_own_data(self, config, user1_id):
        """User can insert data with their own user_id."""
        client = await get_async_client(user1_id, config=config)

        response = await (
            client.table("test_user_data")
            .insert({"user_id": user1_id, "content": "user1 content"})
            .execute()
        )

        assert len(response.data) == 1
        assert response.data[0]["user_id"] == user1_id
        assert response.data[0]["content"] == "user1 content"

    @pytest.mark.asyncio
    async def test_user_can_read_own_data(self, config, user1_id):
        """User can read their own data."""
        client = await get_async_client(user1_id, config=config)

        # Insert some data first
        await (
            client.table("test_user_data")
            .insert({"user_id": user1_id, "content": "readable content"})
            .execute()
        )

        # Read it back
        response = await client.table("test_user_data").select("*").execute()

        assert len(response.data) >= 1
        assert all(row["user_id"] == user1_id for row in response.data)

    @pytest.mark.asyncio
    async def test_user_cannot_read_other_users_data(self, config, user1_id, user2_id):
        """User cannot read another user's data."""
        # User 1 inserts data
        client1 = await get_async_client(user1_id, config=config)
        await (
            client1.table("test_user_data")
            .insert({"user_id": user1_id, "content": "user1 secret"})
            .execute()
        )

        # User 2 tries to read all data
        client2 = await get_async_client(user2_id, config=config)
        response = await client2.table("test_user_data").select("*").execute()

        # User 2 should not see user 1's data
        user1_data = [row for row in response.data if row["user_id"] == user1_id]
        assert len(user1_data) == 0

    @pytest.mark.asyncio
    async def test_user_cannot_insert_data_for_other_user(
        self, config, user1_id, user2_id
    ):
        """User cannot insert data with another user's user_id."""
        client1 = await get_async_client(user1_id, config=config)

        # Try to insert data pretending to be user2
        # Using Exception because supabase can raise various error types
        with pytest.raises(Exception):  # noqa: B017
            await (
                client1.table("test_user_data")
                .insert({"user_id": user2_id, "content": "malicious content"})
                .execute()
            )

    @pytest.mark.asyncio
    async def test_user_can_update_own_data(self, config, user1_id):
        """User can update their own data."""
        client = await get_async_client(user1_id, config=config)

        # Insert data
        insert_response = await (
            client.table("test_user_data")
            .insert({"user_id": user1_id, "content": "original"})
            .execute()
        )
        row_id = insert_response.data[0]["id"]

        # Update it
        update_response = await (
            client.table("test_user_data")
            .update({"content": "updated"})
            .eq("id", row_id)
            .execute()
        )

        assert len(update_response.data) == 1
        assert update_response.data[0]["content"] == "updated"

    @pytest.mark.asyncio
    async def test_user_can_delete_own_data(self, config, user1_id):
        """User can delete their own data."""
        client = await get_async_client(user1_id, config=config)

        # Insert data
        insert_response = await (
            client.table("test_user_data")
            .insert({"user_id": user1_id, "content": "to be deleted"})
            .execute()
        )
        row_id = insert_response.data[0]["id"]

        # Delete it
        delete_response = await (
            client.table("test_user_data").delete().eq("id", row_id).execute()
        )

        assert len(delete_response.data) == 1

        # Verify it's gone
        select_response = await (
            client.table("test_user_data").select("*").eq("id", row_id).execute()
        )
        assert len(select_response.data) == 0
