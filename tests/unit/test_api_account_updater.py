from __future__ import annotations

import pytest

from account_details_update import AccountUpdatePort, BankingDetails, PaymentMethod
from account_details_update.http_api.api_account_updater import ApiAccountUpdater
from account_details_update.http_api.errors import MfaVerificationError, RaziApiError
from account_details_update.http_api.schemas import (
    BankingUpdateResponse,
    PaymentUpdateResponse,
    TokenResponse,
)
from tests.support.fake_data import fake_banking_details, fake_payment_method


class FakeRaziApiClient:
    def __init__(self, *, mfa_fails_times: int = 0) -> None:
        self.calls: list[str] = []
        self._mfa_fails_remaining = mfa_fails_times

    def request_token(self) -> TokenResponse:
        self.calls.append("request_token")
        return TokenResponse(mfa_required=True, mfa_token="mfa_test", message="ok")

    def verify_mfa(self, token_response: TokenResponse) -> str:
        self.calls.append("verify_mfa")
        if self._mfa_fails_remaining > 0:
            self._mfa_fails_remaining -= 1
            raise MfaVerificationError("Invalid or expired MFA session")
        return "bearer_test"

    def update_banking(
        self, bearer_token: str, banking_details: BankingDetails
    ) -> BankingUpdateResponse:
        self.calls.append("update_banking")
        assert bearer_token == "bearer_test"
        return BankingUpdateResponse(
            routing_masked="•••••6789",
            account_masked="••••••7890",
            token="btok_test",
        )

    def update_payment(
        self, bearer_token: str, payment_method: PaymentMethod
    ) -> PaymentUpdateResponse:
        self.calls.append("update_payment")
        assert bearer_token == "bearer_test"
        return PaymentUpdateResponse(
            card_brand="visa",
            last4="4242",
            exp_month=12,
            exp_year=2030,
            token="tok_test",
        )


def test_api_account_updater_orchestrates_auth_and_updates_in_order() -> None:
    fake_client = FakeRaziApiClient()
    updater = ApiAccountUpdater(client=fake_client)

    updater.login()
    updater.complete_mfa()
    updater.update_banking_details(fake_banking_details())
    updater.update_payment_method(fake_payment_method())
    result = updater.verify_updates()

    assert fake_client.calls == [
        "request_token",
        "verify_mfa",
        "update_banking",
        "update_payment",
    ]
    assert result.banking_summary == "Routing •••••6789 — Account ••••••7890"
    assert result.payment_summary == "Visa ending in 4242 (12/2030)"


def test_api_account_updater_satisfies_account_update_port() -> None:
    updater = ApiAccountUpdater(client=FakeRaziApiClient())

    assert isinstance(updater, AccountUpdatePort)


def test_complete_mfa_retries_when_mfa_session_lands_on_different_instance() -> None:
    # Simulates the Supabase edge-function routing issue where verify_mfa hits
    # a different instance than request_token and sees no record of the token.
    fake_client = FakeRaziApiClient(mfa_fails_times=2)
    updater = ApiAccountUpdater(client=fake_client)

    updater.login()
    updater.complete_mfa()

    assert fake_client.calls.count("request_token") == 3  # 1 login + 2 retries
    assert fake_client.calls.count("verify_mfa") == 3     # 2 failures + 1 success


def test_complete_mfa_raises_after_exhausting_retries() -> None:
    fake_client = FakeRaziApiClient(mfa_fails_times=10)
    updater = ApiAccountUpdater(client=fake_client)

    updater.login()
    with pytest.raises(MfaVerificationError):
        updater.complete_mfa(_max_retries=3)


def test_complete_mfa_requires_login_first() -> None:
    updater = ApiAccountUpdater(client=FakeRaziApiClient())

    with pytest.raises(RaziApiError, match="login\\(\\) must be called"):
        updater.complete_mfa()


def test_update_banking_requires_mfa_first() -> None:
    updater = ApiAccountUpdater(client=FakeRaziApiClient())
    updater.login()

    with pytest.raises(RaziApiError, match="complete_mfa\\(\\) must be called"):
        updater.update_banking_details(fake_banking_details())


def test_verify_updates_requires_both_updates() -> None:
    updater = ApiAccountUpdater(client=FakeRaziApiClient())
    updater.login()
    updater.complete_mfa()
    updater.update_banking_details(fake_banking_details())

    with pytest.raises(RaziApiError, match="Banking and payment updates must complete"):
        updater.verify_updates()
