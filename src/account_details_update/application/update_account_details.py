"""Use case: update a user's banking details and payment method."""

from __future__ import annotations

from ..banking_details import BankingDetails
from ..payment_method import PaymentMethod
from ..ports import AccountUpdatePort, AccountUpdateResult


class UpdateAccountDetails:
    """Application-layer entry point for the account update workflow."""

    def __init__(self, account_update_port: AccountUpdatePort) -> None:
        self._port = account_update_port

    def execute(
        self,
        banking_details: BankingDetails,
        payment_method: PaymentMethod,
    ) -> AccountUpdateResult:
        return self._port.execute(banking_details, payment_method)
