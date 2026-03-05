from __future__ import annotations

import pandas as pd
import pytest

import ldlinkpython.endpoints.ldpop as ldpop_mod


def test_ldpop_calls_endpoint_and_parses(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    tsv = "Population\tR2\tD.\tchr7.24966446\nCEU\t0.8\t0.9\tA\n"

    def fake_request(**kwargs):
        captured.update(kwargs)
        return tsv

    monkeypatch.setattr(ldpop_mod, "http_request", fake_request)

    out = ldpop_mod.ldpop(
        var1="rs3",
        var2="chr7:24966446",
        pop=["ceu", "yri"],
        r2d="r2",
        token="tok-123",
        genome_build="grch38_high_coverage",
        api_root="https://example.org/LDlinkRest",
    )

    assert captured["endpoint"] == "ldpop"
    assert captured["method"] == "GET"
    params = captured["params"]
    assert isinstance(params, dict)
    assert params["var1"] == "rs3"
    assert params["var2"] == "chr7:24966446"
    assert params["pop"] == "CEU+YRI"
    assert params["r2_d"] == "r2"
    assert params["genome_build"] == "grch38_high_coverage"

    assert isinstance(out, pd.DataFrame)
    assert "D'" in out.columns
    assert "chr7:24966446" in out.columns


def test_ldpop_validates_inputs() -> None:
    with pytest.raises(Exception, match="Invalid query SNP format for Variant 1"):
        ldpop_mod.ldpop(var1="bad", var2="rs4", token="x")

    with pytest.raises(Exception, match="Invalid query SNP format for Variant 2"):
        ldpop_mod.ldpop(var1="rs3", var2="bad", token="x")

    with pytest.raises(Exception, match="Not a valid population code"):
        ldpop_mod.ldpop(var1="rs3", var2="rs4", pop="BAD", token="x")

    with pytest.raises(Exception, match="Not a valid r2d"):
        ldpop_mod.ldpop(var1="rs3", var2="rs4", r2d="bad", token="x")

    with pytest.raises(Exception, match="Not an available genome build"):
        ldpop_mod.ldpop(var1="rs3", var2="rs4", genome_build="hg19", token="x")


def test_ldpop_raises_runtime_error_on_error_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ldpop_mod,
        "http_request",
        lambda **kwargs: "error\tmessage\nERROR: something bad\tx\n",
    )

    with pytest.raises(RuntimeError, match="ERROR: something bad"):
        ldpop_mod.ldpop(var1="rs3", var2="rs4", token="x")


def test_ldpop_writes_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ldpop_mod, "http_request", lambda **kwargs: "A\tB\n1\t2\n")

    out_file = tmp_path / "nested" / "ldpop.tsv"
    out = ldpop_mod.ldpop(var1="rs3", var2="rs4", token="x", file=str(out_file))

    assert out_file.exists()
    written = out_file.read_text()
    assert "A\tB" in written
    assert isinstance(out, pd.DataFrame)
