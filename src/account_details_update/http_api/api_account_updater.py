"""AccountUpdatePort adapter backed by the Razi REST API."""

from __future__ import annotations

from dataclasses import dataclass

from ..banking_details import BankingDetails
from ..payment_method import PaymentMethod
from ..ports import AccountUpdateResult
from .razi_api_client import RaziApiClient
from .schemas.banking import BankingUpdateResponse
from .schemas.payment import PaymentUpdateResponse


@dataclass(frozen=True, slots=True)
class ApiAccountUpdater:
    """API adapter that implements AccountUpdatePort via the Razi REST API."""

    client: RaziApiClient

    def execute(
        self,
        banking_details: BankingDetails,
        payment_method: PaymentMethod,
    ) -> AccountUpdateResult:
        token_response = self.client.request_token()
        bearer = self.client.verify_mfa(token_response)
        banking = self.client.update_banking(bearer, banking_details)
        payment = self.client.update_payment(bearer, payment_method)
        return AccountUpdateResult(
            banking_summary=self._banking_summary(banking),
            payment_summary=self._payment_summary(payment),
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _banking_summary(banking: BankingUpdateResponse) -> str:
        return f"Routing {banking.routing_masked} — Account {banking.account_masked}"

    @staticmethod
    def _payment_summary(payment: PaymentUpdateResponse) -> str:
        return (
            f"{payment.card_brand.title()} ending in {payment.last4} "
            f"({payment.exp_month}/{payment.exp_year})"
        )
