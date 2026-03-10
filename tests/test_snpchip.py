# tests/test_snpchip.py

from __future__ import annotations

import pandas as pd
import pytest

import ldlinkpython.endpoints.snpchip as snpchip_mod


def test_snpchip_posts_and_parses_tsv(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    tsv = (
        "RS.Number\tCoord\tArrays\n"
        "rs3\tchr1:101\tIllumina Human1Mv1,Affymetrix SNP 5.0\n"
        "rs4\tchr1:202\tAffymetrix SNP 5.0\n"
    )

    def fake_request(**kwargs):
        captured.update(kwargs)
        return tsv

    monkeypatch.setattr(snpchip_mod, "http_request", fake_request)

    out = snpchip_mod.snpchip(
        snps=["rs3", "rs4"],
        chip=["A_SNP5.0", "I_1M"],
        genome_build="grch38",
        token="tok-123",
        api_root="https://example.org/LDlinkRest",
    )

    assert captured["endpoint"] == "snpchip"
    assert captured["method"] == "POST"
    body = captured["json_body"]
    assert isinstance(body, dict)
    assert body["snps"] == "rs3\nrs4"
    assert body["platforms"] == "A_SNP5.0+I_1M"
    assert body["genome_build"] == "grch38"

    assert isinstance(out, pd.DataFrame)
    assert list(out.columns) == ["RS_Number", "Coord", "I_1M", "A_SNP5.0"]
    assert out.loc[0, "I_1M"] == 1
    assert out.loc[0, "A_SNP5.0"] == 1
    assert out.loc[1, "I_1M"] == 0
    assert out.loc[1, "A_SNP5.0"] == 1


def test_snpchip_expands_all_platforms(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(snpchip_mod, "http_request", lambda **kwargs: captured.update(kwargs) or "RS.Number\tCoord\tArrays\n")

    out = snpchip_mod.snpchip(snps=["rs3"], chip="ALL", token="tok")

    assert isinstance(out, pd.DataFrame)
    body = captured["json_body"]
    assert isinstance(body, dict)
    platforms = body["platforms"]
    assert "I_100" in platforms
    assert "A_UKBA" in platforms
    assert "ALL" not in platforms


def test_snpchip_raw_return_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(snpchip_mod, "http_request", lambda **kwargs: "raw-text")

    out = snpchip_mod.snpchip(snps=["rs3"], token="tok", return_type="raw")
    assert out == "raw-text"


def test_snpchip_raises_on_error_row(monkeypatch: pytest.MonkeyPatch) -> None:
    tsv_error = "RS.Number\tCoord\tArrays\nrs3\tchr1:1\tAffymetrix SNP 5.0\nError: bad request\t\t\n"
    monkeypatch.setattr(snpchip_mod, "http_request", lambda **kwargs: tsv_error)
    with pytest.raises(RuntimeError, match="Error: bad request"):
        snpchip_mod.snpchip(snps=["rs3"], token="tok")


def test_snpchip_handles_missing_array_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    tsv = (
        "RS.Number\tCoord\tArrays\n"
        "rs3\tchr1:101\tIllumina Human1Mv1\n"
        "rs148890987\tchr7:24966446\tNA\n"
    )
    monkeypatch.setattr(snpchip_mod, "http_request", lambda **kwargs: tsv)

    out = snpchip_mod.snpchip(snps=["rs3", "rs148890987"], token="tok")
    assert isinstance(out, pd.DataFrame)
    assert list(out["RS_Number"]) == ["rs3", "rs148890987"]
    assert "I_1M" in out.columns
    assert out.loc[0, "I_1M"] == 1
    assert out.loc[1, "I_1M"] == 0


def test_snpchip_validation() -> None:
    with pytest.raises(Exception, match="1 to 5000 variants"):
        snpchip_mod.snpchip(snps=[], token="tok")

    with pytest.raises(Exception, match="Invalid query format"):
        snpchip_mod.snpchip(snps=["bad_variant"], token="tok")

    with pytest.raises(Exception, match="Invalid SNP chip array platform code"):
        snpchip_mod.snpchip(snps=["rs3"], chip="BAD", token="tok")

    with pytest.raises(Exception, match="Not an available genome build"):
        snpchip_mod.snpchip(snps=["rs3"], genome_build="hg19", token="tok")

    with pytest.raises(Exception, match="return_type must be 'dataframe' or 'raw'"):
        snpchip_mod.snpchip(snps=["rs3"], token="tok", return_type="json")
