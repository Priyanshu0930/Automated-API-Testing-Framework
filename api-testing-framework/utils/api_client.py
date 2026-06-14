"""
utils/api_client.py
───────────────────
Reusable HTTP client that wraps the `requests` library.

Every public method:
  • Accepts an optional `**kwargs` forwarded straight to requests.
  • Returns a `requests.Response` object so tests can assert freely.
  • Logs request / response metadata at DEBUG level.
  • Raises a descriptive RuntimeError when a network-level failure occurs
    (connection refused, timeout, etc.).
"""

import logging
import time
from typing import Any, Dict, Optional

import requests
from requests import Response, Session

logger = logging.getLogger(__name__)


class APIClient:
    """
    Thin, stateful HTTP client built on top of `requests.Session`.

    Parameters
    ----------
    base_url : str
        Root URL of the API under test, e.g. "https://jsonplaceholder.typicode.com".
    default_headers : dict, optional
        Headers merged into every request (e.g. {"Content-Type": "application/json"}).
    timeout : int
        Default request timeout in seconds (can be overridden per call).
    """

    def __init__(
        self,
        base_url: str,
        default_headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Persistent session – reuses TCP connections, shares cookies/headers
        self.session: Session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        if default_headers:
            self.session.headers.update(default_headers)

        logger.debug("APIClient initialised | base_url=%s | timeout=%ss", self.base_url, self.timeout)

    # ──────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────

    def _build_url(self, endpoint: str) -> str:
        """Concatenate base URL with the given endpoint path."""
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _send(self, method: str, endpoint: str, **kwargs) -> Response:
        """
        Core dispatch method.

        Measures wall-clock request time, logs at DEBUG/INFO level, and
        surfaces network exceptions as a RuntimeError with a helpful message.
        """
        url = self._build_url(endpoint)
        kwargs.setdefault("timeout", self.timeout)

        logger.debug("→ %s %s | kwargs=%s", method.upper(), url, {k: v for k, v in kwargs.items() if k != "json"})

        try:
            start = time.perf_counter()
            response: Response = self.session.request(method, url, **kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1_000

        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(f"Connection failed for {url}: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            raise RuntimeError(f"Request timed out for {url} (>{self.timeout}s): {exc}") from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"Request error for {url}: {exc}") from exc

        # Attach elapsed time as a custom attribute so tests can inspect it
        response.elapsed_ms = elapsed_ms  # type: ignore[attr-defined]

        logger.info(
            "← %s %s | status=%d | time=%.1fms",
            method.upper(),
            url,
            response.status_code,
            elapsed_ms,
        )
        logger.debug("   Response body: %s", response.text[:500])

        return response

    # ──────────────────────────────────────────────────────────
    # Public HTTP verb methods
    # ──────────────────────────────────────────────────────────

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Response:
        """HTTP GET – retrieve a resource."""
        return self._send("GET", endpoint, params=params, **kwargs)

    def post(self, endpoint: str, payload: Optional[Dict[str, Any]] = None, **kwargs) -> Response:
        """HTTP POST – create a resource."""
        return self._send("POST", endpoint, json=payload, **kwargs)

    def put(self, endpoint: str, payload: Optional[Dict[str, Any]] = None, **kwargs) -> Response:
        """HTTP PUT – replace a resource."""
        return self._send("PUT", endpoint, json=payload, **kwargs)

    def patch(self, endpoint: str, payload: Optional[Dict[str, Any]] = None, **kwargs) -> Response:
        """HTTP PATCH – partially update a resource."""
        return self._send("PATCH", endpoint, json=payload, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Response:
        """HTTP DELETE – remove a resource."""
        return self._send("DELETE", endpoint, **kwargs)

    # ──────────────────────────────────────────────────────────
    # Session management
    # ──────────────────────────────────────────────────────────

    def close(self) -> None:
        """Release underlying TCP connections."""
        self.session.close()
        logger.debug("APIClient session closed.")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
