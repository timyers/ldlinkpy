# tests/test_http.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

import pytest
import requests

import ldlinkpy.http as http


class DummyResp:
    def __init__(self, status_code: int = 200, text: str = "ok", reason: str = "OK") -> None:
        self.status_code = status_code
        self.text = text
        self.reason = reason


def test_token_is_added_to_params(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: Dict[str, Any] = {}

    def fake_request(
        *,
        method: str,
        url: str,
        params: Dict[str, Any],
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float,
    ) -> DummyResp:
        calls["method"] = method
        calls["url"] = url
        calls["params"] = dict(params)
        calls["json"] = json
        calls["headers"] = headers
        calls["timeout"] = timeout
        return DummyResp(200, "ok")

    monkeypatch.setattr(http.requests, "request", fake_request)

    out = http.request(
        "LDproxy",
        api_root="https://ldlink.nih.gov/LDlinkRest",
        token="abc123",
        params={"snp": "rs429358"},
    )
    assert out == "ok"
    assert calls["params"]["token"] == "abc123"
    assert calls["params"]["snp"] == "rs429358"


def test_headers_are_forwarded(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: Dict[str, Any] = {}

    def fake_request(
        *,
        method: str,
        url: str,
        params: Dict[str, Any],
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float,
    ) -> DummyResp:
        calls["headers"] = headers
        return DummyResp(200, "ok")

    monkeypatch.setattr(http.requests, "request", fake_request)

    out = http.request(
        "LDmatrix",
        api_root="https://ldlink.nih.gov/LDlinkRest",
        token="t",
        params={"snps": "rs1", "pop": "CEU"},
        headers={"Accept": "application/json"},
    )
    assert out == "ok"
    assert calls["headers"] == {"Accept": "application/json"}


def test_lock_wrapper_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
    acquired = {"value": False}

    @contextmanager
    def fake_lock() -> Iterator[None]:
        acquired["value"] = True
        yield

    def fake_request(
        *,
        method: str,
        url: str,
        params: Dict[str, Any],
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float,
    ) -> DummyResp:
        return DummyResp(200, "ok")

    monkeypatch.setattr(http, "_request_lock", fake_lock)
    monkeypatch.setattr(http.requests, "request", fake_request)

    _ = http.request(
        "LDpair",
        api_root="https://ldlink.nih.gov/LDlinkRest",
        token="t",
        params={"var1": "rs1", "var2": "rs2"},
    )
    assert acquired["value"] is True


def test_ipv4_retry_triggers_only_on_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = {"n": 0}
    ipv4_used = {"value": False}

    @contextmanager
    def fake_ipv4() -> Iterator[None]:
        ipv4_used["value"] = True
        yield

    def fake_request(
        *,
        method: str,
        url: str,
        params: Dict[str, Any],
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float,
    ) -> DummyResp:
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise requests.exceptions.ConnectionError("boom")
        return DummyResp(200, "ok")

    monkeypatch.setattr(http, "_force_ipv4_only", fake_ipv4)
    monkeypatch.setattr(http.requests, "request", fake_request)

    out = http.request(
        "LDmatrix",
        api_root="https://ldlink.nih.gov/LDlinkRest",
        token="t",
        params={"snps": "rs1,rs2", "pop": "CEU"},
    )
    assert out == "ok"
    assert call_count["n"] == 2
    assert ipv4_used["value"] is True


def test_ipv4_retry_only_once_then_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = {"n": 0}
    ipv4_used = {"value": False}

    @contextmanager
    def fake_ipv4() -> Iterator[None]:
        ipv4_used["value"] = True
        yield

    def fake_request(
        *,
        method: str,
        url: str,
        params: Dict[str, Any],
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float,
    ) -> DummyResp:
        call_count["n"] += 1
        raise requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(http, "_force_ipv4_only", fake_ipv4)
    monkeypatch.setattr(http.requests, "request", fake_request)

    with pytest.raises(RuntimeError) as e:
        _ = http.request(
            "LDproxy",
            api_root="https://ldlink.nih.gov/LDlinkRest",
            token="t",
            params={"snp": "rs1"},
        )

    msg = str(e.value)
    assert "after IPv4 retry" in msg
    assert call_count["n"] == 2
    assert ipv4_used["value"] is True


def test_http_status_400_raises_runtimeerror(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(
        *,
        method: str,
        url: str,
        params: Dict[str, Any],
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float,
    ) -> DummyResp:
        return DummyResp(400, "Bad Request", "Bad Request")

    monkeypatch.setattr(http.requests, "request", fake_request)

    with pytest.raises(RuntimeError) as e:
        _ = http.request(
            "LDproxy",
            api_root="https://ldlink.nih.gov/LDlinkRest",
            token="t",
            params={"snp": "rs1"},
        )

    assert "HTTP 400" in str(e.value)