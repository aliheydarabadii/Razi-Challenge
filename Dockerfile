# ── api ───────────────────────────────────────────────────────────────────────
# Lightweight image for the REST API adapter — no browser required.
#
# Build:  docker build --target api -t account-updater:api .
# Run:    docker run --env-file .env account-updater:api
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.13-slim AS api

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml README.md uv.lock ./
COPY src/ src/
RUN uv sync --frozen --no-cache --no-dev --system

CMD ["account-details-update", "api"]


# ── browser ───────────────────────────────────────────────────────────────────
# Full image for the Playwright browser adapter — includes Chromium and all
# system dependencies required for headless browser automation.
#
# Build:  docker build --target browser -t account-updater:browser .
# Run:    docker run --env-file .env account-updater:browser
# ─────────────────────────────────────────────────────────────────────────────
FROM api AS browser

RUN playwright install --with-deps chromium

CMD ["account-details-update", "browser"]
