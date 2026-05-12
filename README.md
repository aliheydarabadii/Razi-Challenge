# Razi Engineering Challenge

Initial Python scaffold for updating account banking details and payment method details through two future adapters:

- Browser automation with Playwright
- REST API client

## Current Status

This repository is scaffold-only. It defines the package structure, data models, core use case, ports, configuration, placeholder adapters, and unit tests.

Real Playwright selectors, login flow, MFA flow, account update flow, HTTP requests, retries, and production error handling will be implemented in later phases.

There are no real browser automation calls and no real network calls in this scaffold.

## Architecture

`account_details_update` is the use-case package. It is intentionally named around the business capability: updating account details.

- `ports.py` defines the core interface, `AccountUpdatePort`.
- `update_account_details.py` contains the main use case orchestration.
- `account_details.py` contains validated immutable input models.
- `account_update_result.py` contains the immutable result model.
- `browser/` is the future Playwright adapter.
- `http_api/` is the future REST API adapter.

The core files do not import Playwright or `httpx`. Browser automation remains inside `browser/`, and HTTP/API implementation details remain inside `http_api/`.

## Folder Structure

```text
razi-engineering-challenge/
  README.md
  pyproject.toml
  .env.example
  .gitignore
  src/
    account_details_update/
      cli.py
      config.py
      account_details.py
      account_update_result.py
      ports.py
      update_account_details.py
      browser/
      http_api/
      support/
  tests/
    unit/
    integration/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Playwright browser binaries are not needed for the current scaffold tests. They will be needed once browser automation is implemented.

## Environment Variables

Copy `.env.example` to `.env` when local configuration is needed.

```bash
cp .env.example .env
```

The defaults are sandbox challenge values only. Do not use real banking or card data.

## Run Tests

```bash
pytest
```

## Future Commands

The CLI is scaffolded with future subcommands:

```bash
python -m account_details_update.cli browser
python -m account_details_update.cli api
```

For now, these commands only print scaffold status messages and do not run real automation or API calls.

## Notes

- Use fake test data only.
- Do not use real banking details.
- Do not use real card details.
- No real network calls are made in this scaffold phase.
- No real browser automation is executed in this scaffold phase.
