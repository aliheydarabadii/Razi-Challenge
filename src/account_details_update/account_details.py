"""Validated account detail input models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


def _luhn_valid(number: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(number)):
        digit = int(ch)
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


@dataclass(frozen=True, slots=True)
class BankingDetails:
    """Banking details required to update an account."""

    routing_number: str
    account_number: str

    def __post_init__(self) -> None:
        if not self.routing_number.isdigit():
            raise ValueError("routing_number must contain only digits")
        if len(self.routing_number) != 9:
            raise ValueError("routing_number must be exactly 9 digits")
        if not self.account_number.isdigit():
            raise ValueError("account_number must contain only digits")
        if not 4 <= len(self.account_number) <= 17:
            raise ValueError("account_number must be 4 to 17 digits")


@dataclass(frozen=True, slots=True)
class PaymentMethod:
    """Payment method details required to update an account."""

    cardholder_name: str
    card_number: str
    expiry_month: str
    expiry_year: str
    cvc: str

    def __post_init__(self) -> None:
        if not self.cardholder_name.strip():
            raise ValueError("cardholder_name is required")
        if not self.card_number.isdigit():
            raise ValueError("card_number must contain only digits")
        if not 13 <= len(self.card_number) <= 19:
            raise ValueError("card_number must be 13 to 19 digits")
        if not _luhn_valid(self.card_number):
            raise ValueError("card_number failed Luhn check")
        if not self.cvc.isdigit() or len(self.cvc) not in {3, 4}:
            raise ValueError("cvc must be 3 or 4 digits")
        if not self.expiry_month.isdigit():
            raise ValueError("expiry_month must contain only digits")
        expiry_month = int(self.expiry_month)
        if not 1 <= expiry_month <= 12:
            raise ValueError("expiry_month must be 1 to 12")
        if not self.expiry_year.isdigit() or len(self.expiry_year) != 4:
            raise ValueError("expiry_year must be a 4 digit year")
        today = date.today()
        if (int(self.expiry_year), expiry_month) < (today.year, today.month):
            raise ValueError("card has already expired")
