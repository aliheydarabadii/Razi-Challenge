from __future__ import annotations

from account_details_update import AccountUpdateResult
from account_details_update.browser import selectors
from account_details_update.browser.pages.account_page import AccountPage
from account_details_update.browser.pages.login_page import LoginPage
from account_details_update.browser.pages.mfa_page import MfaPage
from tests.support.browser_fakes import FakePage
from tests.support.fake_data import fake_banking_details, fake_payment_method


def test_login_page_opens_and_submits_credentials() -> None:
    page = FakePage()
    login_page = LoginPage(page)

    login_page.open("https://marketplace.dev-challenge.com/login")
    login_page.login("candidate@dev-challenge.com", "Password123!")

    assert page.calls == [
        (
            "goto",
            "https://marketplace.dev-challenge.com/login",
            {"wait_until": "domcontentloaded"},
        ),
        ("wait_for_load_state", "networkidle"),
        ("fill", selectors.EMAIL_INPUT, "candidate@dev-challenge.com"),
        ("fill", selectors.PASSWORD_INPUT, "Password123!"),
        ("click", selectors.LOGIN_BUTTON),
        ("wait_for_load_state", "networkidle"),
    ]


def test_mfa_page_submits_code() -> None:
    page = FakePage()

    MfaPage(page).verify("0000")

    assert page.calls == [
        ("fill", selectors.MFA_CODE_INPUT, "0000"),
        ("click", selectors.MFA_VERIFY_BUTTON),
        ("wait_for_load_state", "networkidle"),
    ]


def test_account_page_updates_details_and_returns_fixed_confirmation() -> None:
    page = FakePage()
    account_page = AccountPage(page)

    account_page.open("https://marketplace.dev-challenge.com/app/account")
    account_page.update_banking(fake_banking_details())
    account_page.update_payment(fake_payment_method())
    result = account_page.verify_updates()

    assert page.calls == [
        (
            "goto",
            "https://marketplace.dev-challenge.com/app/account",
            {"wait_until": "domcontentloaded"},
        ),
        ("wait_for_load_state", "networkidle"),
        ("fill", selectors.BANK_ROUTING_INPUT, "123456789"),
        ("fill", selectors.BANK_ACCOUNT_INPUT, "1234567890"),
        ("click", selectors.BANK_SAVE_BUTTON),
        ("wait_for_load_state", "networkidle"),
        ("fill", selectors.CARDHOLDER_NAME_INPUT, "Test Candidate"),
        ("fill", selectors.CARD_NUMBER_INPUT, "4242424242424242"),
        ("fill", selectors.CARD_EXPIRY_MONTH_INPUT, "12"),
        ("fill", selectors.CARD_EXPIRY_YEAR_INPUT, "2030"),
        ("fill", selectors.CARD_CVC_INPUT, "123"),
        ("click", selectors.CARD_SAVE_BUTTON),
        ("wait_for_load_state", "networkidle"),
    ]
    assert result == AccountUpdateResult(
        banking_summary="Banking details updated successfully.",
        payment_summary="Payment method updated successfully.",
    )
