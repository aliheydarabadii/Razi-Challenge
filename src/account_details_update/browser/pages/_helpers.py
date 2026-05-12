"""Helpers shared by Playwright page objects."""

from __future__ import annotations

from typing import Any, Protocol


class BrowserPageError(RuntimeError):
    """Raised when a browser page object cannot perform an action."""


class _PageWithLoadState(Protocol):
    def wait_for_load_state(self, state: str) -> None: ...


def require_page(page: Any | None) -> Any:
    if page is None:
        raise BrowserPageError(
            "A Playwright page is required. Pass a page to the adapter or let "
            "PlaywrightAccountUpdater create one."
        )
    return page


def wait_for_page_idle(page: _PageWithLoadState) -> None:
    page.wait_for_load_state("networkidle")
