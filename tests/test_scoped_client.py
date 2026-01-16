"""Tests for the ScopedClient wrapper with auto-refresh."""

import threading
import time
import uuid

import pytest

from supabase_scoped_clients.clients.sync import ScopedClient


class TestScopedClientCreation:
    """Test ScopedClient initialization."""

    def test_creates_scoped_client(self, config):
        """ScopedClient can be created with user_id and config."""
        user_id = str(uuid.uuid4())
        scoped_client = ScopedClient(user_id, config)
        assert scoped_client is not None

    def test_accepts_all_parameters(self, config):
        """ScopedClient accepts all configuration parameters."""
        user_id = str(uuid.uuid4())
        scoped_client = ScopedClient(
            user_id,
            config,
            role="authenticated",
            expiry_seconds=3600,
            custom_claims={"org_id": "test-org"},
            refresh_threshold_seconds=60,
        )
        assert scoped_client is not None


class TestTokenRefresh:
    """Test automatic token refresh behavior."""

    def test_no_refresh_when_token_valid(self, config):
        """Token is not refreshed when still valid."""
        user_id = str(uuid.uuid4())
        scoped_client = ScopedClient(
            user_id,
            config,
            expiry_seconds=3600,
            refresh_threshold_seconds=60,
        )

        refresh_count = [0]
        original_create = scoped_client._create_client

        def counting_create():
            refresh_count[0] += 1
            original_create()

        scoped_client._create_client = counting_create

        # Access storage (should not trigger refresh - token still valid)
        _ = scoped_client.storage

        assert refresh_count[0] == 0

    def test_refresh_when_token_near_expiry(self, config):
        """Token is refreshed when approaching expiry."""
        user_id = str(uuid.uuid4())
        scoped_client = ScopedClient(
            user_id,
            config,
            expiry_seconds=3600,
            refresh_threshold_seconds=60,
        )

        refresh_count = [0]
        original_create = scoped_client._create_client

        def counting_create():
            refresh_count[0] += 1
            original_create()

        scoped_client._create_client = counting_create

        # Simulate token being near expiry by setting exp to past
        scoped_client._token_exp = int(time.time()) - 1

        # Access storage (should trigger refresh)
        _ = scoped_client.storage

        assert refresh_count[0] == 1

    def test_refresh_threshold_is_configurable(self, config):
        """Refresh threshold can be configured."""
        user_id = str(uuid.uuid4())
        threshold = 120

        scoped_client = ScopedClient(
            user_id,
            config,
            expiry_seconds=3600,
            refresh_threshold_seconds=threshold,
        )

        refresh_count = [0]
        original_create = scoped_client._create_client

        def counting_create():
            refresh_count[0] += 1
            original_create()

        scoped_client._create_client = counting_create

        # Set token to expire within threshold
        scoped_client._token_exp = int(time.time()) + threshold - 1

        # Access storage (should trigger refresh due to threshold)
        _ = scoped_client.storage

        assert refresh_count[0] == 1


class TestSingleFlightRefresh:
    """Test that concurrent operations share one refresh."""

    def test_concurrent_operations_single_refresh(self, config):
        """Multiple concurrent operations don't cause multiple refreshes."""
        user_id = str(uuid.uuid4())
        scoped_client = ScopedClient(
            user_id,
            config,
            expiry_seconds=3600,
            refresh_threshold_seconds=60,
        )

        refresh_count = [0]
        original_create = scoped_client._create_client

        def counting_create():
            refresh_count[0] += 1
            original_create()

        scoped_client._create_client = counting_create

        # Force token to need refresh
        scoped_client._token_exp = int(time.time()) - 1

        # Launch multiple threads accessing the client (using storage property)
        threads = []
        for _ in range(5):
            t = threading.Thread(target=lambda: scoped_client.storage)
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should only have one refresh despite 5 concurrent accesses
        assert refresh_count[0] == 1


class TestClientDelegation:
    """Test that all Client operations delegate correctly."""

    def test_table_property_delegates(self, config):
        """table property delegates to underlying client."""
        user_id = str(uuid.uuid4())
        scoped_client = ScopedClient(user_id, config)

        table = scoped_client.table("test_user_data")
        assert table is not None

    def test_storage_property_delegates(self, config):
        """storage property delegates to underlying client."""
        user_id = str(uuid.uuid4())
        scoped_client = ScopedClient(user_id, config)

        storage = scoped_client.storage
        assert storage is not None

    def test_functions_property_delegates(self, config):
        """functions property delegates to underlying client."""
        user_id = str(uuid.uuid4())
        scoped_client = ScopedClient(user_id, config)

        functions = scoped_client.functions
        assert functions is not None

    def test_rpc_method_delegates(self, config):
        """rpc method delegates to underlying client."""
        user_id = str(uuid.uuid4())
        scoped_client = ScopedClient(user_id, config)

        # RPC method should be callable
        assert callable(scoped_client.rpc)


class TestScopedClientRLS:
    """Integration tests for RLS through ScopedClient."""

    @pytest.fixture
    def user1_id(self):
        """Generate a user ID for test user 1."""
        return str(uuid.uuid4())

    @pytest.fixture
    def user2_id(self):
        """Generate a user ID for test user 2."""
        return str(uuid.uuid4())

    def test_user_can_insert_own_data(self, config, user1_id):
        """User can insert data through ScopedClient."""
        scoped_client = ScopedClient(user1_id, config)

        response = (
            scoped_client.table("test_user_data")
            .insert({"user_id": user1_id, "content": "scoped content"})
            .execute()
        )

        assert len(response.data) == 1
        assert response.data[0]["user_id"] == user1_id

    def test_user_can_read_own_data(self, config, user1_id):
        """User can read their own data through ScopedClient."""
        scoped_client = ScopedClient(user1_id, config)

        # Insert data
        scoped_client.table("test_user_data").insert(
            {"user_id": user1_id, "content": "readable"}
        ).execute()

        # Read it back
        response = scoped_client.table("test_user_data").select("*").execute()

        assert len(response.data) >= 1
        assert all(row["user_id"] == user1_id for row in response.data)

    def test_rls_isolation_between_users(self, config, user1_id, user2_id):
        """ScopedClient maintains RLS isolation between users."""
        client1 = ScopedClient(user1_id, config)
        client2 = ScopedClient(user2_id, config)

        # User 1 inserts data
        client1.table("test_user_data").insert(
            {"user_id": user1_id, "content": "user1 secret"}
        ).execute()

        # User 2 can't see user 1's data
        response = client2.table("test_user_data").select("*").execute()
        user1_data = [row for row in response.data if row["user_id"] == user1_id]
        assert len(user1_data) == 0


class TestRefreshDuringOperations:
    """Test that refresh works correctly during actual operations."""

    def test_operation_succeeds_after_refresh(self, config):
        """Operations succeed even when token needs refresh."""
        user_id = str(uuid.uuid4())
        scoped_client = ScopedClient(
            user_id,
            config,
            expiry_seconds=3600,
            refresh_threshold_seconds=60,
        )

        # Force token to need refresh
        scoped_client._token_exp = int(time.time()) - 1

        # Operation should still succeed
        response = (
            scoped_client.table("test_user_data")
            .insert({"user_id": user_id, "content": "after refresh"})
            .execute()
        )

        assert len(response.data) == 1
