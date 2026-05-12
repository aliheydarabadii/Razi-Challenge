from __future__ import annotations

import pytest
from pydantic import ValidationError

from account_details_update.http_api.schemas import (
    BankingUpdateRequest,
    MfaVerifyRequest,
    PaymentUpdateRequest,
    TokenRequest,
)


def test_token_request_construction() -> None:
    request = TokenRequest(
        username="candidate@dev-challenge.com",
        password="Password123!",
    )

    assert request.username == "candidate@dev-challenge.com"
    assert request.password == "Password123!"
    assert request.model_dump() == {
        "username": "candidate@dev-challenge.com",
        "password": "Password123!",
    }


def test_mfa_verify_request_construction() -> None:
    request = MfaVerifyRequest(token="temporary-token", code="0000")

    assert request.token == "temporary-token"
    assert request.code == "0000"


def test_banking_update_request_construction() -> None:
    request = BankingUpdateRequest(
        routing_number="123456789",
        account_number="1234567890",
    )

    assert request.routing_number == "123456789"
    assert request.account_number == "1234567890"


def test_payment_update_request_construction() -> None:
    request = PaymentUpdateRequest(
        cardholder_name="Test Candidate",
        card_number="4242424242424242",
        expiry_month="12",
        expiry_year="2030",
        cvc="123",
    )

    assert request.cardholder_name == "Test Candidate"
    assert request.card_number == "4242424242424242"


def test_extra_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        TokenRequest(
            username="candidate@dev-challenge.com",
            password="Password123!",
            unexpected="field",
        )
