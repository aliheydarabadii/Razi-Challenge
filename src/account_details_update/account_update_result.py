"""Result model for account detail updates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AccountUpdateResult:
    """Masked update confirmation summaries."""

    banking_summary: str
    payment_summary: str
