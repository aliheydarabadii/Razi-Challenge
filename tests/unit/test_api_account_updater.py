from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from account_details_update import AccountUpdatePort, BankingDetails, PaymentMethod
from account_details_update.http_api.api_account_updater import (
    ApiAccountUpdater,
    _MFA_ROUTING_RETRIES,
)
from account_details_update.http_api.errors import MfaVerificationError, RaziApiError
from account_details_update.http_api.schemas import (
    BankingUpdateResponse,
    PaymentUpdateResponse,
    TokenResponse,
)
from tests.support.fake_data import fake_banking_details, fake_payment_method


class FakeRaziApiClient:
    def __init__(self, *, verify_mfa_raises: Exception | None = None) -> None:
        self.calls: list[str | tuple[str, str]] = []
        self._verify_mfa_raises = verify_mfa_raises

    def request_token(self) -> TokenResponse:
        self.calls.append("request_token")
        return TokenResponse(mfa_required=False, mfa_token="", message="native")

    def verify_mfa(self, token_response: TokenResponse) -> str:
        self.calls.append("verify_mfa")
        if self._verify_mfa_raises is not None:
            raise self._verify_mfa_raises
        return "bearer_test"

    def update_banking(
        self, bearer_token: str, banking_details: BankingDetails
    ) -> BankingUpdateResponse:
        self.calls.append(("update_banking", bearer_token))
        return BankingUpdateResponse(
            routing_masked="•••••6789",
            account_masked="••••••7890",
            token="btok_test",
        )

    def update_payment(
        self, bearer_token: str, payment_method: PaymentMethod
    ) -> PaymentUpdateResponse:
        self.calls.append(("update_payment", bearer_token))
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
        ("update_banking", "bearer_test"),
        ("update_payment", "bearer_test"),
    ]
    assert result.banking_summary == "Routing •••••6789 — Account ••••••7890"
    assert result.payment_summary == "Visa ending in 4242 (12/2030)"


def test_api_account_updater_satisfies_account_update_port() -> None:
    updater = ApiAccountUpdater(client=FakeRaziApiClient())

    assert isinstance(updater, AccountUpdatePort)


def test_complete_mfa_requires_login_first() -> None:
    updater = ApiAccountUpdater(client=FakeRaziApiClient())

    with pytest.raises(RaziApiError, match="login\\(\\) must be called"):
        updater.complete_mfa()


def test_complete_mfa_propagates_mfa_failure_after_all_retries() -> None:
    fake_client = FakeRaziApiClient(
        verify_mfa_raises=MfaVerificationError("Invalid or expired MFA session")
    )
    updater = ApiAccountUpdater(client=fake_client)
    updater.login()

    with pytest.raises(MfaVerificationError):
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


# ── routing-miss retry (Deno instance routing) ────────────────────────────────


@pytest.mark.parametrize(
    "failures, should_succeed",
    [
        (0, True),                          # no routing miss — succeeds immediately
        (1, True),                          # one miss — succeeds mid-run
        (_MFA_ROUTING_RETRIES - 1, True),   # boundary: last attempt succeeds
        (_MFA_ROUTING_RETRIES, False),      # all attempts exhausted — raises
    ],
)
def test_complete_mfa_routing_miss_retry_behaviour(
    failures: int, should_succeed: bool
) -> None:
    fake_client = FakeRaziApiClient()
    updater = ApiAccountUpdater(client=fake_client)
    updater.login()

    token_response = TokenResponse(mfa_required=False, mfa_token="", message="native")
    side_effects: list[str | MfaVerificationError] = [
        MfaVerificationError("routing miss")
    ] * failures
    if should_succeed:
        side_effects.append("bearer_ok")

    mock_verify = MagicMock(side_effect=side_effects)

    with patch.object(fake_client, "request_token", return_value=token_response):
        with patch.object(fake_client, "verify_mfa", mock_verify):
            if should_succeed:
                updater.complete_mfa()
                assert updater._bearer_token == "bearer_ok"
                assert mock_verify.call_count == failures + 1
            else:
                with pytest.raises(MfaVerificationError):
                    updater.complete_mfa()
                assert mock_verify.call_count == _MFA_ROUTING_RETRIES
