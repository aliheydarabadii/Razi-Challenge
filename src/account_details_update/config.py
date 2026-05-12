"""Runtime configuration for future browser and API adapters."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings for the challenge sandbox."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    challenge_base_url: str = Field(
        default="https://marketplace.dev-challenge.com",
        alias="CHALLENGE_BASE_URL",
    )
    api_base_url: str = Field(
        default="https://zvyhufnwclhcvmgtqxwp.supabase.co/functions/v1/api-v1",
        alias="API_BASE_URL",
    )
    username: str = Field(
        default="candidate@dev-challenge.com",
        alias="CHALLENGE_USERNAME",
    )
    password: str = Field(default="Password123!", alias="CHALLENGE_PASSWORD")
    mfa_code: str = Field(default="000000", alias="MFA_CODE")
    headed: bool = Field(default=False, alias="HEADED")
    slow_mo_ms: int = Field(default=0, alias="SLOW_MO_MS")


def load_settings() -> Settings:
    """Load settings from environment variables and optional .env file."""

    return Settings()
