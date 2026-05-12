"""Placeholder API schemas for future request and response shapes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TokenRequest:
    username: str
    password: str


@dataclass(frozen=True, slots=True)
class MfaVerifyRequest:
    token: str
    code: str


@dataclass(frozen=True, slots=True)
class BankingUpdateRequest:
    routing_number: str
    account_number: str


@dataclass(frozen=True, slots=True)
class PaymentUpdateRequest:
    cardholder_name: str
    card_number: str
    expiry_month: str
    expiry_year: str
    cvc: str


@dataclass(frozen=True, slots=True)
class MaskedConfirmation:
    banking_summary: str
    payment_summary: str
