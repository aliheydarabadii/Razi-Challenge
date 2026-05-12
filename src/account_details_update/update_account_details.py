"""Use case for updating account details."""

from __future__ import annotations

from .account_update_result import AccountUpdateResult
from .banking_details import BankingDetails
from .payment_method import PaymentMethod
from .ports import AccountUpdatePort


class UpdateAccountDetails:
    """Orchestrates the full account details update workflow."""

    def __init__(self, account_update_port: AccountUpdatePort) -> None:
        self._account_update_port = account_update_port

    def execute(
        self,
        banking_details: BankingDetails,
        payment_method: PaymentMethod,
    ) -> AccountUpdateResult:
        self._account_update_port.login()
        self._account_update_port.complete_mfa()
        self._account_update_port.update_banking_details(banking_details)
        self._account_update_port.update_payment_method(payment_method)
        return self._account_update_port.verify_updates()
