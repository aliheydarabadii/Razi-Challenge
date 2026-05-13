# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (creates .venv)
uv sync --extra dev

# Install Playwright browsers (browser adapter only)
uv run playwright install chromium

# Run all unit tests (offline, no network)
uv run python -m pytest tests/

# Run a single test file
uv run python -m pytest tests/unit/test_razi_api_client.py -v

# Run integration tests against live sandbox (requires .env)
INTEGRATION_TESTS=1 uv run python -m pytest tests/integration/ -v

# Run browser integration test with visible browser
INTEGRATION_TESTS=1 HEADED=true SLOW_MO_MS=500 uv run python -m pytest tests/integration/test_browser_integration.py -v

# Lint + format
uv run ruff check --fix src tests
uv run ruff format src tests

# Type-check
uv run mypy src

# Run the CLI
uv run account-details-update browser
uv run account-details-update api
HEADED=true SLOW_MO_MS=500 uv run account-details-update browser
```

Pre-commit hooks run `ruff check --fix`, `ruff format`, and `mypy src` automatically on commit.

## Architecture

Hexagonal (ports & adapters) with CQRS. The domain knows nothing about Playwright or HTTP.

```
domain layer      ports.py, banking_details.py, payment_method.py
application layer application/commands.py, application/update_account_details.py
adapters          browser/playwright_account_updater.py
                  http_api/api_account_updater.py
bootstrap         bootstrap/cli.py  ← wires everything and runs
```

**Port:** `AccountUpdatePort` (protocol in `ports.py`) — one method: `execute(banking, payment) → AccountUpdateResult`. Both adapters implement this.

**Handler:** `UpdateAccountDetailsHandler` in `application/` — receives any `AccountUpdatePort` and delegates to it. The CLI injects either the Playwright or the API adapter.

**Browser adapter flow:** `BrowserSession` (Playwright lifecycle) → `PlaywrightAccountUpdater.execute()` → page objects in `browser/pages/` (login → MFA → account). CSS selectors live in `browser/selectors.py`.

**API adapter flow:** `RaziApiClient` (httpx, handles auth + retries) → `ApiAccountUpdater.execute()` → typed Pydantic schemas in `http_api/schemas/`. Errors map to a typed exception hierarchy rooted at `RaziApiError`.

**Settings:** Pydantic-settings `Settings` class reads from `.env`. Copy `.env.example` to `.env` before running. Secrets (`password`, `mfa_code`) are `SecretStr`.

**Tests:** Unit tests use `FakePage`/`FakePlaywrightFactory` from `tests/support/browser_fakes.py` to avoid real browser calls. Integration tests are gated by `INTEGRATION_TESTS=1` env var.
