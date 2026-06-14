"""
conftest.py
───────────
Root-level pytest configuration.

Fixtures defined here are available to every test module without imports.
This file is intentionally kept lean – only cross-cutting concerns live here.
Module-specific fixtures belong in a conftest.py inside the relevant package.

Fixtures
────────
  api_client      – Session-scoped APIClient instance (shared across all tests)
  test_data       – Session-scoped dict loaded from data/test_data.json
  base_url        – Session-scoped base URL string
  response_threshold_ms – Response time limit (ms) from test_data.json
"""

import json
import logging
from pathlib import Path

import pytest

from utils.api_client import APIClient
from utils.logger import configure_logging, get_logger

# ── Bootstrap logging before any test collection happens ─────
configure_logging()
logger = get_logger(__name__)

# ── Path constants ────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "data" / "test_data.json"
REPORTS_DIR = Path(__file__).parent / "reports"

# Ensure reports directory exists so pytest-html never errors out
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# Session-scoped fixtures  (created once per test run)
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_data() -> dict:
    """Load and return the entire test_data.json as a Python dict."""
    logger.debug("Loading test data from %s", DATA_FILE)
    with DATA_FILE.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    logger.info("Test data loaded successfully.")
    return data


@pytest.fixture(scope="session")
def base_url(test_data: dict) -> str:
    """Return the base URL for the API under test."""
    return test_data["base_url"]


@pytest.fixture(scope="session")
def response_threshold_ms(test_data: dict) -> int:
    """Maximum acceptable response time in milliseconds."""
    return test_data["response_time_threshold_ms"]


@pytest.fixture(scope="session")
def api_client(base_url: str) -> APIClient:
    """
    Provide a single, reusable APIClient for the whole test session.

    The client is automatically closed after all tests have run,
    releasing underlying TCP connections cleanly.
    """
    logger.info("Creating shared APIClient | base_url=%s", base_url)
    client = APIClient(base_url=base_url, timeout=15)
    yield client
    logger.info("Tearing down shared APIClient.")
    client.close()


# ─────────────────────────────────────────────────────────────
# Function-scoped convenience fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture()
def users_data(test_data: dict) -> dict:
    """Shortcut to the 'users' section of test_data.json."""
    return test_data["users"]


@pytest.fixture()
def posts_data(test_data: dict) -> dict:
    """Shortcut to the 'posts' section of test_data.json."""
    return test_data["posts"]


@pytest.fixture()
def negative_data(test_data: dict) -> dict:
    """Shortcut to the 'negative_tests' section of test_data.json."""
    return test_data["negative_tests"]


# ─────────────────────────────────────────────────────────────
# Hooks
# ─────────────────────────────────────────────────────────────

def pytest_configure(config):
    """Register custom markers so -W error::PytestUnknownMarkWarning stays clean."""
    config.addinivalue_line("markers", "smoke: Fast critical-path smoke tests")
    config.addinivalue_line("markers", "regression: Full regression suite")
    config.addinivalue_line("markers", "users: Tests for the /users endpoint")
    config.addinivalue_line("markers", "posts: Tests for the /posts endpoint")
    config.addinivalue_line("markers", "negative: Negative / edge-case tests")
    config.addinivalue_line("markers", "slow: Tests expected to take longer than average")


def pytest_runtest_logreport(report):
    """Emit a concise summary line after each test phase."""
    if report.when == "call":
        status = "PASSED" if report.passed else ("FAILED" if report.failed else "SKIPPED")
        logger.info("TEST %s – %s", status, report.nodeid)
