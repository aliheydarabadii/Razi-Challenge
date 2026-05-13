from __future__ import annotations

from account_details_update.browser import selectors
from account_details_update.browser.pages.account_page import AccountPage
from account_details_update.browser.pages.login_page import LoginPage
from account_details_update.browser.pages.mfa_page import MfaPage
from tests.support.browser_fakes import FakePage
from tests.support.fake_data import fake_banking_details, fake_payment_method

_PAYMENT = fake_payment_method()
_BANKING_TOAST = "Banking details saved"
_PAYMENT_TOAST = "Payment method saved"


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


def test_account_page_update_banking_waits_for_toast_and_returns_text() -> None:
    page = FakePage(text_by_selector={selectors.SAVE_CONFIRMATION: _BANKING_TOAST})

    summary = AccountPage(page).update_banking(fake_banking_details())

    assert summary == _BANKING_TOAST
    assert (
        "wait_for_selector",
        selectors.SAVE_CONFIRMATION,
        {"state": "visible"},
    ) in page.calls


def test_account_page_update_payment_waits_for_toast_and_returns_text() -> None:
    page = FakePage(text_by_selector={selectors.SAVE_CONFIRMATION: _PAYMENT_TOAST})

    summary = AccountPage(page).update_payment(fake_payment_method())

    assert summary == _PAYMENT_TOAST
    assert (
        "wait_for_selector",
        selectors.SAVE_CONFIRMATION,
        {"state": "visible"},
    ) in page.calls


def test_account_page_fills_and_submits_banking_form() -> None:
    page = FakePage(text_by_selector={selectors.SAVE_CONFIRMATION: _BANKING_TOAST})

    AccountPage(page).update_banking(fake_banking_details())

    assert ("fill", selectors.BANK_ROUTING_INPUT, "123456789") in page.calls
    assert ("fill", selectors.BANK_ACCOUNT_INPUT, "1234567890") in page.calls
    assert ("click", selectors.BANK_SAVE_BUTTON) in page.calls


def test_account_page_fills_and_submits_payment_form() -> None:
    page = FakePage(text_by_selector={selectors.SAVE_CONFIRMATION: _PAYMENT_TOAST})

    AccountPage(page).update_payment(fake_payment_method())

    cardholder = _PAYMENT.cardholder_name
    assert ("fill", selectors.CARDHOLDER_NAME_INPUT, cardholder) in page.calls
    assert ("fill", selectors.CARD_NUMBER_INPUT, _PAYMENT.card_number) in page.calls
    assert ("click", selectors.CARD_SAVE_BUTTON) in page.calls
