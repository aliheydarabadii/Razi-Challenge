"""Integration test for the Playwright browser adapter.

Runs the full end-to-end flow against the live challenge site. Requires
Playwright + Chromium to be installed (`playwright install chromium`).

Run with:
    INTEGRATION_TESTS=1 pytest tests/integration/test_browser_integration.py -v

To watch the browser:
    INTEGRATION_TESTS=1 HEADED=true SLOW_MO_MS=500 \
        pytest tests/integration/test_browser_integration.py -v
"""

from __future__ import annotations

import pytest

from account_details_update.application.commands import UpdateAccountDetailsCommand
from account_details_update.application.update_account_details import (
    UpdateAccountDetailsHandler,
)
from account_details_update.banking_details import BankingDetails
from account_details_update.bootstrap.settings import Settings
from account_details_update.browser.playwright_account_updater import (
    PlaywrightAccountUpdater,
)
from account_details_update.payment_method import PaymentMethod


@pytest.fixture(scope="module")
def settings() -> Settings:
    return Settings()


def test_full_browser_flow(settings: Settings) -> None:
    """Complete sign-in → MFA → banking update → payment update → verify."""
    pytest.importorskip(
        "playwright",
        reason="playwright not installed — run `playwright install chromium` first",
    )

    command = UpdateAccountDetailsCommand(
        banking_details=BankingDetails(
            routing_number=settings.bank_routing,
            account_number=settings.bank_account,
        ),
        payment_method=PaymentMethod(
            cardholder_name=settings.cardholder_name,
            card_number=settings.card_number,
            expiry_month=settings.card_expiry_month,
            expiry_year=settings.card_expiry_year,
            cvc=settings.card_cvc,
        ),
    )

    with PlaywrightAccountUpdater(
        base_url=settings.challenge_base_url,
        username=settings.username,
        password=settings.password.get_secret_value(),
        mfa_code=settings.mfa_code.get_secret_value(),
        headed=settings.headed,
        slow_mo_ms=settings.slow_mo_ms,
    ) as updater:
        result = UpdateAccountDetailsHandler(port=updater).handle(command)

    assert result.banking_summary, "expected a non-empty banking confirmation"
    assert result.payment_summary, "expected a non-empty payment confirmation"
