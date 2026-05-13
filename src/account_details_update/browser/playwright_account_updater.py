"""Playwright adapter for account detail updates."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any

from ..banking_details import BankingDetails
from ..payment_method import PaymentMethod
from ..ports import AccountUpdateResult
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

    # ── Runtime state ─────────────────────────────────────────────────────────

    _owns_page: bool = field(default=False, init=False)
    _playwright: Any | None = field(default=None, init=False)
    _browser: Any | None = field(default=None, init=False)
    _context: Any | None = field(default=None, init=False)
    login_page: LoginPage = field(init=False)
    mfa_page: MfaPage = field(init=False)
    account_page: AccountPage = field(init=False)

    # ── AccountUpdatePort ─────────────────────────────────────────────────────

    def execute(
        self,
        banking_details: BankingDetails,
        payment_method: PaymentMethod,
    ) -> AccountUpdateResult:
        self._ensure_page()
        self._authenticate()
        return self._perform_updates(banking_details, payment_method)

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

    # ── Private helpers ───────────────────────────────────────────────────────

    def _authenticate(self) -> None:
        self.login_page.open(self.login_url)
        self.login_page.login(self.username, self.password)
        self.mfa_page.verify(self.mfa_code)

    def _perform_updates(
        self,
        banking_details: BankingDetails,
        payment_method: PaymentMethod,
    ) -> AccountUpdateResult:
        self.account_page.open(self.account_url)
        self.account_page.update_banking(banking_details)
        self.account_page.update_payment(payment_method)
        return self.account_page.verify_updates()

    def _ensure_page(self) -> None:
        if self.page is None:
            self._start_browser()

    def _start_browser(self) -> None:
        self._playwright = self._resolve_factory()().start()
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

    def _resolve_factory(self) -> Callable[[], Any]:
        if self._playwright_factory is not None:
            return self._playwright_factory
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is required for browser automation. Install project "
                "dependencies and run `playwright install chromium`."
            ) from exc
        return sync_playwright

    def _bind_page_objects(self, page: Any | None) -> None:
        self.login_page = LoginPage(page)
        self.mfa_page = MfaPage(page)
        self.account_page = AccountPage(page)

    # ── Protocol / initialisation (boilerplate) ───────────────────────────────

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        if not self.login_url:
            self.login_url = _join_url(self.base_url, DEFAULT_LOGIN_PATH)
        if not self.account_url:
            self.account_url = _join_url(self.base_url, DEFAULT_ACCOUNT_PATH)
        self._owns_page = self.page is None
        self._bind_page_objects(self.page)

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


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url}/{path.lstrip('/')}"
