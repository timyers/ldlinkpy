# ldlinkpy/client.py

from __future__ import annotations

import os
import threading
from typing import Any

import requests

from . import DEFAULT_API_ROOT
from .exceptions import APIError


class LDlinkClient:
    """Thin, sequential-only HTTP client for the NIH LDlink REST API."""

    def __init__(
        self,
        token: str | None = None,
        api_root: str = DEFAULT_API_ROOT,
        genome_build: str = "grch37",
        timeout: float | int = 60,
    ) -> None:
        self.api_root = api_root
        self.genome_build = genome_build
        self.timeout = timeout

        self.token = token or os.getenv("LDLINK_TOKEN")
        self._lock = threading.Lock()

    def request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> str:
        if not self.token:
            raise ValueError(
                "LDlink API token is required. Pass token=... or set env var LDLINK_TOKEN."
            )

        url = self.api_root.rstrip("/") + "/" + endpoint.lstrip("/")

        req_params: dict[str, Any] = dict(params or {})
        req_params["token"] = self.token

        try:
            with self._lock:
                resp = requests.request(
                    method=method.upper(),
                    url=url,
                    params=req_params,
                    json=json_body,
                    timeout=self.timeout,
                )
        except requests.RequestException as e:
            raise APIError(f"Request failed for {method.upper()} {url}: {e}") from e

        if resp.status_code != 200:
            raise APIError(
                f"LDlink API error {resp.status_code} for {method.upper()} {url}: {resp.text}"
            )

        return resp.text

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> str:
        return self.request("GET", endpoint, params=params, json_body=None)

    def post(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> str:
        return self.request("POST", endpoint, params=params, json_body=json_body)
