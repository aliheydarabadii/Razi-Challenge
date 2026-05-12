"""Command-line entrypoint for future account detail update flows."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="account-details-update",
        description="Scaffold CLI for account details update workflows.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "browser",
        help="Future Playwright account details update flow.",
    )
    subparsers.add_parser(
        "api",
        help="Future REST API account details update flow.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "browser":
        print(
            "Browser flow is scaffold-only. Real Playwright execution is not "
            "implemented yet."
        )
        return 0

    if args.command == "api":
        print(
            "API flow is scaffold-only. Real HTTP execution is not implemented yet."
        )
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
