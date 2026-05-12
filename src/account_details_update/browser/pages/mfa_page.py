"""MFA page placeholder for future Playwright automation."""

from __future__ import annotations

from typing import Any


class MfaPage:
    """Placeholder page object for the MFA screen."""

    def __init__(self, page: Any | None = None) -> None:
        self.page = page

    def verify(self, code: str) -> None:
        # TODO: Fill the MFA code and submit using verified selectors.
        raise NotImplementedError("MFA verification is not implemented yet.")
