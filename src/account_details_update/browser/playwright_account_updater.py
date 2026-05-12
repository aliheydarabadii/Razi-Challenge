"""Future Playwright adapter for account detail updates."""

from __future__ import annotations

from typing import Any

from ..account_details import BankingDetails, PaymentMethod
from ..account_update_result import AccountUpdateResult
from .pages.account_page import AccountPage
from .pages.login_page import LoginPage
from .pages.mfa_page import MfaPage


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
        self.login_page = LoginPage(page)
        self.mfa_page = MfaPage(page)
        self.account_page = AccountPage(page)

    def login(self) -> None:
        # TODO: Coordinate LoginPage.open and LoginPage.login after selectors are verified.
        raise NotImplementedError("Playwright login flow is not implemented yet.")

    def complete_mfa(self) -> None:
        # TODO: Coordinate MfaPage.verify after selectors are verified.
        raise NotImplementedError("Playwright MFA flow is not implemented yet.")

    def update_banking_details(self, banking_details: BankingDetails) -> None:
        # TODO: Coordinate AccountPage.update_banking after selectors are verified.
        raise NotImplementedError(
            "Playwright banking details update is not implemented yet."
        )

    def update_payment_method(self, payment_method: PaymentMethod) -> None:
        # TODO: Coordinate AccountPage.update_payment after selectors are verified.
        raise NotImplementedError(
            "Playwright payment method update is not implemented yet."
        )

    def verify_updates(self) -> AccountUpdateResult:
        # TODO: Coordinate AccountPage.verify_updates after selectors are verified.
        raise NotImplementedError(
            "Playwright update verification is not implemented yet."
        )
