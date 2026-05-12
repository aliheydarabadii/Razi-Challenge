"""Command-line entrypoint for account detail update flows."""

from __future__ import annotations

import argparse
import sys

from ..application.update_account_details import UpdateAccountDetails
from ..banking_details import BankingDetails
from ..browser.errors import BrowserPageError
from ..browser.playwright_account_updater import PlaywrightAccountUpdater
from ..http_api import RaziApiError
from ..http_api.api_account_updater import ApiAccountUpdater
from ..http_api.razi_api_client import RaziApiClient
from ..payment_method import PaymentMethod
from ..ports import AccountUpdateResult
from .logging import configure_logging
from .settings import Settings, load_settings


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)
    settings = load_settings()

    try:
        result = _execute(args.command, settings)
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    except BrowserPageError as exc:
        print(f"Browser error: {exc}", file=sys.stderr)
        return 1
    except RaziApiError as exc:
        print(f"API error: {exc}", file=sys.stderr)
        return 1

    print(result.banking_summary)
    print(result.payment_summary)
    return 0


def _execute(command: str, settings: Settings) -> AccountUpdateResult:
    """Build the adapter for *command*, run the use case, return the result."""
    banking_details, payment_method = _build_domain_objects(settings)

    if command == "browser":
        with PlaywrightAccountUpdater(
            base_url=settings.challenge_base_url,
            username=settings.username,
            password=settings.password.get_secret_value(),
            mfa_code=settings.mfa_code.get_secret_value(),
            headed=settings.headed,
            slow_mo_ms=settings.slow_mo_ms,
        ) as updater:
            return UpdateAccountDetails(account_update_port=updater).execute(
                banking_details=banking_details,
                payment_method=payment_method,
            )

    with RaziApiClient(
        base_url=settings.api_base_url,
        username=settings.username,
        password=settings.password.get_secret_value(),
        mfa_code=settings.mfa_code.get_secret_value(),
        anon_key=settings.supabase_anon_key.get_secret_value(),
        supabase_url=settings.supabase_url,
    ) as client:
        return UpdateAccountDetails(
            account_update_port=ApiAccountUpdater(client=client)
        ).execute(
            banking_details=banking_details,
            payment_method=payment_method,
        )


def _build_domain_objects(settings: Settings) -> tuple[BankingDetails, PaymentMethod]:
    return (
        BankingDetails(
            routing_number=settings.bank_routing,
            account_number=settings.bank_account,
        ),
        PaymentMethod(
            cardholder_name=settings.cardholder_name,
            card_number=settings.card_number,
            expiry_month=settings.card_expiry_month,
            expiry_year=settings.card_expiry_year,
            cvc=settings.card_cvc,
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="account-details-update",
        description="Update account banking and payment details via browser or API.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "browser",
        help="Update account details using Playwright browser automation.",
    )
    subparsers.add_parser(
        "api",
        help="Update account details using the REST API.",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
