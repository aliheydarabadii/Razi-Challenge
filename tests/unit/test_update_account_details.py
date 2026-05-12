from __future__ import annotations

from account_details_update.application.update_account_details import (
    UpdateAccountDetails,
)
from account_details_update.banking_details import BankingDetails
from account_details_update.payment_method import PaymentMethod
from account_details_update.ports import AccountUpdateResult


class FakeAccountUpdatePort:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def login(self) -> None:
        self.calls.append("login")

    def complete_mfa(self) -> None:
        self.calls.append("complete_mfa")

    def update_banking_details(self, banking_details: BankingDetails) -> None:
        self.calls.append("update_banking_details")

    def update_payment_method(self, payment_method: PaymentMethod) -> None:
        self.calls.append("update_payment_method")

    def verify_updates(self) -> AccountUpdateResult:
        self.calls.append("verify_updates")
        return AccountUpdateResult(
            banking_summary="Bank account ending in 7890 updated",
            payment_summary="Card ending in 4242 updated",
        )


def test_execute_orchestrates_account_update_steps_in_order() -> None:
    port = FakeAccountUpdatePort()
    use_case = UpdateAccountDetails(account_update_port=port)

    result = use_case.execute(
        banking_details=BankingDetails(
            routing_number="123456789",
            account_number="1234567890",
        ),
        payment_method=PaymentMethod(
            cardholder_name="Test Candidate",
            card_number="4242424242424242",
            expiry_month="12",
            expiry_year="2030",
            cvc="123",
        ),
    )

    assert port.calls == [
        "login",
        "complete_mfa",
        "update_banking_details",
        "update_payment_method",
        "verify_updates",
    ]
    assert result == AccountUpdateResult(
        banking_summary="Bank account ending in 7890 updated",
        payment_summary="Card ending in 4242 updated",
    )
