"""Account page object for Playwright automation."""

from __future__ import annotations

from typing import Any

from ...account_details import BankingDetails, PaymentMethod
from ...account_update_result import AccountUpdateResult
from .. import selectors
from ._helpers import read_required_text, require_page, wait_for_page_idle


class AccountPage:
    """Page object for account update screens."""

    def __init__(self, page: Any | None = None) -> None:
        self.page = page

    def open(self, url: str) -> None:
        page = require_page(self.page)
        page.goto(url, wait_until="domcontentloaded")
        wait_for_page_idle(page)

    def update_banking(self, banking_details: BankingDetails) -> None:
        page = require_page(self.page)
        page.fill(selectors.BANK_ROUTING_INPUT, banking_details.routing_number)
        page.fill(selectors.BANK_ACCOUNT_INPUT, banking_details.account_number)
        page.click(selectors.BANK_SAVE_BUTTON)
        wait_for_page_idle(page)

    def update_payment(self, payment_method: PaymentMethod) -> None:
        page = require_page(self.page)
        page.fill(selectors.CARDHOLDER_NAME_INPUT, payment_method.cardholder_name)
        page.fill(selectors.CARD_NUMBER_INPUT, payment_method.card_number)
        page.fill(selectors.CARD_EXPIRY_MONTH_INPUT, payment_method.expiry_month)
        page.fill(selectors.CARD_EXPIRY_YEAR_INPUT, payment_method.expiry_year)
        page.fill(selectors.CARD_CVC_INPUT, payment_method.cvc)
        page.click(selectors.CARD_SAVE_BUTTON)
        wait_for_page_idle(page)

    def verify_updates(self) -> AccountUpdateResult:
        page = require_page(self.page)
        return AccountUpdateResult(
            banking_summary=read_required_text(page, selectors.BANKING_SUMMARY),
            payment_summary=read_required_text(page, selectors.PAYMENT_SUMMARY),
        )
