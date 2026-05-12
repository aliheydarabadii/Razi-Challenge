"""Page-readiness guards and synchronisation primitives."""

from __future__ import annotations

from typing import Any, Protocol

from ..errors import BrowserPageError


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
