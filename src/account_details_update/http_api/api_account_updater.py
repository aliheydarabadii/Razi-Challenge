"""AccountUpdatePort adapter backed by the Razi REST API."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..banking_details import BankingDetails
from ..payment_method import PaymentMethod
from ..ports import AccountUpdateResult
from .errors import RaziApiError
from .razi_api_client import RaziApiClient
from .schemas.banking import BankingUpdateResponse
from .schemas.payment import PaymentUpdateResponse


@dataclass(slots=True)
class ApiAccountUpdater:
    """API adapter that implements AccountUpdatePort via the Razi REST API."""

    # ── Constructor parameter ─────────────────────────────────────────────────

    client: RaziApiClient

    # ── Runtime state ─────────────────────────────────────────────────────────

    _login_called: bool = field(default=False, init=False)
    _bearer_token: str | None = field(default=None, init=False)
    _banking_confirmation: BankingUpdateResponse | None = field(
        default=None, init=False
    )
    _payment_confirmation: PaymentUpdateResponse | None = field(
        default=None, init=False
    )

    # ── AccountUpdatePort ─────────────────────────────────────────────────────

    def login(self) -> None:
        self._login_called = True

    def complete_mfa(self) -> None:
        if not self._login_called:
            raise RaziApiError("login() must be called before complete_mfa().")
        token_response = self.client.request_token()
        self._bearer_token = self.client.verify_mfa(token_response)

    def update_banking_details(self, banking_details: BankingDetails) -> None:
        self._banking_confirmation = self.client.update_banking(
            self._require_authenticated(), banking_details
        )

    def update_payment_method(self, payment_method: PaymentMethod) -> None:
        self._payment_confirmation = self.client.update_payment(
            self._require_authenticated(), payment_method
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

    # ── Private helpers ───────────────────────────────────────────────────────

    def _require_authenticated(self) -> str:
        if self._bearer_token is None:
            raise RaziApiError("complete_mfa() must be called before updating details.")
        return self._bearer_token
