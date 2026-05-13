"""Fake sandbox data for tests."""

from __future__ import annotations

from datetime import date

from account_details_update.banking_details import BankingDetails
from account_details_update.payment_method import PaymentMethod


def fake_banking_details() -> BankingDetails:
    return BankingDetails(
        routing_number="123456789",
        account_number="1234567890",
    )


def fake_payment_method() -> PaymentMethod:
    return PaymentMethod(
        cardholder_name="Test Candidate",
        card_number="4242424242424242",
        expiry_month=12,
        expiry_year=date.today().year + 5,
        cvc="123",
    )
