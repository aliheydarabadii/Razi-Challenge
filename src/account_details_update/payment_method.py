"""PaymentMethod value object."""

from __future__ import annotations

from dataclasses import InitVar, dataclass
from datetime import date

_CARD_NUMBER_MIN = 13
_CARD_NUMBER_MAX = 19
_VALID_CVC_LENGTHS = {3, 4}


@dataclass(frozen=True, slots=True)
class PaymentMethod:
    """Validated payment method details required to update an account."""

    cardholder_name: str
    card_number: str
    expiry_month: int
    expiry_year: int
    cvc: str
    reference_date: InitVar[date | None] = None

    def __post_init__(self, reference_date: date | None) -> None:
        self._validate_cardholder_name()
        self._validate_card_number()
        self._validate_cvc()
        self._validate_expiry(reference_date or date.today())

    def _validate_cardholder_name(self) -> None:
        if not self.cardholder_name.strip():
            raise ValueError("cardholder_name is required")

    def _validate_card_number(self) -> None:
        if not self.card_number.isdigit():
            raise ValueError("card_number must contain only digits")
        if not _CARD_NUMBER_MIN <= len(self.card_number) <= _CARD_NUMBER_MAX:
            raise ValueError(
                f"card_number must be {_CARD_NUMBER_MIN} to {_CARD_NUMBER_MAX} digits"
            )
        if not _luhn_valid(self.card_number):
            raise ValueError("card_number failed Luhn check")

    def _validate_cvc(self) -> None:
        if not self.cvc.isdigit() or len(self.cvc) not in _VALID_CVC_LENGTHS:
            raise ValueError("cvc must be 3 or 4 digits")

    def _validate_expiry(self, reference_date: date) -> None:
        if not 1 <= self.expiry_month <= 12:
            raise ValueError("expiry_month must be 1 to 12")
        if not 1000 <= self.expiry_year <= 9999:
            raise ValueError("expiry_year must be a 4 digit year")
        card = (self.expiry_year, self.expiry_month)
        if card < (reference_date.year, reference_date.month):
            raise ValueError("card has already expired")


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
