# Razi Engineering Challenge

A Python client that updates a user's banking details and payment method through two independent adapters: a Playwright browser adapter (Part 1) and a REST API adapter (Part 2).

Both adapters share the same domain core and implement the same `AccountUpdatePort` protocol, so the use case (`UpdateAccountDetails`) works identically regardless of which adapter is injected.

## Architecture

The project follows hexagonal / clean architecture. The domain has no knowledge of Playwright or HTTP.

```
account_details_update/
  ports.py                  ← AccountUpdatePort protocol (runtime_checkable)
  update_account_details.py ← use case — orchestrates login, MFA, updates, verify
  account_details.py        ← BankingDetails, PaymentMethod value objects (validated)
  account_update_result.py  ← AccountUpdateResult value object
  browser/
    playwright_account_updater.py  ← AccountUpdatePort adapter (Playwright)
    pages/                         ← LoginPage, MfaPage, AccountPage objects
    selectors.py                   ← id/data-testid selector constants
  http_api/
    razi_api_client.py      ← low-level httpx client
    api_account_updater.py  ← AccountUpdatePort adapter (REST API)
    schemas.py              ← Pydantic request / response models
    errors.py               ← typed API exception hierarchy
  bootstrap/
    cli.py                  ← entrypoint — `browser` and `api` subcommands
    settings.py             ← pydantic-settings Settings (env / .env file)
    logging.py              ← logging setup
tests/
  support/
    fake_data.py            ← BankingDetails / PaymentMethod test factories
    browser_fakes.py        ← FakePage, FakePlaywrightFactory
  unit/                     ← 48 unit tests, all offline
  integration/
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
Banking details updated successfully.
Payment method updated successfully.
```

## Part 2 — REST API Client

Uses `httpx` to authenticate and update account details via the REST API.

```bash
uv run account-details-update api
```

**Full flow (copy-paste ready):**

```bash
BASE=https://zvyhufnwclhcvmgtqxwp.supabase.co/functions/v1/api-v1

# Step 1 — authenticate and capture the MFA token
MFA_TOKEN=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"candidate@dev-challenge.com","password":"Password123!"}' \
  $BASE/auth/token \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['mfa_token'])")

# Step 2 — verify MFA and capture the bearer token
TOKEN=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "{\"mfa_token\":\"$MFA_TOKEN\",\"code\":\"1234\"}" \
  $BASE/auth/mfa/verify \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Step 3 — update banking details
curl -s -X PUT $BASE/account/banking \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"routing_number":"123456789","account_number":"1234567890"}'
# → {"routing_masked":"•••••6789","account_masked":"••••••7890","token":"btok_..."}

# Step 4 — update payment method
curl -s -X PUT $BASE/account/payment \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cardholder_name":"Test Candidate","card_number":"4242424242424242","exp_month":12,"exp_year":2035,"cvc":"123"}'
# → {"card_brand":"visa","last4":"4242","exp_month":12,"exp_year":2035,"token":"tok_..."}
```

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
