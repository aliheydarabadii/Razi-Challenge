from __future__ import annotations

import pytest

from account_details_update.banking_details import BankingDetails
from account_details_update.http_api.api_account_updater import ApiAccountUpdater
from account_details_update.http_api.errors import MfaVerificationError
from account_details_update.http_api.schemas.authentication import TokenResponse
from account_details_update.http_api.schemas.banking import BankingUpdateResponse
from account_details_update.http_api.schemas.payment import PaymentUpdateResponse
from account_details_update.payment_method import PaymentMethod
from account_details_update.ports import AccountUpdatePort
from tests.support.fake_data import fake_banking_details, fake_payment_method


class FakeRaziApiClient:
    def __init__(self, *, verify_mfa_raises: Exception | None = None) -> None:
        self.calls: list[str | tuple[str, str]] = []
        self._verify_mfa_raises = verify_mfa_raises

    def request_token(self) -> TokenResponse:
        self.calls.append("request_token")
        return TokenResponse(mfa_required=True, mfa_token="mfa_tok", message="ok")

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


def test_execute_authenticates_and_updates_in_order() -> None:
    fake_client = FakeRaziApiClient()
    updater = ApiAccountUpdater(client=fake_client)

    result = updater.execute(fake_banking_details(), fake_payment_method())

    assert fake_client.calls == [
        "request_token",
        "verify_mfa",
        ("update_banking", "bearer_test"),
        ("update_payment", "bearer_test"),
    ]
    assert result.banking_summary == "Routing •••••6789 — Account ••••••7890"
    assert result.payment_summary == "Visa ending in 4242 (12/2030)"


def test_execute_satisfies_account_update_port() -> None:
    assert isinstance(ApiAccountUpdater(client=FakeRaziApiClient()), AccountUpdatePort)


def test_execute_propagates_mfa_failure() -> None:
    fake_client = FakeRaziApiClient(
        verify_mfa_raises=MfaVerificationError("Invalid or expired MFA session")
    )
    with pytest.raises(MfaVerificationError):
        ApiAccountUpdater(client=fake_client).execute(
            fake_banking_details(), fake_payment_method()
        )
