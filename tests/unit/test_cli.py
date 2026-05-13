from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from account_details_update.bootstrap.cli import (
    build_parser,
    main,
)
from account_details_update.bootstrap.settings import Settings
from account_details_update.browser.errors import BrowserPageError
from account_details_update.http_api.errors import RaziApiError
from account_details_update.ports import AccountUpdateResult

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


# ── main — browser command ────────────────────────────────────────────────────


def test_main_browser_prints_summary_and_returns_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with (
        patch(f"{_CLI}.load_settings", return_value=_test_settings()),
        patch(f"{_CLI}.PlaywrightAccountUpdater") as MockUpdater,
        patch(f"{_CLI}.UpdateAccountDetailsHandler") as MockUseCase,
    ):
        _mock_updater_cm(MockUpdater)
        MockUseCase.return_value.handle.return_value = _MOCK_RESULT
        code = main(["browser"])

    assert code == 0
    out = capsys.readouterr().out
    assert "Routing" in out
    assert "Visa" in out


def test_main_browser_returns_one_on_configuration_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with patch(
        f"{_CLI}.load_settings",
        return_value=_test_settings(bank_routing="BAD"),
    ):
        code = main(["browser"])

    assert code == 1
    assert "Configuration error" in capsys.readouterr().err


def test_main_browser_returns_one_on_browser_page_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with (
        patch(f"{_CLI}.load_settings", return_value=_test_settings()),
        patch(f"{_CLI}.PlaywrightAccountUpdater") as MockUpdater,
        patch(f"{_CLI}.UpdateAccountDetailsHandler") as MockUseCase,
    ):
        _mock_updater_cm(MockUpdater)
        MockUseCase.return_value.handle.side_effect = BrowserPageError("not found")
        code = main(["browser"])

    assert code == 1
    assert "Browser error" in capsys.readouterr().err


# ── main — api command ────────────────────────────────────────────────────────


def test_main_api_prints_summary_and_returns_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with (
        patch(f"{_CLI}.load_settings", return_value=_test_settings()),
        patch(f"{_CLI}.RaziApiClient") as MockClient,
        patch(f"{_CLI}.UpdateAccountDetailsHandler") as MockUseCase,
    ):
        _mock_updater_cm(MockClient)
        MockUseCase.return_value.handle.return_value = _MOCK_RESULT
        code = main(["api"])

    assert code == 0
    out = capsys.readouterr().out
    assert "Routing" in out
    assert "Visa" in out


def test_main_api_returns_one_on_configuration_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with patch(
        f"{_CLI}.load_settings",
        return_value=_test_settings(bank_routing="BAD"),
    ):
        code = main(["api"])

    assert code == 1
    assert "Configuration error" in capsys.readouterr().err


def test_main_api_returns_one_on_api_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with (
        patch(f"{_CLI}.load_settings", return_value=_test_settings()),
        patch(f"{_CLI}.RaziApiClient") as MockClient,
        patch(f"{_CLI}.UpdateAccountDetailsHandler") as MockUseCase,
    ):
        _mock_updater_cm(MockClient)
        MockUseCase.return_value.handle.side_effect = RaziApiError("refused")
        code = main(["api"])

    assert code == 1
    assert "API error" in capsys.readouterr().err
