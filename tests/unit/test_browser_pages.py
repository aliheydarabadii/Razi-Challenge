from __future__ import annotations

from account_details_update.account_update_result import AccountUpdateResult
from account_details_update.browser import selectors
from account_details_update.browser.pages.account_page import AccountPage
from account_details_update.browser.pages.login_page import LoginPage
from account_details_update.browser.pages.mfa_page import MfaPage
from tests.support.browser_fakes import FakePage
from tests.support.fake_data import fake_banking_details, fake_payment_method


def test_login_page_opens_and_submits_credentials() -> None:
    page = FakePage()
    login_page = LoginPage(page)

    login_page.open("https://marketplace.dev-challenge.com")
    login_page.login("candidate@dev-challenge.com", "Password123!")

    assert (
        "goto",
        "https://marketplace.dev-challenge.com",
        {"wait_until": "domcontentloaded"},
    ) in page.calls
    assert ("fill", selectors.EMAIL_INPUT, "candidate@dev-challenge.com") in page.calls
    assert ("fill", selectors.PASSWORD_INPUT, "Password123!") in page.calls
    assert ("click", selectors.LOGIN_BUTTON) in page.calls


def test_mfa_page_submits_code() -> None:
    page = FakePage()

    MfaPage(page).verify("000000")

    assert page.calls == [
        ("fill", selectors.MFA_CODE_INPUT, "000000"),
        ("click", selectors.MFA_VERIFY_BUTTON),
        ("wait_for_load_state", "networkidle"),
    ]


def test_account_page_updates_details_and_reads_confirmations() -> None:
    page = FakePage(
        text_by_selector={
            selectors.BANKING_SUMMARY: "Bank account ending in 7890 updated",
            selectors.PAYMENT_SUMMARY: "Card ending in 4242 updated",
        }
    )
    account_page = AccountPage(page)

    account_page.update_banking(fake_banking_details())
    account_page.update_payment(fake_payment_method())
    result = account_page.verify_updates()

    assert ("fill", selectors.BANK_ROUTING_INPUT, "123456789") in page.calls
    assert ("fill", selectors.BANK_ACCOUNT_INPUT, "1234567890") in page.calls
    assert ("click", selectors.BANK_SAVE_BUTTON) in page.calls
    assert ("fill", selectors.CARD_NUMBER_INPUT, "4242424242424242") in page.calls
    assert ("click", selectors.CARD_SAVE_BUTTON) in page.calls
    assert result == AccountUpdateResult(
        banking_summary="Bank account ending in 7890 updated",
        payment_summary="Card ending in 4242 updated",
    )
