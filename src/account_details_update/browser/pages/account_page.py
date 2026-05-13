"""Account page object for Playwright automation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...banking_details import BankingDetails
from ...payment_method import PaymentMethod
from .. import selectors
from .page_ready import require_page, wait_for_page_idle


@dataclass(frozen=True, slots=True)
class AccountPage:
    """Page object for account update screens."""

    page: Any | None = None

    def open(self, url: str) -> None:
        page = require_page(self.page)
        page.goto(url, wait_until="domcontentloaded")
        wait_for_page_idle(page)

    def update_banking(self, banking_details: BankingDetails) -> str:
        """Fill and submit the banking form; returns the confirmation toast text."""
        page = require_page(self.page)
        page.fill(selectors.BANK_ROUTING_INPUT, banking_details.routing_number)
        page.fill(selectors.BANK_ACCOUNT_INPUT, banking_details.account_number)
        page.click(selectors.BANK_SAVE_BUTTON)
        page.wait_for_selector(selectors.BANK_CONFIRMATION, state="visible")
        return (page.text_content(selectors.BANK_CONFIRMATION) or "").strip()

    def update_payment(self, payment_method: PaymentMethod) -> str:
        """Fill and submit the payment form; returns the confirmation toast text."""
        page = require_page(self.page)
        page.fill(selectors.CARDHOLDER_NAME_INPUT, payment_method.cardholder_name)
        page.fill(selectors.CARD_NUMBER_INPUT, payment_method.card_number)
        page.fill(selectors.CARD_EXPIRY_MONTH_INPUT, payment_method.expiry_month)
        page.fill(selectors.CARD_EXPIRY_YEAR_INPUT, payment_method.expiry_year)
        page.fill(selectors.CARD_CVC_INPUT, payment_method.cvc)
        page.click(selectors.CARD_SAVE_BUTTON)
        page.wait_for_selector(selectors.CARD_CONFIRMATION, state="visible")
        return (page.text_content(selectors.CARD_CONFIRMATION) or "").strip()
