from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from account_details_update.account_update_result import AccountUpdateResult
from account_details_update.bootstrap.cli import _build_domain_objects, build_parser, main
from account_details_update.bootstrap.settings import Settings
from account_details_update.http_api.errors import RaziApiError

_MOCK_RESULT = AccountUpdateResult(
    banking_summary="Routing •••••6789 — Account ••••••7890",
    payment_summary="Visa ending in 4242 (12/2030)",
)


def _test_settings(**overrides: object) -> Settings:
    base: dict[str, object] = dict(
        challenge_base_url="https://example.com",
        api_base_url="https://api.example.com",
        username="u@example.com",
        password="pass",
        mfa_code="1234",
        supabase_url="",
        supabase_anon_key="",
        bank_routing="123456789",
        bank_account="1234567890",
        cardholder_name="Test User",
        card_number="4242424242424242",
        card_expiry_month="12",
        card_expiry_year="2035",
        card_cvc="123",
        headed=False,
        slow_mo_ms=0,
    )
    base.update(overrides)
    return Settings.model_construct(**base)


# ── build_parser ──────────────────────────────────────────────────────────────


def test_build_parser_requires_subcommand() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_build_parser_accepts_browser_subcommand() -> None:
    args = build_parser().parse_args(["browser"])
    assert args.command == "browser"


def test_build_parser_accepts_api_subcommand() -> None:
    args = build_parser().parse_args(["api"])
    assert args.command == "api"


# ── _build_domain_objects ─────────────────────────────────────────────────────


def test_build_domain_objects_returns_correct_types() -> None:
    from account_details_update import BankingDetails, PaymentMethod

    banking, payment = _build_domain_objects(_test_settings())

    assert isinstance(banking, BankingDetails)
    assert banking.routing_number == "123456789"
    assert isinstance(payment, PaymentMethod)
    assert payment.cardholder_name == "Test User"


def test_build_domain_objects_raises_on_invalid_routing_number() -> None:
    with pytest.raises(ValueError, match="routing_number"):
        _build_domain_objects(_test_settings(bank_routing="BAD"))


def test_build_domain_objects_raises_on_invalid_card_number() -> None:
    with pytest.raises(ValueError, match="card_number"):
        _build_domain_objects(_test_settings(card_number="not-digits"))


# ── main — browser command ────────────────────────────────────────────────────


def test_main_browser_prints_summary_and_returns_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with (
        patch("account_details_update.bootstrap.cli.load_settings", return_value=_test_settings()),
        patch("account_details_update.bootstrap.cli.PlaywrightAccountUpdater") as MockUpdater,
        patch("account_details_update.bootstrap.cli.UpdateAccountDetails") as MockUseCase,
    ):
        MockUpdater.return_value.__enter__ = MagicMock(return_value=MockUpdater.return_value)
        MockUpdater.return_value.__exit__ = MagicMock(return_value=None)
        MockUseCase.return_value.execute.return_value = _MOCK_RESULT

        code = main(["browser"])

    assert code == 0
    out = capsys.readouterr().out
    assert "Routing" in out
    assert "Visa" in out


def test_main_browser_returns_one_on_configuration_error(capsys: pytest.CaptureFixture[str]) -> None:
    with patch(
        "account_details_update.bootstrap.cli.load_settings",
        return_value=_test_settings(bank_routing="BAD"),
    ):
        code = main(["browser"])

    assert code == 1
    assert "Configuration error" in capsys.readouterr().err


def test_main_browser_returns_one_on_browser_page_error(capsys: pytest.CaptureFixture[str]) -> None:
    from account_details_update.browser import BrowserPageError

    with (
        patch("account_details_update.bootstrap.cli.load_settings", return_value=_test_settings()),
        patch("account_details_update.bootstrap.cli.PlaywrightAccountUpdater") as MockUpdater,
        patch("account_details_update.bootstrap.cli.UpdateAccountDetails") as MockUseCase,
    ):
        MockUpdater.return_value.__enter__ = MagicMock(return_value=MockUpdater.return_value)
        MockUpdater.return_value.__exit__ = MagicMock(return_value=None)
        MockUseCase.return_value.execute.side_effect = BrowserPageError("element not found")

        code = main(["browser"])

    assert code == 1
    assert "Browser error" in capsys.readouterr().err


# ── main — api command ────────────────────────────────────────────────────────


def test_main_api_prints_summary_and_returns_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with (
        patch("account_details_update.bootstrap.cli.load_settings", return_value=_test_settings()),
        patch("account_details_update.bootstrap.cli.RaziApiClient") as MockClient,
        patch("account_details_update.bootstrap.cli.UpdateAccountDetails") as MockUseCase,
    ):
        MockClient.return_value.__enter__ = MagicMock(return_value=MockClient.return_value)
        MockClient.return_value.__exit__ = MagicMock(return_value=None)
        MockUseCase.return_value.execute.return_value = _MOCK_RESULT

        code = main(["api"])

    assert code == 0
    out = capsys.readouterr().out
    assert "Routing" in out
    assert "Visa" in out


def test_main_api_returns_one_on_configuration_error(capsys: pytest.CaptureFixture[str]) -> None:
    with patch(
        "account_details_update.bootstrap.cli.load_settings",
        return_value=_test_settings(bank_routing="BAD"),
    ):
        code = main(["api"])

    assert code == 1
    assert "Configuration error" in capsys.readouterr().err


def test_main_api_returns_one_on_api_error(capsys: pytest.CaptureFixture[str]) -> None:
    with (
        patch("account_details_update.bootstrap.cli.load_settings", return_value=_test_settings()),
        patch("account_details_update.bootstrap.cli.RaziApiClient") as MockClient,
        patch("account_details_update.bootstrap.cli.UpdateAccountDetails") as MockUseCase,
    ):
        MockClient.return_value.__enter__ = MagicMock(return_value=MockClient.return_value)
        MockClient.return_value.__exit__ = MagicMock(return_value=None)
        MockUseCase.return_value.execute.side_effect = RaziApiError("connection refused")

        code = main(["api"])

    assert code == 1
    assert "API error" in capsys.readouterr().err
