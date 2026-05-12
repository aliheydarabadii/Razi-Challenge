# ── api ───────────────────────────────────────────────────────────────────────
# Lightweight image for the REST API adapter — no browser required.
#
# Build:  docker build --target api -t account-updater:api .
# Run:    docker run --env-file .env account-updater:api
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.13-slim AS api

WORKDIR /app

# Copy packaging metadata and source before installing so setuptools can
# resolve the package. pyproject.toml + README.md are copied separately so
# this layer is cached as long as dependencies do not change.
COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir .

CMD ["account-details-update", "api"]


# ── browser ───────────────────────────────────────────────────────────────────
# Full image for the Playwright browser adapter — includes Chromium and all
# system dependencies required for headless browser automation.
#
# Build:  docker build --target browser -t account-updater:browser .
# Run:    docker run --env-file .env account-updater:browser
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.13-slim AS browser

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir .
RUN playwright install --with-deps chromium

CMD ["account-details-update", "browser"]
