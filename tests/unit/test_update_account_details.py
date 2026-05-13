from __future__ import annotations

from account_details_update.application.commands import UpdateAccountDetailsCommand
from account_details_update.application.update_account_details import (
    UpdateAccountDetailsHandler,
)
from account_details_update.banking_details import BankingDetails
from account_details_update.payment_method import PaymentMethod
from account_details_update.ports import AccountUpdateResult


class FakeAccountUpdatePort:
    def __init__(self) -> None:
        self.called = False
        self.received_banking: BankingDetails | None = None
        self.received_payment: PaymentMethod | None = None

    def execute(
        self,
        banking_details: BankingDetails,
        payment_method: PaymentMethod,
    ) -> AccountUpdateResult:
        self.called = True
        self.received_banking = banking_details
        self.received_payment = payment_method
        return AccountUpdateResult(
            banking_summary="Bank account ending in 7890 updated",
            payment_summary="Card ending in 4242 updated",
        )


def test_handle_delegates_command_to_port() -> None:
    port = FakeAccountUpdatePort()
    handler = UpdateAccountDetailsHandler(port=port)
    banking = BankingDetails(routing_number="123456789", account_number="1234567890")
    payment = PaymentMethod(
        cardholder_name="Test Candidate",
        card_number="4242424242424242",
        expiry_month="12",
        expiry_year="2035",
        cvc="123",
    )
    command = UpdateAccountDetailsCommand(
        banking_details=banking,
        payment_method=payment,
    )

    result = handler.handle(command)

    assert port.called
    assert port.received_banking is banking
    assert port.received_payment is payment
    assert result == AccountUpdateResult(
        banking_summary="Bank account ending in 7890 updated",
        payment_summary="Card ending in 4242 updated",
    )
