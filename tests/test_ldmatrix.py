# tests/test_ldmatrix.py
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import pytest


def _parse_matrix_tsv(text: str) -> pd.DataFrame:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    header = lines[0].split("\t")[1:]
    rows = []
    idx = []
    for ln in lines[1:]:
        parts = ln.split("\t")
        idx.append(parts[0])
        rows.append([float(x) for x in parts[1:]])
    return pd.DataFrame(rows, index=idx, columns=header)


def test_ldmatrix_auto_get_params(monkeypatch: pytest.MonkeyPatch) -> None:
    from ldlinkpy.endpoints import ldmatrix as ldmatrix_mod

    calls: Dict[str, Any] = {}

    def fake_http_request(
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        token: Optional[str] = None,
        api_root: str,
        method: str = "GET",
        timeout: float = 60.0,
    ) -> str:
        calls["endpoint"] = endpoint
        calls["api_root"] = api_root
        calls["token"] = token
        calls["method"] = method
        calls["params"] = params
        calls["json_body"] = json_body
        calls["headers"] = headers
        calls["timeout"] = timeout
        return "\trs1\trs2\nrs1\t1\t0.2\nrs2\t0.2\t1\n"

    monkeypatch.setattr(ldmatrix_mod, "parse_matrix", _parse_matrix_tsv)
    monkeypatch.setattr(ldmatrix_mod, "http_request", fake_http_request)

    df = ldmatrix_mod.ldmatrix(
        snps=["rs1", "rs2"],
        pop="CEU",
        r2d="r2",
        genome_build="grch37",
        token="tok",
        api_root="https://ldlink.nih.gov/LDlinkRest",
        return_type="dataframe",
        request_method="auto",
    )

    assert isinstance(df, pd.DataFrame)
    assert calls["method"] == "GET"
    assert calls["endpoint"] == "ldmatrix"
    assert calls["api_root"] == "https://ldlink.nih.gov/LDlinkRest"
    assert calls["token"] == "tok"
    assert calls["params"] is not None
    assert calls["params"]["pop"] == "CEU"
    assert calls["params"]["r2_d"] == "r2"
    assert calls["params"]["genome_build"] == "grch37"
    assert "rs1" in calls["params"]["snps"]
    assert "rs2" in calls["params"]["snps"]
    assert calls["json_body"] is None


def test_ldmatrix_auto_post_json_body(monkeypatch: pytest.MonkeyPatch) -> None:
    from ldlinkpy.endpoints import ldmatrix as ldmatrix_mod

    calls: Dict[str, Any] = {}

    def fake_http_request(
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        token: Optional[str] = None,
        api_root: str,
        method: str = "GET",
        timeout: float = 60.0,
    ) -> str:
        calls["endpoint"] = endpoint
        calls["api_root"] = api_root
        calls["token"] = token
        calls["method"] = method
        calls["params"] = params
        calls["json_body"] = json_body
        calls["headers"] = headers
        calls["timeout"] = timeout
        return "\trs1\trs2\nrs1\t1\t0.2\nrs2\t0.2\t1\n"

    monkeypatch.setattr(ldmatrix_mod, "parse_matrix", _parse_matrix_tsv)
    monkeypatch.setattr(ldmatrix_mod, "http_request", fake_http_request)

    df = ldmatrix_mod.ldmatrix(
        snps=[f"rs{i}" for i in range(1, 302)],  # 301 forces POST in auto mode
        pop="CEU",
        r2d="r2",
        genome_build="grch37",
        token="tok",
        api_root="https://ldlink.nih.gov/LDlinkRest",
        return_type="dataframe",
        request_method="auto",
    )

    assert isinstance(df, pd.DataFrame)
    assert calls["method"] == "POST"
    assert calls["endpoint"] == "ldmatrix"
    assert calls["api_root"] == "https://ldlink.nih.gov/LDlinkRest"
    assert calls["token"] == "tok"
    assert calls["params"] is None
    assert calls["json_body"] is not None
    assert calls["json_body"]["pop"] == "CEU"
    assert calls["json_body"]["r2_d"] == "r2"
    assert calls["json_body"]["genome_build"] == "grch37"
    assert isinstance(calls["json_body"]["snps"], list)
    assert len(calls["json_body"]["snps"]) == 301


def test_ldmatrix_parses_matrix_to_dataframe(monkeypatch: pytest.MonkeyPatch) -> None:
    from ldlinkpy.endpoints import ldmatrix as ldmatrix_mod

    def fake_http_request(
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        token: Optional[str] = None,
        api_root: str,
        method: str = "GET",
        timeout: float = 60.0,
    ) -> str:
        return "\trsA\trsB\nrsA\t1\t0.75\nrsB\t0.75\t1\n"

    monkeypatch.setattr(ldmatrix_mod, "parse_matrix", _parse_matrix_tsv)
    monkeypatch.setattr(ldmatrix_mod, "http_request", fake_http_request)

    df = ldmatrix_mod.ldmatrix(
        snps="rsA rsB",
        pop="CEU",
        r2d="r2",
        genome_build="grch37",
        token="tok",
        api_root="https://ldlink.nih.gov/LDlinkRest",
        return_type="dataframe",
        request_method="get",
    )

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["rsA", "rsB"]
    assert list(df.index) == ["rsA", "rsB"]
    assert float(df.loc["rsA", "rsB"]) == 0.75