"""Account page placeholder for future Playwright automation."""

from __future__ import annotations

from typing import Any

from account_details_update.account_details import BankingDetails, PaymentMethod
from account_details_update.account_update_result import AccountUpdateResult


class AccountPage:
    """Placeholder page object for account update screens."""

    def __init__(self, page: Any | None = None) -> None:
        self.page = page

    def open(self, base_url: str) -> None:
        # TODO: Navigate to the verified account details URL using Playwright.
        raise NotImplementedError("Account page navigation is not implemented yet.")

    def update_banking(self, banking_details: BankingDetails) -> None:
        # TODO: Fill and submit banking details using verified selectors.
        raise NotImplementedError("Banking details update is not implemented yet.")

    def update_payment(self, payment_method: PaymentMethod) -> None:
        # TODO: Fill and submit payment details using verified selectors.
        raise NotImplementedError("Payment method update is not implemented yet.")

    def verify_updates(self) -> AccountUpdateResult:
        # TODO: Read masked banking and payment confirmations from the page.
        raise NotImplementedError("Account update verification is not implemented yet.")
