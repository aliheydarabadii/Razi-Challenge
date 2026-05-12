"""Placeholder API schemas for future request and response shapes."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ApiSchema(BaseModel):
    """Base model for API request and response placeholders."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class TokenRequest(ApiSchema):
    username: str
    password: str


class MfaVerifyRequest(ApiSchema):
    token: str
    code: str


class BankingUpdateRequest(ApiSchema):
    routing_number: str
    account_number: str


class PaymentUpdateRequest(ApiSchema):
    cardholder_name: str
    card_number: str
    expiry_month: str
    expiry_year: str
    cvc: str
