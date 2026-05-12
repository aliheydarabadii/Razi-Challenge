"""Future Playwright adapter for account detail updates."""

from __future__ import annotations

from typing import Any

from account_details_update.account_details import BankingDetails, PaymentMethod
from account_details_update.account_update_result import AccountUpdateResult


class PlaywrightAccountUpdater:
    """Placeholder browser adapter that will structurally implement AccountUpdatePort."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        mfa_code: str,
        page: Any | None = None,
    ) -> None:
        self.base_url = base_url
        self.username = username
        self.password = password
        self.mfa_code = mfa_code
        self.page = page

    def login(self) -> None:
        # TODO: Use Playwright page objects to open the challenge site and log in.
        raise NotImplementedError("Playwright login flow is not implemented yet.")

    def complete_mfa(self) -> None:
        # TODO: Complete MFA with verified challenge-site selectors.
        raise NotImplementedError("Playwright MFA flow is not implemented yet.")

    def update_banking_details(self, banking_details: BankingDetails) -> None:
        # TODO: Fill and submit banking fields through the account page.
        raise NotImplementedError(
            "Playwright banking details update is not implemented yet."
        )

    def update_payment_method(self, payment_method: PaymentMethod) -> None:
        # TODO: Fill and submit payment method fields through the account page.
        raise NotImplementedError(
            "Playwright payment method update is not implemented yet."
        )

    def verify_updates(self) -> AccountUpdateResult:
        # TODO: Read masked update confirmations from the account page.
        raise NotImplementedError(
            "Playwright update verification is not implemented yet."
        )
