"""Playwright browser session — lifecycle management."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class BrowserSession:
    """Opens and owns a Playwright browser page.

    Use ensure_ready() before accessing .page.
    Use the context-manager protocol or close() to release resources.
    Inject a page via with_page() to skip browser launch in tests.
    """

    headed: bool = False
    slow_mo_ms: int = 0
    _playwright_factory: Callable[[], Any] | None = field(
        default=None, kw_only=True
    )

    page: Any | None = field(default=None, init=False)
    _owns_page: bool = field(default=False, init=False)
    _playwright: Any | None = field(default=None, init=False)
    _browser: Any | None = field(default=None, init=False)
    _context: Any | None = field(default=None, init=False)

    @classmethod
    def with_page(cls, page: Any) -> BrowserSession:
        """Return a session pre-loaded with an existing page (for testing)."""
        session = cls()
        session.page = page
        return session

    def ensure_ready(self) -> None:
        """Ensure a page is available; start the browser if not."""
        if self.page is None:
            self._start()

    def close(self) -> None:
        """Close all browser resources and reset session state."""
        if self._context is not None:
            self._context.close()
            self._context = None
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None
        if self._owns_page:
            self.page = None

    # ── Private helpers ───────────────────────────────────────────────────────

    def _start(self) -> None:
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
