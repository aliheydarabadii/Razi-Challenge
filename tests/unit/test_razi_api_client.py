from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from account_details_update import BankingDetails, PaymentMethod
from account_details_update.http_api.errors import (
    AuthenticationError,
    MfaVerificationError,
    RateLimitError,
    ValidationError,
)
from account_details_update.http_api.razi_api_client import RaziApiClient
from account_details_update.http_api.schemas import TokenResponse


def _make_client(
    post_response: httpx.Response | None = None,
    put_response: httpx.Response | None = None,
    *,
    anon_key: str = "",
    supabase_url: str = "",
) -> tuple[RaziApiClient, MagicMock]:
    http = MagicMock(spec=httpx.Client)
    if post_response is not None:
        http.post.return_value = post_response
    if put_response is not None:
        http.put.return_value = put_response
    client = RaziApiClient(
        base_url="https://api.example.com",
        username="candidate@dev-challenge.com",
        password="Password123!",
        mfa_code="1234",
        anon_key=anon_key,
        supabase_url=supabase_url,
        _http_client=http,
    )
    return client, http


# ── request_token ─────────────────────────────────────────────────────────────

def test_request_token_posts_credentials_and_returns_token_response() -> None:
    response = httpx.Response(
        200,
        json={"mfa_required": True, "mfa_token": "mfa_abc123", "message": "ok"},
    )
    client, http = _make_client(post_response=response)

    token = client.request_token()

    http.post.assert_called_once_with(
        "https://api.example.com/auth/token",
        json={"email": "candidate@dev-challenge.com", "password": "Password123!"},
    )
    assert token.mfa_token == "mfa_abc123"
    assert token.mfa_required is True


def test_request_token_raises_authentication_error_on_401() -> None:
    client, _ = _make_client(
        post_response=httpx.Response(401, json={"error": "Invalid credentials"})
    )

    with pytest.raises(AuthenticationError, match="Invalid credentials"):
        client.request_token()


def test_request_token_raises_rate_limit_error_on_429() -> None:
    client, _ = _make_client(
        post_response=httpx.Response(429, json={"error": "Rate limit exceeded"})
    )

    with pytest.raises(RateLimitError):
        client.request_token()


# ── native auth path ─────────────────────────────────────────────────────────

def test_request_token_uses_native_supabase_auth_when_anon_key_set() -> None:
    response = httpx.Response(
        200, json={"access_token": "native_jwt", "token_type": "Bearer"}
    )
    client, http = _make_client(
        post_response=response,
        anon_key="anon_key_value",
        supabase_url="https://proj.supabase.co",
    )

    token = client.request_token()

    http.post.assert_called_once_with(
        "https://proj.supabase.co/auth/v1/token?grant_type=password",
        json={"email": "candidate@dev-challenge.com", "password": "Password123!"},
        headers={"apikey": "anon_key_value"},
    )
    assert token.mfa_required is False


def test_verify_mfa_returns_cached_native_token_without_http_call() -> None:
    response = httpx.Response(
        200, json={"access_token": "native_jwt", "token_type": "Bearer"}
    )
    client, http = _make_client(
        post_response=response,
        anon_key="anon_key_value",
        supabase_url="https://proj.supabase.co",
    )
    token_response = client.request_token()

    bearer = client.verify_mfa(token_response)

    assert bearer == "native_jwt"
    assert http.post.call_count == 1  # only request_token, no second post


# ── verify_mfa (custom flow) ──────────────────────────────────────────────────

def test_verify_mfa_posts_token_and_code_returns_bearer_token() -> None:
    response = httpx.Response(
        200,
        json={
            "access_token": "eyJbearer",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "ref_xyz",
        },
    )
    client, http = _make_client(post_response=response)
    token_response = TokenResponse(
        mfa_required=True, mfa_token="mfa_abc123", message="ok"
    )

    bearer = client.verify_mfa(token_response)

    http.post.assert_called_once_with(
        "https://api.example.com/auth/mfa/verify",
        json={"mfa_token": "mfa_abc123", "code": "1234"},
    )
    assert bearer == "eyJbearer"


def test_verify_mfa_raises_mfa_error_on_401() -> None:
    client, _ = _make_client(
        post_response=httpx.Response(401, json={"error": "Invalid MFA code"})
    )
    token_response = TokenResponse(
        mfa_required=True, mfa_token="mfa_bad", message="ok"
    )

    with pytest.raises(MfaVerificationError, match="Invalid MFA code"):
        client.verify_mfa(token_response)


# ── update_banking ────────────────────────────────────────────────────────────

def test_update_banking_puts_with_bearer_and_returns_masked_confirmation() -> None:
    response = httpx.Response(
        200,
        json={
            "routing_masked": "•••••6789",
            "account_masked": "••••••7890",
            "token": "btok_x",
        },
    )
    client, http = _make_client(put_response=response)
    banking = BankingDetails(routing_number="123456789", account_number="1234567890")

    result = client.update_banking("my_bearer", banking)

    http.put.assert_called_once_with(
        "https://api.example.com/account/banking",
        json={"routing_number": "123456789", "account_number": "1234567890"},
        headers={"Authorization": "Bearer my_bearer"},
    )
    assert result.routing_masked == "•••••6789"
    assert result.account_masked == "••••••7890"


def test_update_banking_raises_validation_error_on_422() -> None:
    client, _ = _make_client(
        put_response=httpx.Response(422, json={"error": "Invalid routing number"})
    )
    banking = BankingDetails(routing_number="123456789", account_number="1234567890")

    with pytest.raises(ValidationError, match="Invalid routing number"):
        client.update_banking("bearer", banking)


# ── update_payment ────────────────────────────────────────────────────────────

def test_update_payment_puts_with_bearer_and_returns_masked_confirmation() -> None:
    response = httpx.Response(
        200,
        json={
            "card_brand": "visa",
            "last4": "4242",
            "exp_month": 12,
            "exp_year": 2030,
            "token": "tok_x",
        },
    )
    client, http = _make_client(put_response=response)
    payment = PaymentMethod(
        cardholder_name="Test Candidate",
        card_number="4242424242424242",
        expiry_month="12",
        expiry_year="2030",
        cvc="123",
    )

    result = client.update_payment("my_bearer", payment)

    http.put.assert_called_once_with(
        "https://api.example.com/account/payment",
        json={
            "cardholder_name": "Test Candidate",
            "card_number": "4242424242424242",
            "exp_month": 12,
            "exp_year": 2030,
            "cvc": "123",
        },
        headers={"Authorization": "Bearer my_bearer"},
    )
    assert result.card_brand == "visa"
    assert result.last4 == "4242"
