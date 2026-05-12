from __future__ import annotations

from datetime import date

import pytest

from account_details_update import BankingDetails, PaymentMethod


def test_valid_banking_details() -> None:
    banking_details = BankingDetails(
        routing_number="123456789",
        account_number="1234567890",
    )

    assert banking_details.routing_number == "123456789"
    assert banking_details.account_number == "1234567890"


def test_invalid_routing_number_length() -> None:
    with pytest.raises(ValueError, match="routing_number must be exactly 9 digits"):
        BankingDetails(routing_number="12345678", account_number="1234567890")


def test_invalid_routing_number_non_digit() -> None:
    with pytest.raises(ValueError, match="routing_number must contain only digits"):
        BankingDetails(routing_number="12345678A", account_number="1234567890")


def test_invalid_account_number_length() -> None:
    with pytest.raises(ValueError, match="account_number must be 4 to 17 digits"):
        BankingDetails(routing_number="123456789", account_number="123")


def test_valid_payment_method() -> None:
    payment_method = PaymentMethod(
        cardholder_name="Test Candidate",
        card_number="4242424242424242",
        expiry_month="12",
        expiry_year="2030",
        cvc="123",
    )

    assert payment_method.cardholder_name == "Test Candidate"
    assert payment_method.card_number == "4242424242424242"


def test_missing_cardholder_name() -> None:
    with pytest.raises(ValueError, match="cardholder_name is required"):
        PaymentMethod(
            cardholder_name="",
            card_number="4242424242424242",
            expiry_month="12",
            expiry_year="2030",
            cvc="123",
        )


def test_invalid_card_number_non_digit() -> None:
    with pytest.raises(ValueError, match="card_number must contain only digits"):
        PaymentMethod(
            cardholder_name="Test Candidate",
            card_number="424242424242424X",
            expiry_month="12",
            expiry_year="2030",
            cvc="123",
        )


def test_invalid_card_number_length() -> None:
    with pytest.raises(ValueError, match="card_number must be 13 to 19 digits"):
        PaymentMethod(
            cardholder_name="Test Candidate",
            card_number="424242424242",
            expiry_month="12",
            expiry_year="2030",
            cvc="123",
        )


def test_invalid_cvc_length() -> None:
    with pytest.raises(ValueError, match="cvc must be 3 or 4 digits"):
        PaymentMethod(
            cardholder_name="Test Candidate",
            card_number="4242424242424242",
            expiry_month="12",
            expiry_year="2030",
            cvc="12",
        )


def test_past_expiry_year() -> None:
    with pytest.raises(ValueError, match="card has already expired"):
        PaymentMethod(
            cardholder_name="Test Candidate",
            card_number="4242424242424242",
            expiry_month="12",
            expiry_year=str(date.today().year - 1),
            cvc="123",
        )


def test_card_expired_earlier_this_year_is_rejected() -> None:
    today = date.today()
    if today.month == 1:
        pytest.skip("no elapsed months in January to test against")
    with pytest.raises(ValueError, match="card has already expired"):
        PaymentMethod(
            cardholder_name="Test Candidate",
            card_number="4242424242424242",
            expiry_month=str(today.month - 1),
            expiry_year=str(today.year),
            cvc="123",
        )
