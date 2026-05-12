"""Account page object for Playwright automation."""

from __future__ import annotations

from typing import Any

from ...banking_details import BankingDetails
from ...payment_method import PaymentMethod
from ...ports import AccountUpdateResult
from .. import selectors
from .page_ready import require_page, wait_for_page_idle


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
        banking_summary = page.text_content(selectors.BANK_CONFIRMATION) or ""
        payment_summary = page.text_content(selectors.CARD_CONFIRMATION) or ""
        return AccountUpdateResult(
            banking_summary=banking_summary.strip(),
            payment_summary=payment_summary.strip(),
        )
