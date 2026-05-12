"""Playwright adapter for account detail updates."""

from __future__ import annotations

from types import TracebackType
from typing import Any

from ..account_details import BankingDetails, PaymentMethod
from ..account_update_result import AccountUpdateResult
from .pages.account_page import AccountPage
from .pages.login_page import LoginPage
from .pages.mfa_page import MfaPage


class PlaywrightAccountUpdater:
    """Browser adapter that structurally implements AccountUpdatePort."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        mfa_code: str,
        page: Any | None = None,
        *,
        headed: bool = False,
        slow_mo_ms: int = 0,
    ) -> None:
        self.base_url = base_url
        self.username = username
        self.password = password
        self.mfa_code = mfa_code
        self.headed = headed
        self.slow_mo_ms = slow_mo_ms
        self.page: Any | None = page
        self._owns_page = page is None
        self._playwright: Any | None = None
        self._browser: Any | None = None
        self._context: Any | None = None
        self.login_page: LoginPage
        self.mfa_page: MfaPage
        self.account_page: AccountPage
        self._bind_page_objects(page)

    def __enter__(self) -> PlaywrightAccountUpdater:
        self._ensure_page()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def login(self) -> None:
        self._ensure_page()
        self.login_page.open(self.base_url)
        self.login_page.login(self.username, self.password)

    def complete_mfa(self) -> None:
        self._ensure_page()
        self.mfa_page.verify(self.mfa_code)

    def update_banking_details(self, banking_details: BankingDetails) -> None:
        self._ensure_page()
        self.account_page.update_banking(banking_details)

    def update_payment_method(self, payment_method: PaymentMethod) -> None:
        self._ensure_page()
        self.account_page.update_payment(payment_method)

    def verify_updates(self) -> AccountUpdateResult:
        self._ensure_page()
        return self.account_page.verify_updates()

    def close(self) -> None:
        """Close Playwright resources owned by this adapter."""

        if self._context is not None:
            self._context.close()
            self._context = None
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None
        if self._owns_page and self.page is not None:
            self.page = None
            self._bind_page_objects(None)

    def _bind_page_objects(self, page: Any | None) -> None:
        self.login_page = LoginPage(page)
        self.mfa_page = MfaPage(page)
        self.account_page = AccountPage(page)

    def _ensure_page(self) -> Any:
        if self.page is not None:
            return self.page

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is required for browser automation. Install project "
                "dependencies and run `playwright install chromium`."
            ) from exc

        self._playwright = sync_playwright().start()
        try:
            self._browser = self._playwright.chromium.launch(
                headless=not self.headed,
                slow_mo=self.slow_mo_ms,
            )
            self._context = self._browser.new_context()
            self.page = self._context.new_page()
            self._owns_page = True
        except Exception:
            self.close()
            raise

        self._bind_page_objects(self.page)
        return self.page
