from __future__ import annotations

from typing import Any


class FakePage:
    """Minimal fake for a Playwright page.

    text_by_selector values may be a plain str (returned every time) or a
    list[str] (values are consumed in order, one per call).
    """

    def __init__(
        self,
        text_by_selector: dict[str, str | list[str]] | None = None,
    ) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self._text_by_selector: dict[str, str | list[str]] = text_by_selector or {}

    def goto(self, url: str, **kwargs: Any) -> None:
        self.calls.append(("goto", url, kwargs))

    def fill(self, selector: str, value: str) -> None:
        self.calls.append(("fill", selector, value))

    def click(self, selector: str) -> None:
        self.calls.append(("click", selector))

    def wait_for_load_state(self, state: str) -> None:
        self.calls.append(("wait_for_load_state", state))

    def wait_for_selector(self, selector: str, **kwargs: Any) -> None:
        self.calls.append(("wait_for_selector", selector, kwargs))

    def text_content(self, selector: str) -> str | None:
        self.calls.append(("text_content", selector))
        value = self._text_by_selector.get(selector)
        if isinstance(value, list):
            return value.pop(0) if value else None
        return value
