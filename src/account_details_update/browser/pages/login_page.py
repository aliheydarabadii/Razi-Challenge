"""Login page object for Playwright automation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .. import selectors
from .page_ready import require_page, wait_for_page_idle


@dataclass(frozen=True, slots=True)
class LoginPage:
    """Page object for the login screen."""

    page: Any | None = None

    def open(self, url: str) -> None:
        page = require_page(self.page)
        page.goto(url, wait_until="domcontentloaded")
        wait_for_page_idle(page)

    def login(self, username: str, password: str) -> None:
        page = require_page(self.page)
        page.fill(selectors.EMAIL_INPUT, username)
        page.fill(selectors.PASSWORD_INPUT, password)
        page.click(selectors.LOGIN_BUTTON)
        wait_for_page_idle(page)
