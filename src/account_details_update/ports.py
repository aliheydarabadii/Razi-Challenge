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
    """Single-method port: execute the full account update and return results.

    Adapters own the internal sequence (auth, update, verify). Callers
    cannot invoke steps out of order because there is only one step.
    """

    def execute(
        self,
        banking_details: BankingDetails,
        payment_method: PaymentMethod,
    ) -> AccountUpdateResult:
        """Perform the full update and return masked confirmation summaries."""
