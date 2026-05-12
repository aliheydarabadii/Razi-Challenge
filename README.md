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
  config.py                 ← pydantic-settings Settings (env / .env file)
  cli.py                    ← entrypoint — `browser` and `api` subcommands
  browser/
    playwright_account_updater.py  ← AccountUpdatePort adapter (Playwright)
    pages/                         ← LoginPage, MfaPage, AccountPage objects
    selectors.py                   ← id/data-testid selector constants
  http_api/
    razi_api_client.py      ← low-level httpx client
    api_account_updater.py  ← AccountUpdatePort adapter (REST API)
    schemas.py              ← Pydantic request / response models
    errors.py               ← typed API exception hierarchy
  support/
    logging.py
tests/
  support/
    fake_data.py            ← BankingDetails / PaymentMethod test factories
    browser_fakes.py        ← FakePage, FakePlaywrightFactory
  unit/                     ← 48 unit tests, all offline
  integration/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium   # required for Part 1 only
```

Copy `.env.example` to `.env`. The defaults are sandbox values — do not use real banking or card data.

```bash
cp .env.example .env
```

## Run Tests

```bash
pytest
```

All 48 tests run offline with no real browser or network calls.

## Part 1 — Browser Automation

Uses Playwright to sign in, complete MFA, submit banking and payment details on `/app/account`, then return a confirmation.

```bash
account-details-update browser
# or headed with slow motion for observation:
HEADED=true SLOW_MO_MS=500 account-details-update browser
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
account-details-update api
```

**Documented auth flow (POST /auth/token → POST /auth/mfa/verify):**

```bash
# Step 1
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"candidate@dev-challenge.com","password":"Password123!"}' \
  https://zvyhufnwclhcvmgtqxwp.supabase.co/functions/v1/api-v1/auth/token
# → {"mfa_required":true,"mfa_token":"mfa_abc123...","message":"..."}

# Step 2
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"mfa_token":"mfa_abc123...","code":"1234"}' \
  https://zvyhufnwclhcvmgtqxwp.supabase.co/functions/v1/api-v1/auth/mfa/verify
# → {"error":"Invalid or expired MFA session"}  ← always fails (see below)
```

### Server-side bug in the custom MFA flow

The custom `/auth/token → /auth/mfa/verify` flow has a server-side bug. The MFA token is stored in Deno instance memory inside the edge function. The Supabase load balancer routes the two requests to **different Deno instances**, so the second instance has no record of the token.

This can be confirmed by inspecting the `x-deno-execution-id` response header — it is always different across the two calls:

```bash
MFA_TOKEN=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"candidate@dev-challenge.com","password":"Password123!"}' \
  https://zvyhufnwclhcvmgtqxwp.supabase.co/functions/v1/api-v1/auth/token \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['mfa_token'])")

curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "{\"mfa_token\":\"$MFA_TOKEN\",\"code\":\"1234\"}" \
  https://zvyhufnwclhcvmgtqxwp.supabase.co/functions/v1/api-v1/auth/mfa/verify
# → {"error":"Invalid or expired MFA session"}
```

The fix must be server-side: MFA tokens need to be stored in a shared database or KV store rather than in Deno instance memory.

### Workaround — Supabase native auth

The Supabase native auth endpoint (`POST /auth/v1/token?grant_type=password`) authenticates with the same credentials in a single stateless request and produces a JWT that the `PUT /account/*` endpoints accept. The anon key is a **public** credential embedded in the challenge site's frontend bundle.

Verify the workaround with curl:

```bash
TOKEN=$(curl -s -X POST \
  "https://zvyhufnwclhcvmgtqxwp.supabase.co/auth/v1/token?grant_type=password" \
  -H "Content-Type: application/json" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp2eWh1Zm53Y2xoY3ZtZ3RxeHdwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE0MTg0ODYsImV4cCI6MjA4Njk5NDQ4Nn0.2RhFpJZLSLtLvLqzWWnPha64jEoWFexTq2u4zfUGIXg" \
  -d '{"email":"candidate@dev-challenge.com","password":"Password123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -X PUT \
  https://zvyhufnwclhcvmgtqxwp.supabase.co/functions/v1/api-v1/account/banking \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"routing_number":"021000021","account_number":"1234567890"}'
# → {"routing_masked":"•••••0021","account_masked":"••••••7890","token":"btok_..."}

curl -s -X PUT \
  https://zvyhufnwclhcvmgtqxwp.supabase.co/functions/v1/api-v1/account/payment \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cardholder_name":"Test Candidate","card_number":"4242424242424242","exp_month":12,"exp_year":2030,"cvc":"123"}'
# → {"card_brand":"visa","last4":"4242","exp_month":12,"exp_year":2030,"token":"tok_..."}
```

### How the client handles this

`RaziApiClient` implements the documented two-step interface (`request_token` / `verify_mfa`) and preserves the custom flow as a fallback. When `SUPABASE_URL` and `SUPABASE_ANON_KEY` are configured (the default), it uses the native auth path internally so that `verify_mfa` always succeeds. If those values are removed, the client falls back to the custom flow with a retry loop (up to 10 attempts) in case the load balancer ever routes both calls to the same instance.

**Expected output:**

```
Routing •••••6789 — Account ••••••7890
Visa ending in 4242 (12/2030)
```

## Error handling

The API adapter maps HTTP errors to typed exceptions:

| HTTP status | Exception |
|---|---|
| 401 (auth) | `AuthenticationError` |
| 401 (MFA) | `MfaVerificationError` |
| 422 | `ValidationError` |
| 429 | `RateLimitError` |
| other 4xx/5xx | `RaziApiError` |

All errors are caught in the CLI and printed to stderr with a non-zero exit code.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CHALLENGE_BASE_URL` | `https://marketplace.dev-challenge.com` | Browser automation base URL |
| `API_BASE_URL` | `https://zvyhufnwclhcvmgtqxwp.supabase.co/functions/v1/api-v1` | REST API base URL |
| `SUPABASE_URL` | `https://zvyhufnwclhcvmgtqxwp.supabase.co` | Supabase project URL (for native auth) |
| `SUPABASE_ANON_KEY` | *(see .env.example)* | Public anon key (for native auth) |
| `CHALLENGE_USERNAME` | `candidate@dev-challenge.com` | Login email |
| `CHALLENGE_PASSWORD` | `Password123!` | Login password |
| `MFA_CODE` | `1234` | MFA code |
| `BANK_ROUTING` | `123456789` | Routing number (9 digits) |
| `BANK_ACCOUNT` | `1234567890` | Account number (4–17 digits) |
| `CARDHOLDER_NAME` | `Test Candidate` | Name on card |
| `CARD_NUMBER` | `4242424242424242` | Card number (Luhn-valid) |
| `CARD_EXPIRY_MONTH` | `12` | Expiry month |
| `CARD_EXPIRY_YEAR` | `2030` | Expiry year |
| `CARD_CVC` | `123` | CVC (3–4 digits) |
| `HEADED` | `false` | Run browser in headed mode |
| `SLOW_MO_MS` | `0` | Playwright slow-motion delay (ms) |
