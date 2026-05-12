"""Future AccountUpdatePort adapter backed by the Razi REST API."""

from __future__ import annotations

from typing import Any

from account_details_update.account_details import BankingDetails, PaymentMethod
from account_details_update.account_update_result import AccountUpdateResult
from account_details_update.http_api.razi_api_client import RaziApiClient


class ApiAccountUpdater:
    """Placeholder API adapter that will structurally implement AccountUpdatePort."""

    def __init__(self, client: RaziApiClient) -> None:
        self.client = client
        self.token_response: dict[str, Any] | object | None = None
        self.bearer_token: str | None = None
        self.banking_confirmation: dict[str, Any] | None = None
        self.payment_confirmation: dict[str, Any] | None = None

    def login(self) -> None:
        # TODO: Store the initial auth token response from RaziApiClient.
        raise NotImplementedError("API login flow is not implemented yet.")

    def complete_mfa(self) -> None:
        # TODO: Store the bearer token returned by RaziApiClient.verify_mfa.
        raise NotImplementedError("API MFA flow is not implemented yet.")

    def update_banking_details(self, banking_details: BankingDetails) -> None:
        # TODO: Call RaziApiClient.update_banking and store masked confirmation.
        raise NotImplementedError("API banking details update is not implemented yet.")

    def update_payment_method(self, payment_method: PaymentMethod) -> None:
        # TODO: Call RaziApiClient.update_payment and store masked confirmation.
        raise NotImplementedError("API payment method update is not implemented yet.")

    def verify_updates(self) -> AccountUpdateResult:
        # TODO: Build AccountUpdateResult from stored masked confirmations.
        raise NotImplementedError("API update verification is not implemented yet.")
