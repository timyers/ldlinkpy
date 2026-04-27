from __future__ import annotations

import json

import pytest

from ldlinkpy.endpoints.ldtrait import ldtrait


def test_ldtrait_posts_expected_body_and_parses_tsv(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_request(  # type: ignore[no-untyped-def]
        endpoint: str,
        *,
        params: dict | None = None,
        json_body: dict | None = None,
        headers: dict | None = None,
        token: str | None = None,
        api_root: str,
        method: str = "GET",
        timeout: float = 180.0,
    ) -> str:
        captured["method"] = method
        captured["endpoint"] = endpoint
        captured["token"] = token
        captured["params"] = params
        captured["json_body"] = json_body
        captured["headers"] = headers
        captured["timeout"] = timeout

        return "RS_Number\tR2\nrs3\t0.99\n"

    monkeypatch.setattr("ldlinkpy.endpoints.ldtrait.request", fake_request)
    monkeypatch.setenv("LDLINK_TOKEN", "TESTTOKEN")

    df = ldtrait(
        snps=["rs3", "chr7:24966446"],
        pop=["YRI", "CEU"],
        r2d="r2",
        r2d_threshold=0.2,
        win_size=0,
        genome_build="grch38",
    )

    assert captured["method"] == "POST"
    assert captured["endpoint"] == "ldtrait"
    assert captured["token"] == "TESTTOKEN"
    assert isinstance(captured["params"], dict)
    assert captured["json_body"] is None

    params = captured["params"]
    assert isinstance(params, dict)
    assert params["snps"] == "rs3\nchr7:24966446"
    assert params["pop"] == "YRI+CEU"
    assert params["r2_d"] == "r2"
    assert params["r2_d_threshold"] == "0.2"
    assert params["window"] == "0"
    assert params["genome_build"] == "grch38"

    assert list(df.columns) == ["RS_Number", "R2"]
    assert df.loc[0, "RS_Number"] == "rs3"


def test_ldtrait_get_mode_calls_ldtraitget(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_request(  # type: ignore[no-untyped-def]
        endpoint: str,
        *,
        params: dict | None = None,
        json_body: dict | None = None,
        headers: dict | None = None,
        token: str | None = None,
        api_root: str,
        method: str = "GET",
        timeout: float = 180.0,
    ) -> str:
        captured["method"] = method
        captured["endpoint"] = endpoint
        captured["params"] = params
        return "A\tB\n1\t2\n"

    monkeypatch.setattr("ldlinkpy.endpoints.ldtrait.request", fake_request)
    monkeypatch.setenv("LDLINK_TOKEN", "TESTTOKEN")

    _ = ldtrait(snps="rs3", request_method="get")

    assert captured["method"] == "GET"
    assert captured["endpoint"] == "ldtraitget"


def test_ldtrait_validates_parity_constraints() -> None:
    with pytest.raises(ValueError, match="Input is between 1 to 50 variants"):
        ldtrait(snps=[f"rs{i}" for i in range(60)], token="tok")

    with pytest.raises(ValueError, match="Invalid query format for variant"):
        ldtrait(snps=["not-a-snp"], token="tok")

    with pytest.raises(ValueError, match="Not a valid population code"):
        ldtrait(snps="rs3", pop="BAD", token="tok")

    with pytest.raises(ValueError, match="Window size must be between 0 and 1000000 bp"):
        ldtrait(snps="rs3", win_size=1_000_001, token="tok")

    with pytest.raises(ValueError, match="Window size must be between 0 and 1000000 bp"):
        ldtrait(snps="rs3", win_size=False, token="tok")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Invalid input for file option"):
        ldtrait(snps="rs3", file=123, token="tok")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="on_no_hits must be 'empty' or 'raise'"):
        ldtrait(snps="rs3", on_no_hits="bad", token="tok")  # type: ignore[arg-type]


def test_ldtrait_no_hits_returns_empty_dataframe_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(  # type: ignore[no-untyped-def]
        endpoint: str,
        *,
        params: dict | None = None,
        json_body: dict | None = None,
        headers: dict | None = None,
        token: str | None = None,
        api_root: str,
        method: str = "GET",
        timeout: float = 180.0,
    ) -> dict[str, str]:
        return {"error": "No entries in the GWAS Catalog are identified using the LDtrait search criteria."}

    monkeypatch.setattr("ldlinkpy.endpoints.ldtrait.request", fake_request)
    monkeypatch.setenv("LDLINK_TOKEN", "TESTTOKEN")

    df = ldtrait(snps="rs3")
    assert df.empty


def test_ldtrait_no_hits_can_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(  # type: ignore[no-untyped-def]
        endpoint: str,
        *,
        params: dict | None = None,
        json_body: dict | None = None,
        headers: dict | None = None,
        token: str | None = None,
        api_root: str,
        method: str = "GET",
        timeout: float = 180.0,
    ) -> dict[str, str]:
        return {"error": "No entries in the GWAS Catalog are identified using the LDtrait search criteria."}

    monkeypatch.setattr("ldlinkpy.endpoints.ldtrait.request", fake_request)
    monkeypatch.setenv("LDLINK_TOKEN", "TESTTOKEN")

    with pytest.raises(RuntimeError, match="does not contain records"):
        ldtrait(snps="rs3", on_no_hits="raise")


def test_ldtrait_raw_json_payload_writes_file(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    def fake_request(  # type: ignore[no-untyped-def]
        endpoint: str,
        *,
        params: dict | None = None,
        json_body: dict | None = None,
        headers: dict | None = None,
        token: str | None = None,
        api_root: str,
        method: str = "GET",
        timeout: float = 180.0,
    ) -> dict[str, str]:
        return {"error": "No entries in the GWAS Catalog are identified using the LDtrait search criteria."}

    monkeypatch.setattr("ldlinkpy.endpoints.ldtrait.request", fake_request)
    monkeypatch.setenv("LDLINK_TOKEN", "TESTTOKEN")

    out_file = tmp_path / "ldtrait_raw.json"
    payload = ldtrait(snps="rs3", return_type="raw", file=str(out_file))

    assert payload == {"error": "No entries in the GWAS Catalog are identified using the LDtrait search criteria."}
    assert out_file.exists()
    assert json.loads(out_file.read_text(encoding="utf-8")) == payload
