"""Shared pytest fixtures for all tests."""

import os

import pytest

from supabase_scoped_clients.core.config import Config

# Default values for local Supabase development
DEFAULT_SUPABASE_URL = "http://127.0.0.1:54331"
DEFAULT_SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9."
    "CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
)
DEFAULT_JWT_SECRET = "super-secret-jwt-token-with-at-least-32-characters-long"


@pytest.fixture
def supabase_url() -> str:
    """Get Supabase URL from environment or use default."""
    return os.environ.get("SUPABASE_URL", DEFAULT_SUPABASE_URL)


@pytest.fixture
def supabase_key() -> str:
    """Get Supabase key from environment or use default."""
    return os.environ.get("SUPABASE_KEY", DEFAULT_SUPABASE_KEY)


@pytest.fixture
def supabase_jwt_secret() -> str:
    """Get Supabase JWT secret from environment or use default."""
    return os.environ.get("SUPABASE_JWT_SECRET", DEFAULT_JWT_SECRET)


@pytest.fixture
def config(supabase_url: str, supabase_key: str, supabase_jwt_secret: str) -> Config:
    """Create a test config using environment variables or defaults."""
    return Config(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        supabase_jwt_secret=supabase_jwt_secret,
    )
