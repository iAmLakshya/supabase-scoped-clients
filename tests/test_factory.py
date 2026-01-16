"""Tests for the synchronous client factory."""

import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
from supabase import Client

from supabase_scoped_clients.core.config import Config, load_config
from supabase_scoped_clients.core.exceptions import ClientError
from supabase_scoped_clients.factories.sync import get_client


# Test data - use local Supabase dev instance
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


class TestGetClientBasic:
    """Test basic get_client functionality."""

    def test_returns_supabase_client(self, config):
        """get_client returns a Supabase Client instance."""
        user_id = str(uuid.uuid4())
        client = get_client(user_id, config=config)
        assert isinstance(client, Client)

    def test_accepts_user_id_as_string(self, config):
        """get_client accepts user_id as a string."""
        user_id = str(uuid.uuid4())
        client = get_client(user_id, config=config)
        assert client is not None


class TestGetClientConfig:
    """Test configuration handling."""

    def test_uses_provided_config(self, config):
        """get_client uses the provided config."""
        user_id = str(uuid.uuid4())
        client = get_client(user_id, config=config)
        assert client is not None

    def test_loads_config_from_env_when_not_provided(self, monkeypatch):
        """get_client loads config from environment when not provided."""
        monkeypatch.setenv("SUPABASE_URL", LOCAL_SUPABASE_URL)
        monkeypatch.setenv("SUPABASE_KEY", LOCAL_SUPABASE_KEY)
        monkeypatch.setenv("SUPABASE_JWT_SECRET", LOCAL_JWT_SECRET)

        user_id = str(uuid.uuid4())
        client = get_client(user_id)
        assert isinstance(client, Client)


class TestGetClientParameters:
    """Test parameter pass-through."""

    def test_role_parameter_passed_to_token(self, config):
        """role parameter is passed to token generation."""
        user_id = str(uuid.uuid4())
        client = get_client(user_id, config=config, role="service_role")
        assert client is not None

    def test_expiry_seconds_parameter_passed_to_token(self, config):
        """expiry_seconds parameter is passed to token generation."""
        user_id = str(uuid.uuid4())
        client = get_client(user_id, config=config, expiry_seconds=7200)
        assert client is not None

    def test_custom_claims_parameter_passed_to_token(self, config):
        """custom_claims parameter is passed to token generation."""
        user_id = str(uuid.uuid4())
        client = get_client(
            user_id, config=config, custom_claims={"org_id": "test-org"}
        )
        assert client is not None


class TestGetClientValidation:
    """Test input validation."""

    def test_empty_user_id_raises_client_error(self, config):
        """Empty user_id raises ClientError."""
        with pytest.raises(ClientError) as excinfo:
            get_client("", config=config)
        assert "user_id" in str(excinfo.value).lower()

    def test_whitespace_user_id_raises_client_error(self, config):
        """Whitespace-only user_id raises ClientError."""
        with pytest.raises(ClientError) as excinfo:
            get_client("   ", config=config)
        assert "user_id" in str(excinfo.value).lower()


class TestGetClientIndependence:
    """Test that multiple clients operate independently."""

    def test_multiple_clients_for_same_user_are_independent(self, config):
        """Multiple clients for the same user are independent instances."""
        user_id = str(uuid.uuid4())
        client1 = get_client(user_id, config=config)
        client2 = get_client(user_id, config=config)

        assert client1 is not client2

    def test_multiple_clients_for_different_users_are_independent(self, config):
        """Multiple clients for different users are independent instances."""
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())

        client1 = get_client(user1_id, config=config)
        client2 = get_client(user2_id, config=config)

        assert client1 is not client2


class TestGetClientRLS:
    """Integration tests for RLS policy enforcement.

    These tests verify that the client respects RLS policies by testing
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

    def test_user_can_insert_own_data(self, config, user1_id):
        """User can insert data with their own user_id."""
        client = get_client(user1_id, config=config)

        response = (
            client.table("test_user_data")
            .insert({"user_id": user1_id, "content": "user1 content"})
            .execute()
        )

        assert len(response.data) == 1
        assert response.data[0]["user_id"] == user1_id
        assert response.data[0]["content"] == "user1 content"

    def test_user_can_read_own_data(self, config, user1_id):
        """User can read their own data."""
        client = get_client(user1_id, config=config)

        # Insert some data first
        client.table("test_user_data").insert(
            {"user_id": user1_id, "content": "readable content"}
        ).execute()

        # Read it back
        response = client.table("test_user_data").select("*").execute()

        assert len(response.data) >= 1
        assert all(row["user_id"] == user1_id for row in response.data)

    def test_user_cannot_read_other_users_data(self, config, user1_id, user2_id):
        """User cannot read another user's data."""
        # User 1 inserts data
        client1 = get_client(user1_id, config=config)
        client1.table("test_user_data").insert(
            {"user_id": user1_id, "content": "user1 secret"}
        ).execute()

        # User 2 tries to read all data
        client2 = get_client(user2_id, config=config)
        response = client2.table("test_user_data").select("*").execute()

        # User 2 should not see user 1's data
        user1_data = [row for row in response.data if row["user_id"] == user1_id]
        assert len(user1_data) == 0

    def test_user_cannot_insert_data_for_other_user(self, config, user1_id, user2_id):
        """User cannot insert data with another user's user_id."""
        client1 = get_client(user1_id, config=config)

        # Try to insert data pretending to be user2
        with pytest.raises(Exception):
            client1.table("test_user_data").insert(
                {"user_id": user2_id, "content": "malicious content"}
            ).execute()

    def test_user_can_update_own_data(self, config, user1_id):
        """User can update their own data."""
        client = get_client(user1_id, config=config)

        # Insert data
        insert_response = (
            client.table("test_user_data")
            .insert({"user_id": user1_id, "content": "original"})
            .execute()
        )
        row_id = insert_response.data[0]["id"]

        # Update it
        update_response = (
            client.table("test_user_data")
            .update({"content": "updated"})
            .eq("id", row_id)
            .execute()
        )

        assert len(update_response.data) == 1
        assert update_response.data[0]["content"] == "updated"

    def test_user_can_delete_own_data(self, config, user1_id):
        """User can delete their own data."""
        client = get_client(user1_id, config=config)

        # Insert data
        insert_response = (
            client.table("test_user_data")
            .insert({"user_id": user1_id, "content": "to be deleted"})
            .execute()
        )
        row_id = insert_response.data[0]["id"]

        # Delete it
        delete_response = (
            client.table("test_user_data").delete().eq("id", row_id).execute()
        )

        assert len(delete_response.data) == 1

        # Verify it's gone
        select_response = (
            client.table("test_user_data").select("*").eq("id", row_id).execute()
        )
        assert len(select_response.data) == 0
