from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from hirewire.config.paths import BASE_DIR, CREDENTIALS_DIR
from hirewire.integrations.hhru.settings import HHRUSettings


class GoogleSettings(BaseModel):
    """Configuration for the optional Google Workspace integration."""

    folder_id: str | None = None
    spreadsheet_id: str | None = None
    oauth_client_file: Path = CREDENTIALS_DIR / "oauth-client.json"
    token_file: Path = CREDENTIALS_DIR / "token.json"

    @field_validator("folder_id", "spreadsheet_id", mode="before")
    @classmethod
    def normalize_optional_ids(cls, value: str | None) -> str | None:
        """Treat unset/blank IDs as absent, not as valid empty identifiers."""
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class Settings(BaseSettings):
    """Validated application configuration loaded from environment sources."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        env_prefix="HIREWIRE_",
        extra="ignore",
        validate_default=True,
    )
    environment: Literal["development", "testing", "production"] = (
        "development"
    )
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = (
        "INFO"
    )
    google: GoogleSettings = Field(default_factory=GoogleSettings)
    hhru: HHRUSettings = Field(default_factory=HHRUSettings)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide cached settings instance."""
    return Settings()
