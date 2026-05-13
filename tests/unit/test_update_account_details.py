from __future__ import annotations

from account_details_update.application.commands import UpdateAccountDetailsCommand
from account_details_update.application.update_account_details import (
    UpdateAccountDetailsHandler,
)
from account_details_update.banking_details import BankingDetails
from account_details_update.payment_method import PaymentMethod
from account_details_update.ports import AccountUpdateResult
from tests.support.fake_data import fake_banking_details, fake_payment_method


class FakeAccountUpdatePort:
    def __init__(self) -> None:
        self.received_banking: BankingDetails | None = None
        self.received_payment: PaymentMethod | None = None

    def execute(
        self,
        banking_details: BankingDetails,
        payment_method: PaymentMethod,
    ) -> AccountUpdateResult:
        self.received_banking = banking_details
        self.received_payment = payment_method
        return AccountUpdateResult(
            banking_summary="Bank account ending in 7890 updated",
            payment_summary="Card ending in 4242 updated",
        )


def test_handle_delegates_command_to_port() -> None:
    port = FakeAccountUpdatePort()
    handler = UpdateAccountDetailsHandler(port=port)
    banking = fake_banking_details()
    payment = fake_payment_method()
    command = UpdateAccountDetailsCommand(
        banking_details=banking,
        payment_method=payment,
    )

    result = handler.handle(command)

    assert port.received_banking is banking
    assert port.received_payment is payment
    assert result == AccountUpdateResult(
        banking_summary="Bank account ending in 7890 updated",
        payment_summary="Card ending in 4242 updated",
    )
