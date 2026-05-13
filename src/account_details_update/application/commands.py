"""Application-layer command objects."""

from __future__ import annotations

from dataclasses import dataclass

from ..banking_details import BankingDetails
from ..payment_method import PaymentMethod


@dataclass(frozen=True, slots=True)
class UpdateAccountDetailsCommand:
    """Encapsulates the intent to update banking and payment details."""

    banking_details: BankingDetails
    payment_method: PaymentMethod
