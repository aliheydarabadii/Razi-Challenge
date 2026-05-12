"""Future low-level Razi REST API client."""

from __future__ import annotations

from typing import Any

from ..account_details import BankingDetails, PaymentMethod


class RaziApiClient:
    """Placeholder API client for future HTTP requests."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        mfa_code: str,
    ) -> None:
        self.base_url = base_url
        self._username = username
        self._password = password
        self._mfa_code = mfa_code

    def request_token(self) -> dict[str, Any]:
        # TODO: Request an initial auth token from the API.
        raise NotImplementedError("API token request is not implemented yet.")

    def verify_mfa(self, token_response: dict[str, Any]) -> str:
        # TODO: Exchange the token response and MFA code for a bearer token.
        raise NotImplementedError("API MFA verification is not implemented yet.")

    def update_banking(
        self,
        bearer_token: str,
        banking_details: BankingDetails,
    ) -> dict[str, Any]:
        # TODO: Submit banking details with the bearer token.
        raise NotImplementedError("API banking update is not implemented yet.")

    def update_payment(
        self,
        bearer_token: str,
        payment_method: PaymentMethod,
    ) -> dict[str, Any]:
        # TODO: Submit payment method details with the bearer token.
        raise NotImplementedError("API payment update is not implemented yet.")
