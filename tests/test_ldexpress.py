from __future__ import annotations

from pathlib import Path

import pytest

from ldlinkpy.endpoints.ldexpress import ldexpress
from ldlinkpy.exceptions import LDlinkError


def test_ldexpress_posts_expected_body_and_parses_tsv(monkeypatch: pytest.MonkeyPatch) -> None:
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
        captured["api_root"] = api_root
        captured["token"] = token
        captured["params"] = params
        captured["json_body"] = json_body
        captured["headers"] = headers
        captured["timeout"] = timeout

        return (
            "Query\tRS ID\tPosition\tR2\tD.\tGene Symbol\tGencode ID\tTissue\tNon-effect Allele Freq\tEffect Allele Freq\tEffect Size\tP-value\n"
            "rs429358\trs429358\tchr19:45411941\t1.0\t1.0\tAPOE\tENSG00000130203.10\tWhole Blood\tC=0.9\tT=0.1\t0.2\t0.001\n"
        )

    monkeypatch.setattr("ldlinkpy.endpoints.ldexpress.request", fake_request)
    monkeypatch.setenv("LDLINK_TOKEN", "TESTTOKEN")

    df = ldexpress(
        snps=["rs429358", "chr7:24966446"],
        pop=["YRI", "CEU"],
        tissue=["ADI_SUB", "Whole_Blood"],
        r2d="r2",
        r2d_threshold=0.2,
        p_threshold=0.05,
        win_size=500000,
        genome_build="grch37",
        token=None,
    )

    assert captured["method"] == "POST"
    assert captured["endpoint"] == "/ldexpress"
    assert captured["params"] == {"token": "TESTTOKEN"}

    body = captured["json_body"]
    assert isinstance(body, dict)

    assert body["snps"] == "rs429358\nchr7:24966446"
    assert body["pop"] == "YRI+CEU"
    assert body["tissues"] == "Adipose_Subcutaneous+Whole_Blood"
    assert body["r2_d"] == "r2"
    assert body["r2_d_threshold"] == "0.2"
    assert body["p_threshold"] == "0.05"
    assert body["window"] == "500000"
    assert body["genome_build"] == "grch37"

    assert df.shape[0] == 1
    assert "D'" in df.columns
    assert "Position_grch37" in df.columns
    assert df.loc[0, "Query"] == "rs429358"


def test_ldexpress_all_tissue_expands(monkeypatch: pytest.MonkeyPatch) -> None:
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
        captured["json_body"] = json_body
        return "A\tB\n1\t2\n"

    monkeypatch.setattr("ldlinkpy.endpoints.ldexpress.request", fake_request)
    monkeypatch.setenv("LDLINK_TOKEN", "TESTTOKEN")

    _ = ldexpress(snps="rs429358", tissue="ALL")

    body = captured["json_body"]
    assert isinstance(body, dict)
    assert body["tissues"] != "ALL"
    assert "+" in body["tissues"]

def test_ldexpress_writes_output_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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
        return "A\tB\n1\t2\n"

    monkeypatch.setattr("ldlinkpy.endpoints.ldexpress.request", fake_request)
    monkeypatch.setenv("LDLINK_TOKEN", "TESTTOKEN")

    out_file = tmp_path / "ldexpress.tsv"
    df = ldexpress(snps="rs429358", file=str(out_file))

    assert out_file.exists()
    saved = out_file.read_text()
    assert "A\tB" in saved
    assert df.shape == (1, 2)


def test_ldexpress_raises_clean_error_on_json_payload(monkeypatch: pytest.MonkeyPatch) -> None:
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
        return {"error": "No entries found for genome build grch38"}

    monkeypatch.setattr("ldlinkpy.endpoints.ldexpress.request", fake_request)
    monkeypatch.setenv("LDLINK_TOKEN", "TESTTOKEN")

    with pytest.raises(LDlinkError, match="No entries found for genome build grch38"):
        ldexpress(snps="rs429358", genome_build="grch38", tissue="WHO_BLO")


def test_ldexpress_no_hits_returns_empty_dataframe_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
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
        return {"error": "No entries in GTEx are identified using the LDexpress search criteria."}

    monkeypatch.setattr("ldlinkpy.endpoints.ldexpress.request", fake_request)
    monkeypatch.setenv("LDLINK_TOKEN", "TESTTOKEN")

    df = ldexpress(snps="rs456", win_size=0)
    assert df.empty


def test_ldexpress_no_hits_raises_when_requested(monkeypatch: pytest.MonkeyPatch) -> None:
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
        return {"error": "No entries in GTEx are identified using the LDexpress search criteria."}

    monkeypatch.setattr("ldlinkpy.endpoints.ldexpress.request", fake_request)
    monkeypatch.setenv("LDLINK_TOKEN", "TESTTOKEN")

    with pytest.raises(LDlinkError, match="No entries in GTEx"):
        ldexpress(snps="rs456", win_size=0, on_no_hits="raise")


def test_ldexpress_on_no_hits_must_be_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LDLINK_TOKEN", "TESTTOKEN")
    with pytest.raises(ValueError, match="on_no_hits must be 'empty' or 'raise'."):
        ldexpress(snps="rs456", on_no_hits="nope")
