# ldlinkpy/http.py
#
# Shared HTTP request helper used by all ldlinkpy endpoint wrappers.
#
# What it does
# - Provides a single `request()` function that builds and sends LDlink REST requests via `requests`.
# - Serializes every network call behind one global `threading.Lock` so users cannot accidentally
#   run concurrent requests (LDlink can be sensitive to bursts, and this keeps behavior predictable).
# - Ensures the LDlink API token is always supplied as the required query parameter `token=...`,
#   coming from an explicit `token=` argument or the `LDLINK_TOKEN` environment variable.
# - Returns parsed JSON when the response looks like JSON; otherwise returns the raw text body.
# - Raises a clear RuntimeError on HTTP errors (status >= 400) including a short response snippet.
# - If the initial request fails with a connection/TLS style error (requests ConnectionError),
#   retries once with a temporary “force IPv4 only” DNS resolution patch, which can work around
#   occasional IPv6/network handshake issues seen in some environments.
#
# Why it exists
# - Keeps request logic consistent across endpoints (token handling, error messages, parsing).
# - Centralizes reliability workarounds (global serialization and IPv4 retry) in one place.
# - Makes endpoint functions smaller and easier to maintain and test.

# ldlinkpy/http.py
from __future__ import annotations

import json
import socket
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional, Union
from urllib.parse import urljoin

import requests
import urllib3.util.connection
from requests import Response

from .parsing import is_json_response
from .validators import ensure_token

_REQUEST_LOCK = threading.Lock()


@contextmanager
def _request_lock() -> Iterator[None]:
    """
    Global lock to serialize all HTTP requests.

    Kept as a wrapper so tests can monkeypatch it to verify it is used.
    """
    _REQUEST_LOCK.acquire()
    try:
        yield
    finally:
        _REQUEST_LOCK.release()


@contextmanager
def _force_ipv4_only() -> Iterator[None]:
    """
    Temporarily force urllib3 DNS resolution to return IPv4 only.

    Used as a single retry fallback for connection/TLS handshake style errors.
    """
    original = urllib3.util.connection.allowed_gai_family

    def allowed_gai_family_ipv4() -> int:
        return socket.AF_INET

    urllib3.util.connection.allowed_gai_family = allowed_gai_family_ipv4  # type: ignore[assignment]
    try:
        yield
    finally:
        urllib3.util.connection.allowed_gai_family = original  # type: ignore[assignment]


def _parse_body(resp: Response) -> Union[Dict[str, Any], list, str]:
    text = resp.text if resp.text is not None else ""
    if is_json_response(text):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return text


def _raise_for_status(resp: Response, url: str) -> None:
    if resp.status_code >= 400:
        snippet = (resp.text or "").strip().replace("\r", " ").replace("\n", " ")
        if len(snippet) > 500:
            snippet = snippet[:500] + "..."
        raise RuntimeError(
            f"LDlink request failed: HTTP {resp.status_code} {resp.reason} for {url}. "
            f"Response: {snippet}"
        )


def request(
    endpoint: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    token: Optional[str] = None,
    api_root: str,
    method: str = "GET",
    timeout: float = 180.0,
) -> Union[Dict[str, Any], list, str]:
    """
    Shared HTTP helper for LDlink REST endpoints.

    - Serializes all requests via a single global lock.
    - Adds token as query param token=...
    - For GET: sends params as query string.
    - For non-GET: sends payload in request body (JSON by default; form for ldtrait).
    - Parses JSON if possible; otherwise returns raw text.
    - Retries once forcing IPv4 if the first attempt raises requests.ConnectionError.
    - Supports JSON request bodies and custom headers.

    Raises RuntimeError on HTTP status >= 400 or repeated connection failure.
    """
    tok = ensure_token(token)

    method_u = method.upper()
    endpoint_l = endpoint.lower().lstrip("/")

    # Build URL
    base = api_root.rstrip("/") + "/"
    url = urljoin(base, endpoint.lstrip("/"))

    # Build query params and body depending on method
    if method_u == "GET":
        qparams: Dict[str, Any] = dict(params or {})
        qparams["token"] = tok
        body: Optional[Dict[str, Any]] = json_body
    else:
        # LDlink commonly expects token in the query string even for POST endpoints.
        qparams = {"token": tok}
        body = json_body if json_body is not None else dict(params or {})
        # Ensure token isn't duplicated into body accidentally
        if isinstance(body, dict):
            body.pop("token", None)

    def _do_request() -> Response:
        kwargs: Dict[str, Any] = dict(
            method=method,
            url=url,
            params=qparams,   # query string (includes token)
            headers=headers,
            timeout=timeout,
        )

        if method_u != "GET":
            kwargs["json"] = body   # JSON POST, as in API docs
        # For GET: no request body

        return requests.request(**kwargs)

    with _request_lock():
        try:
            resp = _do_request()
        except requests.exceptions.ConnectionError as e:
            with _force_ipv4_only():
                try:
                    resp = _do_request()
                except requests.exceptions.ConnectionError as e2:
                    raise RuntimeError(
                        f"LDlink request failed due to connection error after IPv4 retry for {url}. "
                        f"Original error: {e!r}; Retry error: {e2!r}"
                    ) from e2

    _raise_for_status(resp, url)
    return _parse_body(resp)