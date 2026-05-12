"""AccountUpdatePort adapter backed by the Razi REST API."""

from __future__ import annotations

from ..account_details import BankingDetails, PaymentMethod
from ..account_update_result import AccountUpdateResult
from .errors import RaziApiError
from .razi_api_client import RaziApiClient
from .schemas import BankingUpdateResponse, PaymentUpdateResponse


class ApiAccountUpdater:
    """API adapter that implements AccountUpdatePort via the Razi REST API."""

    def __init__(self, client: RaziApiClient) -> None:
        self.client = client
        self._login_called = False
        self._bearer_token: str | None = None
        self._banking_confirmation: BankingUpdateResponse | None = None
        self._payment_confirmation: PaymentUpdateResponse | None = None

    def login(self) -> None:
        self._login_called = True

    def complete_mfa(self) -> None:
        if not self._login_called:
            raise RaziApiError("login() must be called before complete_mfa().")
        self._bearer_token = self.client.authenticate()

    def update_banking_details(self, banking_details: BankingDetails) -> None:
        if self._bearer_token is None:
            raise RaziApiError("complete_mfa() must be called before updating details.")
        self._banking_confirmation = self.client.update_banking(
            self._bearer_token, banking_details
        )

    def update_payment_method(self, payment_method: PaymentMethod) -> None:
        if self._bearer_token is None:
            raise RaziApiError("complete_mfa() must be called before updating details.")
        self._payment_confirmation = self.client.update_payment(
            self._bearer_token, payment_method
        )

    def verify_updates(self) -> AccountUpdateResult:
        if self._banking_confirmation is None or self._payment_confirmation is None:
            raise RaziApiError(
                "Banking and payment updates must complete before verification."
            )
        banking = self._banking_confirmation
        payment = self._payment_confirmation
        return AccountUpdateResult(
            banking_summary=(
                f"Routing {banking.routing_masked} — Account {banking.account_masked}"
            ),
            payment_summary=(
                f"{payment.card_brand.title()} ending in {payment.last4} "
                f"({payment.exp_month}/{payment.exp_year})"
            ),
        )
