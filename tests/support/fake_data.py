"""Fake sandbox data for tests."""

from __future__ import annotations

from account_details_update import BankingDetails, PaymentMethod


def fake_banking_details() -> BankingDetails:
    return BankingDetails(
        routing_number="123456789",
        account_number="1234567890",
    )


def fake_payment_method() -> PaymentMethod:
    return PaymentMethod(
        cardholder_name="Test Candidate",
        card_number="4242424242424242",
        expiry_month="12",
        expiry_year="2030",
        cvc="123",
    )
