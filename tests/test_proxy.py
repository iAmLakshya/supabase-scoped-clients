"""Tests for TokenRefreshProxy with automatic token refresh."""

from typing import Any

import pytest

from supabase_scoped_clients.infrastructure.proxy import (
    AsyncTokenManager,
    TokenManager,
    TokenRefreshProxy,
    create_proxy,
)


class MockTokenManager:
    """Sync token manager for testing."""

    def __init__(self) -> None:
        self.refresh_count = 0

    def ensure_valid_token(self) -> None:
        self.refresh_count += 1


class MockAsyncTokenManager:
    """Async token manager for testing."""

    def __init__(self) -> None:
        self.refresh_count = 0

    async def ensure_valid_token(self) -> None:
        self.refresh_count += 1


class MockTable:
    """Mock table class for testing method chaining."""

    def select(self, columns: str) -> "MockQuery":
        return MockQuery(columns)


class MockQuery:
    """Mock query class for testing method chaining."""

    def __init__(self, columns: str) -> None:
        self.columns = columns

    def execute(self) -> dict[str, Any]:
        return {"data": [{"id": 1}], "columns": self.columns}


class MockAsyncTable:
    """Mock async table class for testing method chaining."""

    def select(self, columns: str) -> "MockAsyncQuery":
        return MockAsyncQuery(columns)


class MockAsyncQuery:
    """Mock async query class for testing method chaining."""

    def __init__(self, columns: str) -> None:
        self.columns = columns

    async def execute(self) -> dict[str, Any]:
        return {"data": [{"id": 1}], "columns": self.columns}


class MockClient:
    """Mock Supabase client for testing."""

    def __init__(self) -> None:
        self.name = "test_client"
        self.count = 42

    def table(self, name: str) -> MockTable:
        return MockTable()

    @property
    def storage(self) -> str:
        return "storage_client"


class MockAsyncClient:
    """Mock async Supabase client for testing."""

    def __init__(self) -> None:
        self.name = "async_test_client"
        self.count = 42

    def table(self, name: str) -> MockAsyncTable:
        return MockAsyncTable()

    async def rpc(self, fn_name: str) -> dict[str, Any]:
        return {"result": fn_name}

    @property
    def storage(self) -> str:
        return "async_storage_client"


class TestTokenRefreshProxySync:
    """Test TokenRefreshProxy with synchronous clients."""

    def test_sync_method_calls_ensure_valid_token(self) -> None:
        """Sync methods should call ensure_valid_token before execution."""
        manager = MockTokenManager()
        client = MockClient()
        proxy = TokenRefreshProxy(client, manager)

        proxy.table("test")

        assert manager.refresh_count == 1

    def test_sync_method_returns_proxied_result(self) -> None:
        """Sync methods should return proxied results for chaining."""
        manager = MockTokenManager()
        client = MockClient()
        proxy = TokenRefreshProxy(client, manager)

        result = proxy.table("test")

        assert isinstance(result, TokenRefreshProxy)

    def test_primitive_property_not_proxied(self) -> None:
        """Primitive values should be returned directly, not proxied."""
        manager = MockTokenManager()
        client = MockClient()
        proxy = TokenRefreshProxy(client, manager)

        name = proxy.name
        count = proxy.count

        assert name == "test_client"
        assert count == 42
        assert not isinstance(name, TokenRefreshProxy)
        assert not isinstance(count, TokenRefreshProxy)

    def test_method_chain_works(self) -> None:
        """Method chains like table().select().execute() should work."""
        manager = MockTokenManager()
        client = MockClient()
        proxy = TokenRefreshProxy(client, manager)

        result = proxy.table("test").select("*").execute()

        assert result == {"data": [{"id": 1}], "columns": "*"}
        assert manager.refresh_count == 3


class TestTokenRefreshProxyAsync:
    """Test TokenRefreshProxy with asynchronous clients."""

    @pytest.mark.asyncio
    async def test_async_method_calls_ensure_valid_token(self) -> None:
        """Async methods should call ensure_valid_token before execution."""
        manager = MockAsyncTokenManager()
        client = MockAsyncClient()
        proxy = TokenRefreshProxy(client, manager)

        await proxy.rpc("test_fn")

        assert manager.refresh_count == 1

    @pytest.mark.asyncio
    async def test_async_method_chain_works(self) -> None:
        """Async method chains like table().select().execute() should work."""
        manager = MockAsyncTokenManager()
        client = MockAsyncClient()
        proxy = TokenRefreshProxy(client, manager)

        result = await proxy.table("test").select("*").execute()

        assert result == {"data": [{"id": 1}], "columns": "*"}

    @pytest.mark.asyncio
    async def test_async_primitive_property_not_proxied(self) -> None:
        """Primitive values should be returned directly with async manager."""
        manager = MockAsyncTokenManager()
        client = MockAsyncClient()
        proxy = TokenRefreshProxy(client, manager)

        name = proxy.name
        count = proxy.count

        assert name == "async_test_client"
        assert count == 42
        assert not isinstance(name, TokenRefreshProxy)
        assert not isinstance(count, TokenRefreshProxy)


class TestCreateProxyFactory:
    """Test the create_proxy factory function."""

    def test_create_proxy_returns_typed_proxy(self) -> None:
        """create_proxy should return a proxy that works like the original type."""
        manager = MockTokenManager()
        client = MockClient()

        proxy = create_proxy(client, manager)

        assert proxy.table("test") is not None
        assert proxy.name == "test_client"

    def test_create_proxy_type_casting(self) -> None:
        """create_proxy should preserve type for IDE support."""
        manager = MockTokenManager()
        client = MockClient()

        proxy = create_proxy(client, manager)

        assert isinstance(proxy, TokenRefreshProxy)


class TestProtocolCompliance:
    """Test that protocols work correctly."""

    def test_sync_token_manager_protocol(self) -> None:
        """MockTokenManager should satisfy TokenManager protocol."""
        manager = MockTokenManager()
        assert isinstance(manager, TokenManager)

    def test_async_token_manager_protocol(self) -> None:
        """MockAsyncTokenManager should satisfy AsyncTokenManager protocol."""
        manager = MockAsyncTokenManager()
        assert isinstance(manager, AsyncTokenManager)


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_property_access_proxied_if_not_primitive(self) -> None:
        """Non-primitive properties should be proxied."""

        class ComplexClient:
            @property
            def nested(self) -> dict[str, Any]:
                return {"key": "value"}

        manager = MockTokenManager()
        client = ComplexClient()
        proxy = TokenRefreshProxy(client, manager)

        nested = proxy.nested

        assert nested == {"key": "value"}
        assert not isinstance(nested, TokenRefreshProxy)

    def test_proxy_repr(self) -> None:
        """TokenRefreshProxy should have a useful repr."""
        manager = MockTokenManager()
        client = MockClient()
        proxy = TokenRefreshProxy(client, manager)

        repr_str = repr(proxy)

        assert "TokenRefreshProxy" in repr_str

    def test_list_result_not_proxied(self) -> None:
        """List results should not be proxied."""

        class ListClient:
            def get_items(self) -> list[int]:
                return [1, 2, 3]

        manager = MockTokenManager()
        client = ListClient()
        proxy = TokenRefreshProxy(client, manager)

        result = proxy.get_items()

        assert result == [1, 2, 3]
        assert not isinstance(result, TokenRefreshProxy)

    def test_dict_result_not_proxied(self) -> None:
        """Dict results should not be proxied."""

        class DictClient:
            def get_data(self) -> dict[str, int]:
                return {"a": 1, "b": 2}

        manager = MockTokenManager()
        client = DictClient()
        proxy = TokenRefreshProxy(client, manager)

        result = proxy.get_data()

        assert result == {"a": 1, "b": 2}
        assert not isinstance(result, TokenRefreshProxy)

    def test_none_result_not_proxied(self) -> None:
        """None results should not be proxied."""

        class NoneClient:
            def get_nothing(self) -> None:
                return None

        manager = MockTokenManager()
        client = NoneClient()
        proxy = TokenRefreshProxy(client, manager)

        result = proxy.get_nothing()

        assert result is None


class TestSyncManagerWithSyncMethod:
    """Test sync token manager with sync methods."""

    def test_ensure_valid_token_called_once_per_method(self) -> None:
        """Each sync method call should trigger ensure_valid_token once."""
        manager = MockTokenManager()
        client = MockClient()
        proxy = TokenRefreshProxy(client, manager)

        proxy.table("test1")
        proxy.table("test2")
        proxy.table("test3")

        assert manager.refresh_count == 3


class TestAsyncManagerWithMixedMethods:
    """Test async token manager with mixed sync/async methods."""

    @pytest.mark.asyncio
    async def test_sync_method_with_async_manager_no_refresh(self) -> None:
        """Sync methods should not call async ensure_valid_token."""
        manager = MockAsyncTokenManager()
        client = MockAsyncClient()
        proxy = TokenRefreshProxy(client, manager)

        proxy.table("test")

        assert manager.refresh_count == 0

    @pytest.mark.asyncio
    async def test_async_method_with_async_manager_refreshes(self) -> None:
        """Async methods should call async ensure_valid_token."""
        manager = MockAsyncTokenManager()
        client = MockAsyncClient()
        proxy = TokenRefreshProxy(client, manager)

        await proxy.rpc("test")

        assert manager.refresh_count == 1
