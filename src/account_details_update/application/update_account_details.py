"""Command handler: update a user's banking details and payment method."""

from __future__ import annotations

from ..ports import AccountUpdatePort, AccountUpdateResult
from .commands import UpdateAccountDetailsCommand


class UpdateAccountDetailsHandler:
    """Processes UpdateAccountDetailsCommand via the injected port."""

    def __init__(self, port: AccountUpdatePort) -> None:
        self._port = port

    def handle(self, command: UpdateAccountDetailsCommand) -> AccountUpdateResult:
        return self._port.execute(
            command.banking_details,
            command.payment_method,
        )
