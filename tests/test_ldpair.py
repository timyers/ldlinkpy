from __future__ import annotations

import pytest

import ldlinkpy.endpoints.ldpair as ldpair_mod


def test_ldpair_single_pair_get_returns_dataframe(monkeypatch):
    def fake_http_request(
        path,
        token=None,
        api_root=None,
        method="GET",
        params=None,
        json=None,
    ):
        assert path == "ldpair"
        assert method == "GET"
        assert params is not None
        assert params["var1"] == "rs1"
        assert params["var2"] == "rs2"
        # Minimal TSV with header and one row
        return "SNP_A\tSNP_B\tR2\nrs1\trs2\t0.42\n"

    monkeypatch.setattr(ldpair_mod, "http_request", fake_http_request)

    df = ldpair_mod.ldpair(var1="rs1", var2="rs2", pop="CEU", genome_build="grch37", output="table")
    assert list(df.columns) == ["SNP_A", "SNP_B", "R2"]
    assert df.shape == (1, 3)
    assert df.loc[0, "SNP_A"] == "rs1"
    assert df.loc[0, "SNP_B"] == "rs2"
    assert float(df.loc[0, "R2"]) == pytest.approx(0.42)


def test_ldpair_multiple_pairs_post_returns_parsed_json(monkeypatch):
    def fake_http_request(
        path,
        token=None,
        api_root=None,
        method="GET",
        params=None,
        json=None,
    ):
        assert path == "ldpair"
        assert method == "POST"
        assert json is not None
        assert json["pop"] == "CEU"
        assert json["genome_build"] == "grch37"
        assert json["snp_pairs"] == [["rs1", "rs2"], ["rs3", "rs4"]]
        # Return text JSON to ensure endpoint parses it
        return '{"results":[{"var1":"rs1","var2":"rs2","r2":0.42},{"var1":"rs3","var2":"rs4","r2":0.11}]}'

    monkeypatch.setattr(ldpair_mod, "http_request", fake_http_request)

    out = ldpair_mod.ldpair(snp_pairs=[("rs1", "rs2"), ("rs3", "rs4")], pop="CEU", genome_build="grch37")
    assert isinstance(out, dict)
    assert "results" in out
    assert len(out["results"]) == 2
    assert out["results"][0]["var1"] == "rs1"
    assert out["results"][0]["var2"] == "rs2"


def test_ldpair_validation_errors_missing_or_ambiguous():
    # Missing one of var1/var2 for single pair
    with pytest.raises(ValueError):
        ldpair_mod.ldpair(var1="rs1", var2=None)

    with pytest.raises(ValueError):
        ldpair_mod.ldpair(var1=None, var2="rs2")

    # Ambiguous: both single vars and snp_pairs
    with pytest.raises(ValueError):
        ldpair_mod.ldpair(var1="rs1", var2="rs2", snp_pairs=[("rs3", "rs4")])

    # Empty snp_pairs
    with pytest.raises(ValueError):
        ldpair_mod.ldpair(snp_pairs=[])

    # Bad snp_pairs element shape
    with pytest.raises(ValueError):
        ldpair_mod.ldpair(snp_pairs=[("rs1",)])

    # Bad output
    with pytest.raises(ValueError):
        ldpair_mod.ldpair(var1="rs1", var2="rs2", output="json")

    # Bad request_method
    with pytest.raises(ValueError):
        ldpair_mod.ldpair(var1="rs1", var2="rs2", request_method="PUT")

    # request_method='get' not allowed for multiple pairs
    with pytest.raises(ValueError):
        ldpair_mod.ldpair(snp_pairs=[("rs1", "rs2"), ("rs3", "rs4")], request_method="get")
