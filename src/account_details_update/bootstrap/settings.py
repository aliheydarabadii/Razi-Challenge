"""Application settings loaded from environment variables and .env file."""

from __future__ import annotations

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_CHALLENGE_URL = "https://marketplace.dev-challenge.com"
_DEFAULT_API_URL = "https://zvyhufnwclhcvmgtqxwp.supabase.co/functions/v1/api-v1"


class Settings(BaseSettings):
    """Environment-backed settings for the challenge sandbox."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Endpoints ─────────────────────────────────────────────────────────────

    challenge_base_url: str = Field(
        default=_DEFAULT_CHALLENGE_URL, alias="CHALLENGE_BASE_URL"
    )
    api_base_url: str = Field(default=_DEFAULT_API_URL, alias="API_BASE_URL")

    # ── Credentials ───────────────────────────────────────────────────────────

    username: str = Field(
        default="candidate@dev-challenge.com", alias="CHALLENGE_USERNAME"
    )
    password: SecretStr = Field(
        default=SecretStr("Password123!"), alias="CHALLENGE_PASSWORD"
    )
    mfa_code: SecretStr = Field(default=SecretStr("1234"), alias="MFA_CODE")

    # ── Browser ───────────────────────────────────────────────────────────────

    headed: bool = Field(default=False, alias="HEADED")
    slow_mo_ms: int = Field(default=0, alias="SLOW_MO_MS")

    # ── Banking details ───────────────────────────────────────────────────────

    bank_routing: str = Field(default="123456789", alias="BANK_ROUTING")
    bank_account: str = Field(default="1234567890", alias="BANK_ACCOUNT")

    # ── Payment details ───────────────────────────────────────────────────────

    cardholder_name: str = Field(default="Test Candidate", alias="CARDHOLDER_NAME")
    card_number: str = Field(default="4242424242424242", alias="CARD_NUMBER")
    card_expiry_month: str = Field(default="12", alias="CARD_EXPIRY_MONTH")
    card_expiry_year: str = Field(default="2035", alias="CARD_EXPIRY_YEAR")
    card_cvc: str = Field(default="123", alias="CARD_CVC")

    # ── API retry ─────────────────────────────────────────────────────────────

    api_max_retries: int = Field(default=5, alias="API_MAX_RETRIES")
    api_retry_max_wait: int = Field(default=30, alias="API_RETRY_MAX_WAIT")

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("challenge_base_url", "api_base_url")
    @classmethod
    def must_be_http_url(cls, v: str) -> str:
        if v and not v.lower().startswith(("http://", "https://")):
            raise ValueError(f"must start with http:// or https://, got: {v!r}")
        return v


def load_settings() -> Settings:
    """Load settings from environment variables and optional .env file."""
    return Settings()
