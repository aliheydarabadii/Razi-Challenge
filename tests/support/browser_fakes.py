from __future__ import annotations

from typing import Any


class FakePage:
    def __init__(self, text_by_selector: dict[str, str] | None = None) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.text_by_selector = text_by_selector or {}

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
        return self.text_by_selector.get(selector)
