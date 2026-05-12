"""Port and result type for the account-update use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .banking_details import BankingDetails
from .payment_method import PaymentMethod


@dataclass(frozen=True, slots=True)
class AccountUpdateResult:
    """Masked confirmation summaries returned after a successful update."""

    banking_summary: str
    payment_summary: str


@runtime_checkable
class AccountUpdatePort(Protocol):
    """Interface required by the core update use case."""

    def login(self) -> None:
        """Authenticate with the account details system."""

    def complete_mfa(self) -> None:
        """Complete multi-factor authentication."""

    def update_banking_details(self, banking_details: BankingDetails) -> None:
        """Update banking details."""

    def update_payment_method(self, payment_method: PaymentMethod) -> None:
        """Update payment method details."""

    def verify_updates(self) -> AccountUpdateResult:
        """Return masked confirmation summaries for the updates."""
