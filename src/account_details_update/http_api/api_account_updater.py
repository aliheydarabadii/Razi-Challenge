"""AccountUpdatePort adapter backed by the Razi REST API."""

from __future__ import annotations

from ..banking_details import BankingDetails
from ..payment_method import PaymentMethod
from ..ports import AccountUpdateResult
from .banking import BankingUpdateResponse
from .errors import MfaVerificationError, RaziApiError
from .payment import PaymentUpdateResponse
from .razi_api_client import RaziApiClient

# Number of times to retry the full request_token → verify_mfa cycle when the
# Supabase load balancer routes the two requests to different Deno instances.
# This loop is intentionally separate from the per-call tenacity retry in
# RaziApiClient: tenacity handles transient network/server errors; this loop
# handles MfaVerificationError, which requires a fresh token rather than a
# bare retry. Mixing the two would risk amplification (retries × attempts).
_MFA_ROUTING_RETRIES = 10


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
        for attempt in range(_MFA_ROUTING_RETRIES):
            token_response = self.client.request_token()
            try:
                self._bearer_token = self.client.verify_mfa(token_response)
                return
            except MfaVerificationError:
                if attempt >= _MFA_ROUTING_RETRIES - 1:
                    raise
        raise AssertionError("unreachable")

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
