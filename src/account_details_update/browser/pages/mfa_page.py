"""MFA page object for Playwright automation."""

from __future__ import annotations

from typing import Any

from .. import selectors
from ._helpers import require_page, wait_for_page_idle


class MfaPage:
    """Page object for the MFA screen."""

    def __init__(self, page: Any | None = None) -> None:
        self.page = page

    def verify(self, code: str) -> None:
        page = require_page(self.page)
        page.fill(selectors.MFA_CODE_INPUT, code)
        page.click(selectors.MFA_VERIFY_BUTTON)
        wait_for_page_idle(page)
