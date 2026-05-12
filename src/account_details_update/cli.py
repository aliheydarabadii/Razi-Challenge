"""Command-line entrypoint for account detail update flows."""

from __future__ import annotations

import argparse

from .account_details import BankingDetails, PaymentMethod
from .browser.playwright_account_updater import PlaywrightAccountUpdater
from .config import load_settings
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
        help="Update account details using the REST API (not yet implemented).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "browser":
        settings = load_settings()

        banking_details = BankingDetails(
            routing_number=settings.bank_routing,
            account_number=settings.bank_account,
        )
        payment_method = PaymentMethod(
            cardholder_name=settings.cardholder_name,
            card_number=settings.card_number,
            expiry_month=settings.card_expiry_month,
            expiry_year=settings.card_expiry_year,
            cvc=settings.card_cvc,
        )

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
        print("API flow is not yet implemented.")
        return 1

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
