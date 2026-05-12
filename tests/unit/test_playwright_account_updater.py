from __future__ import annotations

import pytest

from account_details_update.browser import selectors
from account_details_update.browser.errors import BrowserPageError
from account_details_update.browser.playwright_account_updater import (
    PlaywrightAccountUpdater,
)
from account_details_update.ports import AccountUpdatePort, AccountUpdateResult
from tests.support.browser_fakes import FakePage
from tests.support.fake_data import fake_banking_details, fake_payment_method

_PAYMENT = fake_payment_method()


class FakeClosable:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakePlaywright:
    def __init__(self, browser: FakeBrowser) -> None:
        self.chromium = FakeChromium(browser)
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


class FakeChromium:
    def __init__(self, browser: FakeBrowser) -> None:
        self.browser = browser
        self.launch_kwargs: dict[str, object] | None = None

    def launch(self, **kwargs: object) -> FakeBrowser:
        self.launch_kwargs = kwargs
        return self.browser


class FakeBrowser(FakeClosable):
    def __init__(self, context: FakeContext) -> None:
        super().__init__()
        self.context = context

    def new_context(self) -> FakeContext:
        return self.context


class FakeContext(FakeClosable):
    def __init__(self) -> None:
        super().__init__()
        self.page = FakePage()

    def new_page(self) -> FakePage:
        return self.page


class FakePlaywrightStarter:
    def __init__(self, playwright: FakePlaywright) -> None:
        self.playwright = playwright
        self.started = False

    def start(self) -> FakePlaywright:
        self.started = True
        return self.playwright


class FakePlaywrightFactory:
    def __init__(self) -> None:
        self.context = FakeContext()
        self.browser = FakeBrowser(self.context)
        self.playwright = FakePlaywright(self.browser)
        self.starter = FakePlaywrightStarter(self.playwright)

    def __call__(self) -> FakePlaywrightStarter:
        return self.starter


def test_playwright_account_updater_orchestrates_page_objects() -> None:
    page = FakePage(
        text_by_selector={
            selectors.BANK_CONFIRMATION: "Banking details updated successfully.",
            selectors.CARD_CONFIRMATION: "Payment method updated successfully.",
        }
    )
    updater = PlaywrightAccountUpdater(
        base_url="https://marketplace.dev-challenge.com",
        username="candidate@dev-challenge.com",
        password="Password123!",
        mfa_code="0000",
        page=page,
    )

    updater.login()
    updater.complete_mfa()
    updater.update_banking_details(fake_banking_details())
    updater.update_payment_method(fake_payment_method())
    result = updater.verify_updates()

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
        ("fill", selectors.MFA_CODE_INPUT, "0000"),
        ("click", selectors.MFA_VERIFY_BUTTON),
        ("wait_for_load_state", "networkidle"),
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
        ("fill", selectors.CARDHOLDER_NAME_INPUT, _PAYMENT.cardholder_name),
        ("fill", selectors.CARD_NUMBER_INPUT, _PAYMENT.card_number),
        ("fill", selectors.CARD_EXPIRY_MONTH_INPUT, _PAYMENT.expiry_month),
        ("fill", selectors.CARD_EXPIRY_YEAR_INPUT, _PAYMENT.expiry_year),
        ("fill", selectors.CARD_CVC_INPUT, _PAYMENT.cvc),
        ("click", selectors.CARD_SAVE_BUTTON),
        ("wait_for_load_state", "networkidle"),
        ("text_content", selectors.BANK_CONFIRMATION),
        ("text_content", selectors.CARD_CONFIRMATION),
    ]
    assert result == AccountUpdateResult(
        banking_summary="Banking details updated successfully.",
        payment_summary="Payment method updated successfully.",
    )


def test_playwright_account_updater_satisfies_account_update_port() -> None:
    updater = PlaywrightAccountUpdater(
        base_url="https://marketplace.dev-challenge.com",
        username="candidate@dev-challenge.com",
        password="Password123!",
        mfa_code="0000",
        page=FakePage(),
    )

    assert isinstance(updater, AccountUpdatePort)


def test_playwright_account_updater_allows_custom_page_urls() -> None:
    page = FakePage()
    updater = PlaywrightAccountUpdater(
        base_url="https://marketplace.dev-challenge.com",
        username="candidate@dev-challenge.com",
        password="Password123!",
        mfa_code="0000",
        page=page,
        login_url="https://marketplace.dev-challenge.com/sign-in",
        account_url="https://marketplace.dev-challenge.com/profile/payment",
    )

    updater.login()
    updater.complete_mfa()
    updater.update_banking_details(fake_banking_details())

    assert (
        "goto",
        "https://marketplace.dev-challenge.com/sign-in",
        {"wait_until": "domcontentloaded"},
    ) in page.calls
    assert (
        "goto",
        "https://marketplace.dev-challenge.com/profile/payment",
        {"wait_until": "domcontentloaded"},
    ) in page.calls


def test_complete_mfa_requires_initialized_page() -> None:
    updater = PlaywrightAccountUpdater(
        base_url="https://marketplace.dev-challenge.com",
        username="candidate@dev-challenge.com",
        password="Password123!",
        mfa_code="0000",
    )

    with pytest.raises(BrowserPageError, match="Playwright page is required"):
        updater.complete_mfa()


def test_complete_mfa_with_injected_page_still_requires_login_first() -> None:
    updater = PlaywrightAccountUpdater(
        base_url="https://marketplace.dev-challenge.com",
        username="candidate@dev-challenge.com",
        password="Password123!",
        mfa_code="0000",
        page=FakePage(),
    )

    with pytest.raises(BrowserPageError, match=r"login\(\) must complete"):
        updater.complete_mfa()


def test_verify_updates_requires_completed_updates() -> None:
    updater = PlaywrightAccountUpdater(
        base_url="https://marketplace.dev-challenge.com",
        username="candidate@dev-challenge.com",
        password="Password123!",
        mfa_code="0000",
        page=FakePage(),
    )

    updater.login()
    updater.complete_mfa()

    with pytest.raises(BrowserPageError, match="must complete before verification"):
        updater.verify_updates()


def test_close_releases_owned_resources_and_unbinds_page() -> None:
    factory = FakePlaywrightFactory()
    updater = PlaywrightAccountUpdater(
        base_url="https://marketplace.dev-challenge.com",
        username="candidate@dev-challenge.com",
        password="Password123!",
        mfa_code="0000",
        _playwright_factory=factory,
    )

    with updater as active:
        assert active.page is factory.context.page

    assert factory.starter.started is True
    assert factory.playwright.chromium.launch_kwargs == {
        "headless": True,
        "slow_mo": 0,
    }

    assert factory.context.closed is True
    assert factory.browser.closed is True
    assert factory.playwright.stopped is True
    assert updater.page is None

    with pytest.raises(BrowserPageError, match="Playwright page is required"):
        updater.complete_mfa()
