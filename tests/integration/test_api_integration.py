"""Integration tests for the REST API adapter.

Each test hits the live Supabase sandbox. A module-scoped bearer token
fixture authenticates once and is reused across all tests in this file.

Run with:
    INTEGRATION_TESTS=1 pytest tests/integration/test_api_integration.py -v
"""

from __future__ import annotations

import pytest

from account_details_update.application.commands import UpdateAccountDetailsCommand
from account_details_update.application.update_account_details import (
    UpdateAccountDetailsHandler,
)
from account_details_update.banking_details import BankingDetails
from account_details_update.bootstrap.settings import Settings
from account_details_update.http_api.api_account_updater import ApiAccountUpdater
from account_details_update.http_api.errors import AuthenticationError
from account_details_update.http_api.razi_api_client import RaziApiClient
from account_details_update.payment_method import PaymentMethod


@pytest.fixture(scope="module")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="module")
def client(settings: Settings) -> RaziApiClient:  # type: ignore[misc]
    with RaziApiClient(
        base_url=settings.api_base_url,
        username=settings.username,
        password=settings.password.get_secret_value(),
        mfa_code=settings.mfa_code.get_secret_value(),
    ) as c:
        yield c


@pytest.fixture(scope="module")
def bearer_token(client: RaziApiClient) -> str:
    token_response = client.request_token()
    return client.verify_mfa(token_response)


# ── auth ──────────────────────────────────────────────────────────────────────


def test_request_token_succeeds(client: RaziApiClient) -> None:
    token_response = client.request_token()
    assert token_response.mfa_token


def test_verify_mfa_returns_jwt(client: RaziApiClient) -> None:
    token_response = client.request_token()
    token = client.verify_mfa(token_response)
    # JWTs are three base64url segments separated by dots.
    assert token.count(".") == 2
    assert len(token) > 50


def test_wrong_password_raises_authentication_error(settings: Settings) -> None:
    with RaziApiClient(
        base_url=settings.api_base_url,
        username=settings.username,
        password="wrong-password",
        mfa_code=settings.mfa_code.get_secret_value(),
    ) as bad_client:
        with pytest.raises(AuthenticationError):
            bad_client.request_token()


# ── account updates ───────────────────────────────────────────────────────────


def test_update_banking_returns_masked_confirmation(
    client: RaziApiClient, bearer_token: str, settings: Settings
) -> None:
    banking = BankingDetails(
        routing_number=settings.bank_routing,
        account_number=settings.bank_account,
    )
    result = client.update_banking(bearer_token, banking)

    # Masked values must contain the last 4 digits of each number.
    assert settings.bank_routing[-4:] in result.routing_masked
    assert settings.bank_account[-4:] in result.account_masked
    assert result.token  # server returns a bank token


def test_update_payment_returns_card_confirmation(
    client: RaziApiClient, bearer_token: str, settings: Settings
) -> None:
    payment = PaymentMethod(
        cardholder_name=settings.cardholder_name,
        card_number=settings.card_number,
        expiry_month=settings.card_expiry_month,
        expiry_year=settings.card_expiry_year,
        cvc=settings.card_cvc,
    )
    result = client.update_payment(bearer_token, payment)

    assert result.last4 == settings.card_number[-4:]
    assert result.exp_month == settings.card_expiry_month
    assert result.exp_year == settings.card_expiry_year
    assert result.card_brand  # e.g. "visa"
    assert result.token  # server returns a card token


# ── full use-case flow ────────────────────────────────────────────────────────


def test_full_api_flow_via_use_case(settings: Settings) -> None:
    """Runs the complete UpdateAccountDetails use case against the live API."""
    banking = BankingDetails(
        routing_number=settings.bank_routing,
        account_number=settings.bank_account,
    )
    payment = PaymentMethod(
        cardholder_name=settings.cardholder_name,
        card_number=settings.card_number,
        expiry_month=settings.card_expiry_month,
        expiry_year=settings.card_expiry_year,
        cvc=settings.card_cvc,
    )
    command = UpdateAccountDetailsCommand(
        banking_details=banking, payment_method=payment
    )
    with RaziApiClient(
        base_url=settings.api_base_url,
        username=settings.username,
        password=settings.password.get_secret_value(),
        mfa_code=settings.mfa_code.get_secret_value(),
    ) as c:
        result = UpdateAccountDetailsHandler(port=ApiAccountUpdater(client=c)).handle(
            command
        )

    assert settings.bank_routing[-4:] in result.banking_summary
    assert settings.bank_account[-4:] in result.banking_summary
    assert settings.card_number[-4:] in result.payment_summary
