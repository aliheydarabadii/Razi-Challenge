"""BankingDetails value object."""

from __future__ import annotations

from dataclasses import dataclass

_ROUTING_NUMBER_LENGTH = 9
_ACCOUNT_NUMBER_MIN = 4
_ACCOUNT_NUMBER_MAX = 17


@dataclass(frozen=True, slots=True)
class BankingDetails:
    """Validated banking details required to update an account."""

    routing_number: str
    account_number: str

    def __post_init__(self) -> None:
        self._validate_routing_number()
        self._validate_account_number()

    def _validate_routing_number(self) -> None:
        if not self.routing_number.isdigit():
            raise ValueError("routing_number must contain only digits")
        if len(self.routing_number) != _ROUTING_NUMBER_LENGTH:
            raise ValueError(
                f"routing_number must be exactly {_ROUTING_NUMBER_LENGTH} digits"
            )

    def _validate_account_number(self) -> None:
        if not self.account_number.isdigit():
            raise ValueError("account_number must contain only digits")
        if not _ACCOUNT_NUMBER_MIN <= len(self.account_number) <= _ACCOUNT_NUMBER_MAX:
            raise ValueError(
                f"account_number must be {_ACCOUNT_NUMBER_MIN} to"
                f" {_ACCOUNT_NUMBER_MAX} digits"
            )
