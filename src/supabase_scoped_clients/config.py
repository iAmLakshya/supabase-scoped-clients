"""Configuration class for supabase_scoped_clients."""

from pydantic import Field, HttpUrl, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import ConfigurationError


class Config(BaseSettings):
    """Configuration for supabase_scoped_clients.

    Loads from environment variables:
    - SUPABASE_URL
    - SUPABASE_KEY
    - SUPABASE_JWT_SECRET

    Can be overridden programmatically via constructor kwargs.
    """

    supabase_url: HttpUrl = Field(validation_alias="SUPABASE_URL")
    supabase_key: str = Field(validation_alias="SUPABASE_KEY")
    supabase_jwt_secret: str = Field(validation_alias="SUPABASE_JWT_SECRET")

    model_config = SettingsConfigDict(
        populate_by_name=True,
    )

    @field_validator("supabase_key", "supabase_jwt_secret")
    @classmethod
    def not_empty(cls, v: str, info: object) -> str:
        if not v or not v.strip():
            field_name = getattr(info, "field_name", "field")
            raise ValueError(f"{field_name} cannot be empty")
        return v


# Mapping from env var names (aliases) to field names
_ALIAS_TO_FIELD = {
    "SUPABASE_URL": "supabase_url",
    "SUPABASE_KEY": "supabase_key",
    "SUPABASE_JWT_SECRET": "supabase_jwt_secret",
}


def load_config(**kwargs: object) -> Config:
    """Load configuration, converting Pydantic errors to ConfigurationError.

    Args:
        **kwargs: Override configuration values programmatically.

    Returns:
        Config instance.

    Raises:
        ConfigurationError: If configuration is invalid.
    """
    try:
        return Config(**kwargs)  # type: ignore[arg-type]
    except ValidationError as e:
        error = e.errors()[0]
        raw_field = str(error["loc"][0]) if error["loc"] else "unknown"
        field_name = _ALIAS_TO_FIELD.get(raw_field, raw_field)
        reason = error["msg"]
        raise ConfigurationError(field_name, reason) from e
