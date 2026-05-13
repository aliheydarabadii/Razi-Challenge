from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_none

from account_details_update.banking_details import BankingDetails
from account_details_update.http_api.errors import (
    ApiValidationError,
    AuthenticationError,
    MfaVerificationError,
    RateLimitError,
    ServerError,
)
from account_details_update.http_api.razi_api_client import RaziApiClient
from account_details_update.http_api.schemas.authentication import TokenResponse
from account_details_update.payment_method import PaymentMethod

# Fast retrying used by all existing tests — no wait, single attempt.
# This keeps tests instant while still exercising the retry code path.
_NO_RETRY = Retrying(
    retry=retry_if_exception_type((RateLimitError, ServerError, httpx.TransportError)),
    wait=wait_none(),
    stop=stop_after_attempt(1),
    reraise=True,
)

# Fast retrying used by retry-specific tests — no wait, multiple attempts.
_FAST_RETRY = Retrying(
    retry=retry_if_exception_type((RateLimitError, ServerError, httpx.TransportError)),
    wait=wait_none(),
    stop=stop_after_attempt(5),
    reraise=True,
)


def _make_client(
    post_response: httpx.Response | None = None,
    put_response: httpx.Response | None = None,
    *,
    retrying: Retrying = _NO_RETRY,
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
        _http_client=http,
        _retrying=retrying,
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


# ── verify_mfa ────────────────────────────────────────────────────────────────


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
    token_response = TokenResponse(mfa_required=True, mfa_token="mfa_bad", message="ok")

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

    with pytest.raises(ApiValidationError, match="Invalid routing number"):
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


# ── retry behaviour ───────────────────────────────────────────────────────────


def test_request_token_retries_on_rate_limit_then_succeeds() -> None:
    client, http = _make_client(retrying=_FAST_RETRY)
    http.post.side_effect = [
        httpx.Response(429, json={"error": "Rate limit exceeded"}),
        httpx.Response(429, json={"error": "Rate limit exceeded"}),
        httpx.Response(
            200,
            json={"mfa_required": True, "mfa_token": "mfa_abc", "message": "ok"},
        ),
    ]

    token = client.request_token()

    assert http.post.call_count == 3
    assert token.mfa_token == "mfa_abc"


def test_update_banking_retries_on_server_error_then_succeeds() -> None:
    client, http = _make_client(retrying=_FAST_RETRY)
    http.put.side_effect = [
        httpx.Response(503, json={"error": "Service unavailable"}),
        httpx.Response(
            200,
            json={
                "routing_masked": "•••••6789",
                "account_masked": "••••••7890",
                "token": "btok_x",
            },
        ),
    ]
    banking = BankingDetails(routing_number="123456789", account_number="1234567890")

    result = client.update_banking("bearer", banking)

    assert http.put.call_count == 2
    assert result.routing_masked == "•••••6789"


def test_request_token_raises_after_exhausting_retries() -> None:
    client, http = _make_client(
        post_response=httpx.Response(429, json={"error": "Rate limit"}),
        retrying=_FAST_RETRY,
    )

    with pytest.raises(RateLimitError):
        client.request_token()

    assert http.post.call_count == 5


# ── close / resource ownership ────────────────────────────────────────────────


def test_injected_http_client_is_not_closed_on_exit() -> None:
    http = MagicMock(spec=httpx.Client)
    with RaziApiClient(
        base_url="https://api.example.com",
        username="u",
        password="p",
        mfa_code="1234",
        _http_client=http,
    ):
        pass
    http.close.assert_not_called()


def test_owned_http_client_is_closed_on_exit() -> None:
    mock_http = MagicMock(spec=httpx.Client)
    with patch(
        "account_details_update.http_api.razi_api_client.httpx.Client",
        return_value=mock_http,
    ):
        with RaziApiClient(
            base_url="https://api.example.com",
            username="u",
            password="p",
            mfa_code="1234",
        ):
            pass
    mock_http.close.assert_called_once()


# ── _raise_for_status edge cases ──────────────────────────────────────────────


def test_raise_for_status_handles_non_dict_json_body() -> None:
    client, _ = _make_client(post_response=httpx.Response(500, json=["error", "list"]))
    with pytest.raises(ServerError):
        client.request_token()


# ── non-retryable errors ──────────────────────────────────────────────────────


def test_authentication_error_is_not_retried() -> None:
    client, http = _make_client(
        post_response=httpx.Response(401, json={"error": "Invalid credentials"}),
        retrying=_FAST_RETRY,
    )

    with pytest.raises(AuthenticationError):
        client.request_token()

    assert http.post.call_count == 1


def test_validation_error_is_not_retried() -> None:
    client, http = _make_client(
        put_response=httpx.Response(422, json={"error": "Invalid routing"}),
        retrying=_FAST_RETRY,
    )
    banking = BankingDetails(routing_number="123456789", account_number="1234567890")

    with pytest.raises(ApiValidationError):
        client.update_banking("bearer", banking)

    assert http.put.call_count == 1
