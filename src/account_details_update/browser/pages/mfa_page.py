"""MFA page object for Playwright automation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .. import selectors
from .page_ready import require_page, wait_for_page_idle


@dataclass(frozen=True, slots=True)
class MfaPage:
    """Page object for the MFA screen."""

    page: Any | None = None

    def verify(self, code: str) -> None:
        page = require_page(self.page)
        page.fill(selectors.MFA_CODE_INPUT, code)
        page.click(selectors.MFA_VERIFY_BUTTON)
        wait_for_page_idle(page)
