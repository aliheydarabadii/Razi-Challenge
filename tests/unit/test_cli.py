from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from account_details_update.account_update_result import AccountUpdateResult
from account_details_update.bootstrap.cli import (
    _build_domain_objects,
    build_parser,
    main,
)
from account_details_update.bootstrap.settings import Settings
from account_details_update.http_api.errors import RaziApiError

_MOCK_RESULT = AccountUpdateResult(
    banking_summary="Routing •••••6789 — Account ••••••7890",
    payment_summary="Visa ending in 4242 (12/2035)",
)

_CLI = "account_details_update.bootstrap.cli"


def _test_settings(**overrides: object) -> Settings:
    base: dict[str, object] = dict(
        challenge_base_url="https://example.com",
        api_base_url="https://api.example.com",
        username="u@example.com",
        password=SecretStr("pass"),
        mfa_code=SecretStr("1234"),
        supabase_url="",
        supabase_anon_key=SecretStr(""),
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


def _mock_updater_cm(MockClass: MagicMock) -> MagicMock:
    """Wire __enter__/__exit__ so the mock works as a context manager."""
    instance = MockClass.return_value
    instance.__enter__ = MagicMock(return_value=instance)
    instance.__exit__ = MagicMock(return_value=None)
    return instance


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


def test_main_browser_prints_summary_and_returns_zero(capsys) -> None:  # type: ignore[no-untyped-def]
    with (
        patch(f"{_CLI}.load_settings", return_value=_test_settings()),
        patch(f"{_CLI}.PlaywrightAccountUpdater") as MockUpdater,
        patch(f"{_CLI}.UpdateAccountDetails") as MockUseCase,
    ):
        _mock_updater_cm(MockUpdater)
        MockUseCase.return_value.execute.return_value = _MOCK_RESULT
        code = main(["browser"])

    assert code == 0
    out = capsys.readouterr().out
    assert "Routing" in out
    assert "Visa" in out


def test_main_browser_returns_one_on_configuration_error(capsys) -> None:  # type: ignore[no-untyped-def]
    with patch(
        f"{_CLI}.load_settings",
        return_value=_test_settings(bank_routing="BAD"),
    ):
        code = main(["browser"])

    assert code == 1
    assert "Configuration error" in capsys.readouterr().err


def test_main_browser_returns_one_on_browser_page_error(capsys) -> None:  # type: ignore[no-untyped-def]
    from account_details_update.browser import BrowserPageError

    with (
        patch(f"{_CLI}.load_settings", return_value=_test_settings()),
        patch(f"{_CLI}.PlaywrightAccountUpdater") as MockUpdater,
        patch(f"{_CLI}.UpdateAccountDetails") as MockUseCase,
    ):
        _mock_updater_cm(MockUpdater)
        MockUseCase.return_value.execute.side_effect = BrowserPageError("not found")
        code = main(["browser"])

    assert code == 1
    assert "Browser error" in capsys.readouterr().err


# ── main — api command ────────────────────────────────────────────────────────


def test_main_api_prints_summary_and_returns_zero(capsys) -> None:  # type: ignore[no-untyped-def]
    with (
        patch(f"{_CLI}.load_settings", return_value=_test_settings()),
        patch(f"{_CLI}.RaziApiClient") as MockClient,
        patch(f"{_CLI}.UpdateAccountDetails") as MockUseCase,
    ):
        _mock_updater_cm(MockClient)
        MockUseCase.return_value.execute.return_value = _MOCK_RESULT
        code = main(["api"])

    assert code == 0
    out = capsys.readouterr().out
    assert "Routing" in out
    assert "Visa" in out


def test_main_api_returns_one_on_configuration_error(capsys) -> None:  # type: ignore[no-untyped-def]
    with patch(
        f"{_CLI}.load_settings",
        return_value=_test_settings(bank_routing="BAD"),
    ):
        code = main(["api"])

    assert code == 1
    assert "Configuration error" in capsys.readouterr().err


def test_main_api_returns_one_on_api_error(capsys) -> None:  # type: ignore[no-untyped-def]
    with (
        patch(f"{_CLI}.load_settings", return_value=_test_settings()),
        patch(f"{_CLI}.RaziApiClient") as MockClient,
        patch(f"{_CLI}.UpdateAccountDetails") as MockUseCase,
    ):
        _mock_updater_cm(MockClient)
        MockUseCase.return_value.execute.side_effect = RaziApiError("refused")
        code = main(["api"])

    assert code == 1
    assert "API error" in capsys.readouterr().err
