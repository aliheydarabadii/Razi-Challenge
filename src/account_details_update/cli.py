"""Command-line entrypoint for account detail update flows."""

from __future__ import annotations

import argparse
import sys

from .account_details import BankingDetails, PaymentMethod
from .browser.playwright_account_updater import PlaywrightAccountUpdater
from .config import load_settings
from .http_api.api_account_updater import ApiAccountUpdater
from .http_api.errors import RaziApiError
from .http_api.razi_api_client import RaziApiClient
from .support.logging import configure_logging
from .update_account_details import UpdateAccountDetails


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


def _build_domain_objects(
    settings: object,
) -> tuple[BankingDetails, PaymentMethod]:
    from .config import Settings

    s = settings
    assert isinstance(s, Settings)
    return (
        BankingDetails(
            routing_number=s.bank_routing,
            account_number=s.bank_account,
        ),
        PaymentMethod(
            cardholder_name=s.cardholder_name,
            card_number=s.card_number,
            expiry_month=s.card_expiry_month,
            expiry_year=s.card_expiry_year,
            cvc=s.card_cvc,
        ),
    )


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = load_settings()

    if args.command == "browser":
        banking_details, payment_method = _build_domain_objects(settings)
        with PlaywrightAccountUpdater(
            base_url=settings.challenge_base_url,
            username=settings.username,
            password=settings.password,
            mfa_code=settings.mfa_code,
            headed=settings.headed,
            slow_mo_ms=settings.slow_mo_ms,
        ) as updater:
            use_case = UpdateAccountDetails(account_update_port=updater)
            result = use_case.execute(
                banking_details=banking_details,
                payment_method=payment_method,
            )
        print(result.banking_summary)
        print(result.payment_summary)
        return 0

    if args.command == "api":
        banking_details, payment_method = _build_domain_objects(settings)
        client = RaziApiClient(
            base_url=settings.api_base_url,
            username=settings.username,
            password=settings.password,
            mfa_code=settings.mfa_code,
            anon_key=settings.supabase_anon_key,
            supabase_url=settings.supabase_url,
        )
        try:
            adapter = ApiAccountUpdater(client=client)
            use_case = UpdateAccountDetails(account_update_port=adapter)
            result = use_case.execute(
                banking_details=banking_details,
                payment_method=payment_method,
            )
        except RaziApiError as exc:
            print(f"API error: {exc}", file=sys.stderr)
            return 1
        print(result.banking_summary)
        print(result.payment_summary)
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
