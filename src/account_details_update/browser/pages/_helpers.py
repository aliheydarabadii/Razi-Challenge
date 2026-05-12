"""Helpers shared by Playwright page objects."""

from __future__ import annotations

from typing import Any


class BrowserPageError(RuntimeError):
    """Raised when a browser page object cannot perform an action."""


def require_page(page: Any | None) -> Any:
    if page is None:
        raise BrowserPageError(
            "A Playwright page is required. Pass a page to the adapter or let "
            "PlaywrightAccountUpdater create one."
        )
    return page


def wait_for_page_idle(page: Any) -> None:
    wait_for_load_state = getattr(page, "wait_for_load_state", None)
    if callable(wait_for_load_state):
        wait_for_load_state("networkidle")
