from __future__ import annotations

import pytest
from pydantic import ValidationError

from account_details_update.http_api.authentication import (
    MfaVerifyRequest,
    MfaVerifyResponse,
    TokenRequest,
    TokenResponse,
)
from account_details_update.http_api.banking import (
    BankingUpdateRequest,
    BankingUpdateResponse,
)
from account_details_update.http_api.payment import (
    PaymentUpdateRequest,
    PaymentUpdateResponse,
)


def test_token_request_construction() -> None:
    request = TokenRequest(email="candidate@dev-challenge.com", password="Password123!")

    assert request.email == "candidate@dev-challenge.com"
    assert request.password == "Password123!"
    assert request.model_dump() == {
        "email": "candidate@dev-challenge.com",
        "password": "Password123!",
    }


def test_mfa_verify_request_construction() -> None:
    request = MfaVerifyRequest(mfa_token="mfa_abc123", code="1234")

    assert request.mfa_token == "mfa_abc123"
    assert request.code == "1234"


def test_banking_update_request_construction() -> None:
    request = BankingUpdateRequest(
        routing_number="123456789", account_number="1234567890"
    )

    assert request.routing_number == "123456789"
    assert request.account_number == "1234567890"


def test_payment_update_request_construction() -> None:
    request = PaymentUpdateRequest(
        cardholder_name="Test Candidate",
        card_number="4242424242424242",
        exp_month=12,
        exp_year=2030,
        cvc="123",
    )

    assert request.cardholder_name == "Test Candidate"
    assert request.exp_month == 12
    assert request.exp_year == 2030


def test_token_response_construction() -> None:
    response = TokenResponse(
        mfa_required=True,
        mfa_token="mfa_abc123",
        message="MFA code required",
    )

    assert response.mfa_token == "mfa_abc123"
    assert response.mfa_required is True


def test_mfa_verify_response_construction() -> None:
    response = MfaVerifyResponse(
        access_token="eyJabc",
        token_type="Bearer",
        expires_in=3600,
        refresh_token="ref_xyz",
    )

    assert response.access_token == "eyJabc"
    assert response.expires_in == 3600


def test_banking_update_response_construction() -> None:
    response = BankingUpdateResponse(
        routing_masked="•••••0021",
        account_masked="••••••7890",
        token="btok_test",
    )

    assert response.routing_masked == "•••••0021"
    assert response.account_masked == "••••••7890"


def test_payment_update_response_construction() -> None:
    response = PaymentUpdateResponse(
        card_brand="visa",
        last4="4242",
        exp_month=12,
        exp_year=2030,
        token="tok_test",
    )

    assert response.card_brand == "visa"
    assert response.last4 == "4242"


def test_response_ignores_unknown_fields() -> None:
    response = TokenResponse.model_validate(
        {
            "mfa_required": True,
            "mfa_token": "mfa_abc",
            "message": "ok",
            "future_field": "ignored",
        }
    )

    assert not hasattr(response, "future_field")


def test_request_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        TokenRequest(
            email="candidate@dev-challenge.com",
            password="Password123!",
            unexpected="field",
        )
