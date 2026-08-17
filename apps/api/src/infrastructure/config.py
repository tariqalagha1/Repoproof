"""Application configuration — pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -- database --
    database_url: str = "sqlite+aiosqlite:///./repoproof.db"

    # -- llm --
    llm_provider: str = "fake"
    llm_model: str = ""
    llm_api_key: str = ""
    llm_base_url: str = ""

    # -- runner --
    runner_provider: str = "fake"

    # -- auth --
    dev_auth_token: str = ""
    secret_key: str = "change-me-in-production"

    # -- app --
    debug: bool = False
    log_level: str = "INFO"

    def redacted_dict(self) -> dict[str, str]:
        """Return a dict suitable for logging (api_key masked)."""
        d = self.model_dump()
        if d.get("llm_api_key"):
            d["llm_api_key"] = "***"
        return d

    def llm_is_configured(self) -> bool:
        return bool(self.llm_provider and self.llm_provider != "fake")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
