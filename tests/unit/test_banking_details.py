from __future__ import annotations

import pytest

from account_details_update.banking_details import BankingDetails


def test_banking_details_stores_routing_and_account_number() -> None:
    banking = BankingDetails(
        routing_number="123456789",
        account_number="1234567890",
    )

    assert banking.routing_number == "123456789"
    assert banking.account_number == "1234567890"


def test_routing_number_must_be_exactly_9_digits() -> None:
    with pytest.raises(ValueError, match="routing_number must be exactly 9 digits"):
        BankingDetails(routing_number="12345678", account_number="1234567890")


def test_routing_number_must_contain_only_digits() -> None:
    with pytest.raises(ValueError, match="routing_number must contain only digits"):
        BankingDetails(routing_number="12345678A", account_number="1234567890")


def test_account_number_must_be_between_4_and_17_digits() -> None:
    with pytest.raises(ValueError, match="account_number must be 4 to 17 digits"):
        BankingDetails(routing_number="123456789", account_number="123")
