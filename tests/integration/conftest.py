"""Integration test configuration.

These tests make real network calls to the challenge sandbox. They are
skipped by default to keep `pytest tests/` fast and fully offline.

Run them explicitly:
    INTEGRATION_TESTS=1 pytest tests/integration/ -v
"""

from __future__ import annotations

import os

import pytest


def pytest_runtest_setup(item: pytest.Item) -> None:
    if os.getenv("INTEGRATION_TESTS") != "1":
        pytest.skip("set INTEGRATION_TESTS=1 to run integration tests")
