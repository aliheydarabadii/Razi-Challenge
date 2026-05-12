"""Playwright adapter for account detail updates."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any

from ..banking_details import BankingDetails
from ..payment_method import PaymentMethod
from ..ports import AccountUpdateResult
from .errors import BrowserPageError
from .pages._helpers import require_page
from .pages.account_page import AccountPage
from .pages.login_page import LoginPage
from .pages.mfa_page import MfaPage

DEFAULT_LOGIN_PATH = "/login"
DEFAULT_ACCOUNT_PATH = "/app/account"


@dataclass(slots=True)
class PlaywrightAccountUpdater:
    """Browser adapter that structurally implements AccountUpdatePort."""

    # ── Constructor parameters ────────────────────────────────────────────────

    base_url: str
    username: str
    password: str
    mfa_code: str
    page: Any | None = None
    headed: bool = field(default=False, kw_only=True)
    slow_mo_ms: int = field(default=0, kw_only=True)
    login_url: str = field(default="", kw_only=True)
    account_url: str = field(default="", kw_only=True)
    _playwright_factory: Callable[[], Any] | None = field(
        default=None, kw_only=True
    )

    # ── Runtime state (not constructor parameters) ────────────────────────────

    _owns_page: bool = field(default=False, init=False)
    _playwright: Any | None = field(default=None, init=False)
    _browser: Any | None = field(default=None, init=False)
    _context: Any | None = field(default=None, init=False)
    login_page: LoginPage = field(init=False)
    mfa_page: MfaPage = field(init=False)
    account_page: AccountPage = field(init=False)
    _login_completed: bool = field(default=False, init=False)
    _mfa_completed: bool = field(default=False, init=False)
    _account_page_opened: bool = field(default=False, init=False)
    _banking_updated: bool = field(default=False, init=False)
    _payment_updated: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        if not self.login_url:
            self.login_url = _join_url(self.base_url, DEFAULT_LOGIN_PATH)
        if not self.account_url:
            self.account_url = _join_url(self.base_url, DEFAULT_ACCOUNT_PATH)
        self._owns_page = self.page is None
        self._bind_page_objects(self.page)

    # ── Context manager ───────────────────────────────────────────────────────

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

    # ── AccountUpdatePort ─────────────────────────────────────────────────────

    def login(self) -> None:
        self._ensure_page()
        self.login_page.open(self.login_url)
        self.login_page.login(self.username, self.password)
        self._login_completed = True

    def complete_mfa(self) -> None:
        self._require_logged_in()
        self.mfa_page.verify(self.mfa_code)
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
        """Close Playwright resources and reset state for a clean re-entry."""
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

    # ── Private helpers ───────────────────────────────────────────────────────

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
