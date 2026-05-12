"""API request and response schemas for the Razi REST API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ApiRequest(BaseModel):
    """Base for request bodies — rejects unknown fields to catch typos early."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ApiResponse(BaseModel):
    """Base for response bodies — ignores unknown fields for forward compatibility."""

    model_config = ConfigDict(extra="ignore", frozen=True)


# ── Auth ──────────────────────────────────────────────────────────────────────


class TokenRequest(ApiRequest):
    email: str
    password: str


class TokenResponse(ApiResponse):
    mfa_required: bool
    mfa_token: str
    message: str


class MfaVerifyRequest(ApiRequest):
    mfa_token: str
    code: str


class MfaVerifyResponse(ApiResponse):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str


# ── Account updates ───────────────────────────────────────────────────────────


class BankingUpdateRequest(ApiRequest):
    routing_number: str
    account_number: str


class BankingUpdateResponse(ApiResponse):
    routing_masked: str
    account_masked: str
    token: str


class PaymentUpdateRequest(ApiRequest):
    cardholder_name: str
    card_number: str
    exp_month: int
    exp_year: int
    cvc: str


class PaymentUpdateResponse(ApiResponse):
    card_brand: str
    last4: str
    exp_month: int
    exp_year: int
    token: str
