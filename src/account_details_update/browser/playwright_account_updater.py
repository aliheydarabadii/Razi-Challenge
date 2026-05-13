"""Playwright adapter for account detail updates."""

from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType

from ..banking_details import BankingDetails
from ..payment_method import PaymentMethod
from ..ports import AccountUpdateResult
from .pages.account_page import AccountPage
from .pages.login_page import LoginPage
from .pages.mfa_page import MfaPage
from .session import BrowserSession

DEFAULT_LOGIN_PATH = "/login"
DEFAULT_ACCOUNT_PATH = "/app/account"


@dataclass(frozen=True, slots=True)
class PlaywrightAccountUpdater:
    """Browser adapter that structurally implements AccountUpdatePort."""

    base_url: str
    username: str
    password: str
    mfa_code: str
    session: BrowserSession
    login_url: str = ""
    account_url: str = ""

    # ── AccountUpdatePort ─────────────────────────────────────────────────────

    def execute(
        self,
        banking_details: BankingDetails,
        payment_method: PaymentMethod,
    ) -> AccountUpdateResult:
        self.session.ensure_ready()
        self._authenticate()
        return self._perform_updates(banking_details, payment_method)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _authenticate(self) -> None:
        url = self.login_url or _join_url(self.base_url, DEFAULT_LOGIN_PATH)
        login = LoginPage(self.session.page)
        login.open(url)
        login.login(self.username, self.password)
        MfaPage(self.session.page).verify(self.mfa_code)

    def _perform_updates(
        self,
        banking_details: BankingDetails,
        payment_method: PaymentMethod,
    ) -> AccountUpdateResult:
        url = self.account_url or _join_url(self.base_url, DEFAULT_ACCOUNT_PATH)
        account = AccountPage(self.session.page)
        account.open(url)
        account.update_banking(banking_details)
        account.update_payment(payment_method)
        return account.verify_updates()

    # ── Protocol / initialisation (boilerplate) ───────────────────────────────

    def __enter__(self) -> PlaywrightAccountUpdater:
        self.session.ensure_ready()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.session.close()


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"
