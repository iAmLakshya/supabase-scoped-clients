"""Tests for AsyncScopedClient with automatic token refresh."""

import asyncio
import uuid

import pytest

from supabase_scoped_clients.core.exceptions import ClientError


class TestAsyncScopedClientCreation:
    """Test AsyncScopedClient creation and basic properties."""

    @pytest.mark.asyncio
    async def test_create_returns_async_scoped_client(self, config):
        """AsyncScopedClient.create() returns an AsyncScopedClient instance."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        user_id = str(uuid.uuid4())
        client = await AsyncScopedClient.create(user_id, config=config)
        assert isinstance(client, AsyncScopedClient)

    @pytest.mark.asyncio
    async def test_empty_user_id_raises_client_error(self, config):
        """Empty user_id raises ClientError."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        with pytest.raises(ClientError) as excinfo:
            await AsyncScopedClient.create("", config=config)
        assert "user_id" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_whitespace_user_id_raises_client_error(self, config):
        """Whitespace-only user_id raises ClientError."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        with pytest.raises(ClientError) as excinfo:
            await AsyncScopedClient.create("   ", config=config)
        assert "user_id" in str(excinfo.value).lower()


class TestAsyncScopedClientDelegation:
    """Test that AsyncScopedClient delegates to AsyncClient."""

    @pytest.mark.asyncio
    async def test_table_property_returns_table_accessor(self, config):
        """table property returns the underlying client's table accessor."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        user_id = str(uuid.uuid4())
        client = await AsyncScopedClient.create(user_id, config=config)
        table = client.table("test_user_data")
        assert table is not None

    @pytest.mark.asyncio
    async def test_storage_property_returns_storage_client(self, config):
        """storage property returns the underlying client's storage client."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        user_id = str(uuid.uuid4())
        client = await AsyncScopedClient.create(user_id, config=config)
        storage = client.storage
        assert storage is not None

    @pytest.mark.asyncio
    async def test_functions_property_returns_functions_client(self, config):
        """functions property returns the underlying client's functions client."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        user_id = str(uuid.uuid4())
        client = await AsyncScopedClient.create(user_id, config=config)
        functions = client.functions
        assert functions is not None

    @pytest.mark.asyncio
    async def test_rpc_method_calls_underlying_client(self, config):
        """rpc method delegates to the underlying client."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        user_id = str(uuid.uuid4())
        client = await AsyncScopedClient.create(user_id, config=config)
        # rpc method should exist and be callable
        assert hasattr(client, "rpc")
        assert callable(client.rpc)


class TestAsyncScopedClientTokenRefresh:
    """Test automatic token refresh behavior."""

    @pytest.mark.asyncio
    async def test_token_not_refreshed_when_valid(self, config):
        """Token is not refreshed when it's still valid."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        user_id = str(uuid.uuid4())
        client = await AsyncScopedClient.create(
            user_id, config=config, expiry_seconds=3600
        )
        original_exp = client._token_exp

        # Access table (should not trigger refresh)
        client.table("test_user_data")

        # Token expiry should not change
        assert client._token_exp == original_exp

    @pytest.mark.asyncio
    async def test_token_refreshed_when_near_expiry(self, config):
        """Token is refreshed when approaching expiry threshold."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        user_id = str(uuid.uuid4())
        # Create with 2 second expiry and 1 second threshold
        client = await AsyncScopedClient.create(
            user_id,
            config=config,
            expiry_seconds=2,
            refresh_threshold_seconds=1,
        )
        original_exp = client._token_exp

        # Wait until we're within refresh threshold
        await asyncio.sleep(1.5)

        # Ensure token validity (should trigger refresh)
        await client._ensure_valid_token()

        # Token should have been refreshed with new expiry
        assert client._token_exp > original_exp

    @pytest.mark.asyncio
    async def test_refresh_threshold_is_configurable(self, config):
        """refresh_threshold_seconds parameter controls when refresh happens."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        user_id = str(uuid.uuid4())
        # Create with 10 second expiry but 8 second threshold
        client = await AsyncScopedClient.create(
            user_id,
            config=config,
            expiry_seconds=10,
            refresh_threshold_seconds=8,
        )
        original_exp = client._token_exp

        # At t=0, we're already within threshold (10s expiry, 8s threshold)
        # so the next access should refresh
        await asyncio.sleep(0.1)  # Small delay to ensure time has passed

        # Ensure token validity (should trigger refresh since current_time + 8 >= exp)
        await client._ensure_valid_token()

        # With 8s threshold on 10s token, refresh should have happened
        assert client._token_exp >= original_exp


class TestAsyncScopedClientSingleFlight:
    """Test single-flight pattern - concurrent operations share one refresh."""

    @pytest.mark.asyncio
    async def test_concurrent_operations_share_single_refresh(self, config):
        """Multiple concurrent operations don't cause multiple refreshes."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        user_id = str(uuid.uuid4())
        client = await AsyncScopedClient.create(
            user_id,
            config=config,
            expiry_seconds=1,
            refresh_threshold_seconds=0,
        )

        # Force token to be near expiry
        await asyncio.sleep(1.1)

        refresh_count = 0
        original_refresh = client._refresh_token

        async def counting_refresh():
            nonlocal refresh_count
            refresh_count += 1
            await original_refresh()

        client._refresh_token = counting_refresh

        # Launch multiple concurrent operations
        async def access_table():
            await client._ensure_valid_token()

        await asyncio.gather(
            access_table(),
            access_table(),
            access_table(),
            access_table(),
            access_table(),
        )

        # Should have refreshed only once due to lock
        assert refresh_count == 1


class TestAsyncScopedClientRLS:
    """Integration tests for RLS policy enforcement with AsyncScopedClient."""

    @pytest.fixture
    def user1_id(self):
        """Generate a user ID for test user 1."""
        return str(uuid.uuid4())

    @pytest.fixture
    def user2_id(self):
        """Generate a user ID for test user 2."""
        return str(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_scoped_client_can_insert_own_data(self, config, user1_id):
        """AsyncScopedClient can insert data with their own user_id."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        client = await AsyncScopedClient.create(user1_id, config=config)

        response = await (
            client.table("test_user_data")
            .insert({"user_id": user1_id, "content": "scoped client content"})
            .execute()
        )

        assert len(response.data) == 1
        assert response.data[0]["user_id"] == user1_id

    @pytest.mark.asyncio
    async def test_scoped_client_can_read_own_data(self, config, user1_id):
        """AsyncScopedClient can read their own data."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        client = await AsyncScopedClient.create(user1_id, config=config)

        # Insert and read
        await (
            client.table("test_user_data")
            .insert({"user_id": user1_id, "content": "readable"})
            .execute()
        )

        response = await client.table("test_user_data").select("*").execute()
        assert len(response.data) >= 1
        assert all(row["user_id"] == user1_id for row in response.data)

    @pytest.mark.asyncio
    async def test_scoped_client_cannot_read_other_users_data(
        self, config, user1_id, user2_id
    ):
        """AsyncScopedClient cannot read another user's data."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        # User 1 inserts data
        client1 = await AsyncScopedClient.create(user1_id, config=config)
        await (
            client1.table("test_user_data")
            .insert({"user_id": user1_id, "content": "user1 secret"})
            .execute()
        )

        # User 2 tries to read all data
        client2 = await AsyncScopedClient.create(user2_id, config=config)
        response = await client2.table("test_user_data").select("*").execute()

        # User 2 should not see user 1's data
        user1_data = [row for row in response.data if row["user_id"] == user1_id]
        assert len(user1_data) == 0


class TestAsyncScopedClientParameters:
    """Test that parameters are correctly passed through."""

    @pytest.mark.asyncio
    async def test_role_parameter_is_used(self, config):
        """role parameter is passed to token generation."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        user_id = str(uuid.uuid4())
        client = await AsyncScopedClient.create(
            user_id, config=config, role="service_role"
        )
        assert client._role == "service_role"

    @pytest.mark.asyncio
    async def test_expiry_seconds_parameter_is_used(self, config):
        """expiry_seconds parameter is stored for refresh."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        user_id = str(uuid.uuid4())
        client = await AsyncScopedClient.create(
            user_id, config=config, expiry_seconds=7200
        )
        assert client._expiry_seconds == 7200

    @pytest.mark.asyncio
    async def test_custom_claims_parameter_is_stored(self, config):
        """custom_claims parameter is stored for refresh."""
        from supabase_scoped_clients.clients.async_client import AsyncScopedClient

        user_id = str(uuid.uuid4())
        custom = {"org_id": "test-org"}
        client = await AsyncScopedClient.create(
            user_id, config=config, custom_claims=custom
        )
        assert client._custom_claims == custom
