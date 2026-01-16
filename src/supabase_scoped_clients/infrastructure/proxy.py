"""TokenRefreshProxy for automatic token refresh with type preservation."""

import inspect
from typing import Any, Protocol, TypeVar, cast, runtime_checkable

T = TypeVar("T")

_PRIMITIVES = (str, int, float, bool, bytes, type(None), list, dict, tuple, set)


@runtime_checkable
class TokenManager(Protocol):
    """Protocol for synchronous token managers."""

    def ensure_valid_token(self) -> None:
        """Ensure the token is valid, refreshing if necessary."""
        ...


@runtime_checkable
class AsyncTokenManager(Protocol):
    """Protocol for asynchronous token managers."""

    async def ensure_valid_token(self) -> None:
        """Ensure the token is valid, refreshing if necessary."""
        ...


class TokenRefreshProxy:
    """Proxy that intercepts attribute access to handle automatic token refresh.

    Works with both sync and async clients by detecting method types at runtime.
    For async methods, it wraps them to call ensure_valid_token() before execution.
    For sync methods, it wraps them to return proxied results for method chaining.
    """

    __slots__ = ("_target", "_token_manager", "_is_async_manager")

    def __init__(
        self,
        target: Any,
        token_manager: TokenManager | AsyncTokenManager,
    ) -> None:
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_token_manager", token_manager)
        object.__setattr__(
            self,
            "_is_async_manager",
            inspect.iscoroutinefunction(token_manager.ensure_valid_token),
        )

    def __getattr__(self, name: str) -> Any:
        target = object.__getattribute__(self, "_target")
        attr = getattr(target, name)

        if callable(attr):
            return self._wrap_callable(attr)

        if isinstance(attr, _PRIMITIVES):
            return attr

        token_manager = object.__getattribute__(self, "_token_manager")
        return TokenRefreshProxy(attr, token_manager)

    def _wrap_callable(self, func: Any) -> Any:
        """Wrap a callable to handle token refresh appropriately."""
        token_manager = object.__getattribute__(self, "_token_manager")
        is_async_manager = object.__getattribute__(self, "_is_async_manager")

        if inspect.iscoroutinefunction(func):

            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                if is_async_manager:
                    await token_manager.ensure_valid_token()
                result = await func(*args, **kwargs)
                if isinstance(result, _PRIMITIVES):
                    return result
                return TokenRefreshProxy(result, token_manager)

            return async_wrapper

        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            if not is_async_manager:
                token_manager.ensure_valid_token()
            result = func(*args, **kwargs)
            if isinstance(result, _PRIMITIVES):
                return result
            return TokenRefreshProxy(result, token_manager)

        return sync_wrapper

    def __repr__(self) -> str:
        target = object.__getattribute__(self, "_target")
        return f"TokenRefreshProxy({target!r})"


def create_proxy(client: T, token_manager: TokenManager | AsyncTokenManager) -> T:
    """Create a token-refreshing proxy that preserves the client's type for IDE support.

    Args:
        client: The Supabase client to wrap.
        token_manager: Object implementing ensure_valid_token() method.

    Returns:
        A proxy that looks like the original client type to IDEs/type checkers,
        but intercepts calls to handle automatic token refresh.
    """
    return cast(T, TokenRefreshProxy(client, token_manager))
