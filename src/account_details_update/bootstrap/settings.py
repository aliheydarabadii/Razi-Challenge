"""Application settings loaded from environment variables and .env file."""

from __future__ import annotations

from pydantic import Field, SecretStr, field_validator
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
    password: SecretStr = Field(
        default=SecretStr("Password123!"), alias="CHALLENGE_PASSWORD"
    )
    mfa_code: SecretStr = Field(default=SecretStr("1234"), alias="MFA_CODE")
    headed: bool = Field(default=False, alias="HEADED")
    slow_mo_ms: int = Field(default=0, alias="SLOW_MO_MS")

    supabase_url: str = Field(
        default="https://zvyhufnwclhcvmgtqxwp.supabase.co",
        alias="SUPABASE_URL",
    )
    supabase_anon_key: SecretStr = Field(
        default=SecretStr(""),
        alias="SUPABASE_ANON_KEY",
    )

    bank_routing: str = Field(default="123456789", alias="BANK_ROUTING")
    bank_account: str = Field(default="1234567890", alias="BANK_ACCOUNT")
    cardholder_name: str = Field(default="Test Candidate", alias="CARDHOLDER_NAME")
    card_number: str = Field(default="4242424242424242", alias="CARD_NUMBER")
    card_expiry_month: str = Field(default="12", alias="CARD_EXPIRY_MONTH")
    card_expiry_year: str = Field(default="2035", alias="CARD_EXPIRY_YEAR")
    card_cvc: str = Field(default="123", alias="CARD_CVC")

    @field_validator("challenge_base_url", "api_base_url", "supabase_url")
    @classmethod
    def must_be_http_url(cls, v: str) -> str:
        if v and not v.lower().startswith(("http://", "https://")):
            raise ValueError(f"must start with http:// or https://, got: {v!r}")
        return v


def load_settings() -> Settings:
    """Load settings from environment variables and optional .env file."""

    return Settings()
