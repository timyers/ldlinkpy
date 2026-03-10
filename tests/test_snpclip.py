# tests/test_snpclip.py

from __future__ import annotations

import pandas as pd
import pytest

import ldlinkpython.endpoints.snpclip as snpclip_mod


def test_snpclip_posts_and_parses_tsv(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    tsv = (
        "RS_Number\tCoord.hg19\tMAF\n"
        "rs3\tchr1:101\t0.12\n"
        "rs4\tchr1:202\t0.08\n"
    )

    def fake_request(**kwargs):
        captured.update(kwargs)
        return tsv

    monkeypatch.setattr(snpclip_mod, "http_request", fake_request)

    out = snpclip_mod.snpclip(
        snps=["rs3", "rs4"],
        pop=["ceu", "yri"],
        r2_threshold=0.2,
        maf_threshold=0.05,
        genome_build="grch38",
        token="tok-123",
        api_root="https://example.org/LDlinkRest",
    )

    assert captured["endpoint"] == "snpclip"
    assert captured["method"] == "POST"
    body = captured["json_body"]
    assert isinstance(body, dict)
    assert body["snps"] == "rs3\nrs4"
    assert body["pop"] == "CEU+YRI"
    assert body["r2_threshold"] == "0.2"
    assert body["maf_threshold"] == "0.05"
    assert body["genome_build"] == "grch38"

    assert isinstance(out, pd.DataFrame)
    assert list(out.columns) == ["RS_Number", "Coord_hg19", "MAF"]
    assert out.shape == (2, 3)


def test_snpclip_raw_return_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(snpclip_mod, "http_request", lambda **kwargs: "raw-text")

    out = snpclip_mod.snpclip(snps=["rs3"], token="tok", return_type="raw")
    assert out == "raw-text"


def test_snpclip_writes_file(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    tsv = "RS_Number\tCoord.hg19\nrs3\tchr1:101\n"
    monkeypatch.setattr(snpclip_mod, "http_request", lambda **kwargs: tsv)

    out_file = tmp_path / "snpclip.tsv"
    out = snpclip_mod.snpclip(snps=["rs3"], token="tok", file=str(out_file))

    assert isinstance(out, pd.DataFrame)
    assert out_file.exists()
    assert "RS_Number\tCoord_hg19" in out_file.read_text()


def test_snpclip_raises_on_error_or_warning_row(monkeypatch: pytest.MonkeyPatch) -> None:
    tsv_error = "A\tB\nrow\t1\nError: bad request\t\n"
    monkeypatch.setattr(snpclip_mod, "http_request", lambda **kwargs: tsv_error)
    with pytest.raises(RuntimeError, match="Error: bad request"):
        snpclip_mod.snpclip(snps=["rs3"], token="tok")


def test_snpclip_validation() -> None:
    with pytest.raises(Exception, match="1 to 5000 variants"):
        snpclip_mod.snpclip(snps=[], token="tok")

    with pytest.raises(Exception, match="Invalid query format"):
        snpclip_mod.snpclip(snps=["bad_variant"], token="tok")

    with pytest.raises(Exception, match="Not a valid population code"):
        snpclip_mod.snpclip(snps=["rs3"], pop="BAD", token="tok")

    with pytest.raises(Exception, match="R2 threshold must be between 0 and 1"):
        snpclip_mod.snpclip(snps=["rs3"], r2_threshold=2, token="tok")

    with pytest.raises(Exception, match="MAF threshold must be between 0 and 1"):
        snpclip_mod.snpclip(snps=["rs3"], maf_threshold=-1, token="tok")

    with pytest.raises(Exception, match="Not an available genome build"):
        snpclip_mod.snpclip(snps=["rs3"], genome_build="hg19", token="tok")

    with pytest.raises(Exception, match="Invalid input for file option"):
        snpclip_mod.snpclip(snps=["rs3"], token="tok", file=123)

    with pytest.raises(Exception, match="return_type must be 'dataframe' or 'raw'"):
        snpclip_mod.snpclip(snps=["rs3"], token="tok", return_type="json")
