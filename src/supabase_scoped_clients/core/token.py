"""JWT token generation for Supabase-compatible user impersonation."""

from datetime import datetime, timezone
from typing import Any

import jwt as pyjwt

from .config import Config
from .exceptions import TokenError


def generate_token(
    config: Config,
    user_id: str,
    *,
    role: str = "authenticated",
    expiry_seconds: int = 3600,
    custom_claims: dict[str, Any] | None = None,
) -> str:
    """Generate a Supabase-compatible JWT token for user impersonation.

    Args:
        config: Configuration containing the JWT secret and Supabase URL.
        user_id: The UUID of the user to impersonate.
        role: The Supabase role for the token (default: "authenticated").
        expiry_seconds: Token validity in seconds (default: 3600 = 1 hour).
        custom_claims: Additional claims to include in the token.

    Returns:
        A signed JWT token string.

    Raises:
        TokenError: If user_id is empty or expiry_seconds is not positive.
    """
    if not user_id or not user_id.strip():
        raise TokenError("user_id cannot be empty")

    if expiry_seconds <= 0:
        raise TokenError("expiry must be positive")

    now = datetime.now(tz=timezone.utc)
    iat = int(now.timestamp())
    exp = iat + expiry_seconds

    payload: dict[str, Any] = {}

    if custom_claims:
        payload.update(custom_claims)

    payload.update(
        {
            "sub": user_id,
            "role": role,
            "aud": "authenticated",
            "iss": f"{config.supabase_url}/auth/v1",
            "iat": iat,
            "exp": exp,
        }
    )

    return pyjwt.encode(payload, config.supabase_jwt_secret, algorithm="HS256")
