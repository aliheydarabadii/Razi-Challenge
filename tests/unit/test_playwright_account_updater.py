from __future__ import annotations

from account_details_update.account_update_result import AccountUpdateResult
from account_details_update.browser import selectors
from account_details_update.browser.playwright_account_updater import (
    PlaywrightAccountUpdater,
)
from tests.support.browser_fakes import FakePage
from tests.support.fake_data import fake_banking_details, fake_payment_method


def test_playwright_account_updater_orchestrates_page_objects() -> None:
    page = FakePage(
        text_by_selector={
            selectors.BANKING_SUMMARY: "Bank account ending in 7890 updated",
            selectors.PAYMENT_SUMMARY: "Card ending in 4242 updated",
        }
    )
    updater = PlaywrightAccountUpdater(
        base_url="https://marketplace.dev-challenge.com",
        username="candidate@dev-challenge.com",
        password="Password123!",
        mfa_code="000000",
        page=page,
    )

    updater.login()
    updater.complete_mfa()
    updater.update_banking_details(fake_banking_details())
    updater.update_payment_method(fake_payment_method())
    result = updater.verify_updates()

    assert ("click", selectors.LOGIN_BUTTON) in page.calls
    assert ("click", selectors.MFA_VERIFY_BUTTON) in page.calls
    assert ("click", selectors.BANK_SAVE_BUTTON) in page.calls
    assert ("click", selectors.CARD_SAVE_BUTTON) in page.calls
    assert result == AccountUpdateResult(
        banking_summary="Bank account ending in 7890 updated",
        payment_summary="Card ending in 4242 updated",
    )
