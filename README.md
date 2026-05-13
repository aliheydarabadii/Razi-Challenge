# Razi Engineering Challenge

A Python client that updates a user's banking details and payment method through two independent adapters: a Playwright browser adapter (Part 1) and a REST API adapter (Part 2).

Both adapters share the same domain core and implement the same `AccountUpdatePort` protocol, so the use case (`UpdateAccountDetails`) works identically regardless of which adapter is injected.

## Architecture

The project follows hexagonal / clean architecture. The domain has no knowledge of Playwright or HTTP.

```
account_details_update/
  ports.py                  ← AccountUpdatePort protocol + AccountUpdateResult
  banking_details.py        ← BankingDetails value object (validated)
  payment_method.py         ← PaymentMethod value object (Luhn check, expiry)
  application/
    commands.py             ← UpdateAccountDetailsCommand
    update_account_details.py ← UpdateAccountDetailsHandler (CQRS handler)
  browser/
    playwright_account_updater.py  ← AccountUpdatePort adapter (Playwright)
    session.py                     ← BrowserSession — browser lifecycle
    pages/
      login_page.py         ← LoginPage page object
      mfa_page.py           ← MfaPage page object
      account_page.py       ← AccountPage page object
      page_ready.py         ← wait_for_page_idle, require_page helpers
    selectors.py            ← CSS selector constants
    errors.py               ← BrowserPageError
  http_api/
    razi_api_client.py      ← low-level httpx client (auth + updates)
    api_account_updater.py  ← AccountUpdatePort adapter (REST API)
    schemas/
      _base.py              ← ApiRequest (extra=forbid), ApiResponse (extra=ignore)
      authentication.py     ← TokenRequest/Response, MfaVerifyRequest/Response
      banking.py            ← BankingUpdateRequest/Response
      payment.py            ← PaymentUpdateRequest/Response
    errors.py               ← typed API exception hierarchy
  bootstrap/
    cli.py                  ← entrypoint — `browser` and `api` subcommands
    settings.py             ← pydantic-settings Settings (env / .env file)
    logging.py              ← structured JSON logging setup
tests/
  support/
    fake_data.py            ← fake_banking_details(), fake_payment_method()
    browser_fakes.py        ← FakePage, FakePlaywrightFactory
  unit/                     ← 54 unit tests, all offline
  integration/              ← live sandbox tests (INTEGRATION_TESTS=1)
```

## Setup

The project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies (creates .venv automatically)
uv sync --extra dev

# Install Playwright browsers — required for Part 1 only
uv run playwright install chromium
```

Copy `.env.example` to `.env`. The defaults are sandbox values — do not use real banking or card data.

```bash
cp .env.example .env
```

## Run Tests

```bash
uv run python -m pytest tests/
```

All unit tests run offline with no real browser or network calls.

To run the integration tests against the live sandbox (requires a configured `.env`):

```bash
INTEGRATION_TESTS=1 uv run python -m pytest tests/integration/ -v
```

To also run the browser integration test with a visible browser:

```bash
INTEGRATION_TESTS=1 HEADED=true SLOW_MO_MS=500 uv run python -m pytest tests/integration/test_browser_integration.py -v
```

## Docker

The project ships with two build targets. Secrets are always passed at
runtime via `--env-file` — never baked into the image.

**API adapter — lightweight, no browser (~250 MB)**

```bash
docker build --target api -t account-updater:api .
docker run --env-file .env account-updater:api
```

**Browser adapter — includes Playwright + Chromium**

```bash
docker build --target browser -t account-updater:browser .
docker run --env-file .env account-updater:browser
```

## Part 1 — Browser Automation

Uses Playwright to sign in, complete MFA, submit banking and payment details on `/app/account`, then return a confirmation.

```bash
uv run account-details-update browser
# or headed with slow motion for observation:
HEADED=true SLOW_MO_MS=500 uv run account-details-update browser
```

**Flow:**

1. Navigate to `/login` → fill `#email`, `#password` → click `button[type='submit']`
2. Fill `[data-input-otp='true']` with the MFA code → click `button[type='submit']`
3. Navigate to `/app/account`
4. Fill `#bank-routing`, `#bank-account` → click `#bank-save`
5. Fill `#card-holder`, `#card-number`, `#card-exp-month`, `#card-exp-year`, `#card-cvc` → click `#card-save`

**Expected output:**

```
Banking details saved
Payment method saved
```

## Part 2 — REST API Client

Uses `httpx` to authenticate and update account details via the REST API.

```bash
uv run account-details-update api
```

**Auth flow:** `POST /auth/token` → receive `mfa_token` → `POST /auth/mfa/verify` → bearer token → `PUT /account/banking` → `PUT /account/payment`.

**Expected output:**

```
Routing •••••6789 — Account ••••••7890
Visa ending in 4242 (12/2035)
```

## Error handling

The API adapter maps HTTP errors to typed exceptions:

| HTTP status | Exception |
|---|---|
| 401 (auth) | `AuthenticationError` |
| 401 (MFA) | `MfaVerificationError` |
| 422 | `ApiValidationError` |
| 429 | `RateLimitError` |
| other 4xx/5xx | `RaziApiError` |

All errors are caught in the CLI and printed to stderr with a non-zero exit code.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CHALLENGE_BASE_URL` | `https://marketplace.dev-challenge.com` | Browser automation base URL |
| `API_BASE_URL` | `https://zvyhufnwclhcvmgtqxwp.supabase.co/functions/v1/api-v1` | REST API base URL |
| `CHALLENGE_USERNAME` | `candidate@dev-challenge.com` | Login email |
| `CHALLENGE_PASSWORD` | `Password123!` | Login password |
| `MFA_CODE` | `1234` | MFA code |
| `BANK_ROUTING` | `123456789` | Routing number (9 digits) |
| `BANK_ACCOUNT` | `1234567890` | Account number (4–17 digits) |
| `CARDHOLDER_NAME` | `Test Candidate` | Name on card |
| `CARD_NUMBER` | `4242424242424242` | Card number (Luhn-valid) |
| `CARD_EXPIRY_MONTH` | `12` | Expiry month |
| `CARD_EXPIRY_YEAR` | `2035` | Expiry year |
| `CARD_CVC` | `123` | CVC (3–4 digits) |
| `HEADED` | `false` | Run browser in headed mode |
| `SLOW_MO_MS` | `0` | Playwright slow-motion delay (ms) |
| `API_MAX_RETRIES` | `5` | Max retry attempts for 429/5xx/transport errors |
| `API_RETRY_MAX_WAIT` | `30` | Max seconds between retries (exponential backoff cap) |
