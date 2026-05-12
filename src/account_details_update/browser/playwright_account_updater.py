"""Playwright adapter for account detail updates."""

from __future__ import annotations

from collections.abc import Callable
from types import TracebackType
from typing import Any

from ..account_details import BankingDetails, PaymentMethod
from ..account_update_result import AccountUpdateResult
from .pages._helpers import BrowserPageError, require_page
from .pages.account_page import AccountPage
from .pages.login_page import LoginPage
from .pages.mfa_page import MfaPage

DEFAULT_LOGIN_PATH = "/login"
DEFAULT_ACCOUNT_PATH = "/app/account"


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
        login_url: str | None = None,
        account_url: str | None = None,
        _playwright_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.login_url = login_url or _join_url(self.base_url, DEFAULT_LOGIN_PATH)
        self.account_url = account_url or _join_url(
            self.base_url,
            DEFAULT_ACCOUNT_PATH,
        )
        self._username = username
        self._password = password
        self._mfa_code = mfa_code
        self.headed = headed
        self.slow_mo_ms = slow_mo_ms
        self._playwright_factory = _playwright_factory
        self.page: Any | None = page
        self._owns_page = page is None
        self._playwright: Any | None = None
        self._browser: Any | None = None
        self._context: Any | None = None
        self.login_page: LoginPage
        self.mfa_page: MfaPage
        self.account_page: AccountPage
        self._login_completed = False
        self._mfa_completed = False
        self._account_page_opened = False
        self._banking_updated = False
        self._payment_updated = False
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
        self.login_page.open(self.login_url)
        self.login_page.login(self._username, self._password)
        self._login_completed = True

    def complete_mfa(self) -> None:
        self._require_logged_in()
        self.mfa_page.verify(self._mfa_code)
        self._mfa_completed = True

    def update_banking_details(self, banking_details: BankingDetails) -> None:
        self._require_mfa_completed()
        self._open_account_page_once()
        self.account_page.update_banking(banking_details)
        self._banking_updated = True

    def update_payment_method(self, payment_method: PaymentMethod) -> None:
        self._require_mfa_completed()
        self._open_account_page_once()
        self.account_page.update_payment(payment_method)
        self._payment_updated = True

    def verify_updates(self) -> AccountUpdateResult:
        self._require_updates_completed()
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
        self._login_completed = False
        self._mfa_completed = False
        self._account_page_opened = False
        self._banking_updated = False
        self._payment_updated = False

    def _bind_page_objects(self, page: Any | None) -> None:
        self.login_page = LoginPage(page)
        self.mfa_page = MfaPage(page)
        self.account_page = AccountPage(page)

    def _ensure_page(self) -> Any:
        if self.page is not None:
            return self.page

        playwright_factory = self._playwright_factory
        if playwright_factory is None:
            try:
                from playwright.sync_api import sync_playwright
            except ImportError as exc:
                raise RuntimeError(
                    "Playwright is required for browser automation. Install project "
                    "dependencies and run `playwright install chromium`."
                ) from exc
            playwright_factory = sync_playwright

        self._playwright = playwright_factory().start()
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

    def _require_logged_in(self) -> None:
        require_page(self.page)
        if not self._login_completed:
            raise BrowserPageError(
                "login() must complete before continuing browser account updates."
            )

    def _require_mfa_completed(self) -> None:
        self._require_logged_in()
        if not self._mfa_completed:
            raise BrowserPageError(
                "complete_mfa() must complete before updating account details."
            )

    def _require_updates_completed(self) -> None:
        self._require_mfa_completed()
        if not self._banking_updated or not self._payment_updated:
            raise BrowserPageError(
                "Banking and payment updates must complete before verification."
            )

    def _open_account_page_once(self) -> None:
        if self._account_page_opened:
            return
        self.account_page.open(self.account_url)
        self._account_page_opened = True


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url}/{path.lstrip('/')}"
