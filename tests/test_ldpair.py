from __future__ import annotations

import pytest

import ldlinkpy.endpoints.ldpair as ldpair_mod


LDPAIR_TEXT_REPORT = """Query SNPs:
rs7742053 (chr6:6841452)
rs17142617 (chr6:6838025)

EUR Haplotypes:
               rs17142617
               A       G
             -----------------
           A | 1     | 120   | 121   (0.12)
rs7742053    -----------------
           C | 881   | 4     | 885   (0.88)
             -----------------
               882     124     1006
              (0.877) (0.123)

          C_A: 881 (0.876)
          A_G: 120 (0.119)
          C_G: 4 (0.004)
          A_A: 1 (0.001)

          D': 0.9906
          R2: 0.9543
      Chi-sq: 959.9763
     p-value: <0.0001

rs7742053(A) allele is correlated with rs17142617(G) allele
rs7742053(C) allele is correlated with rs17142617(A) allele
"""


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


def test_ldpair_single_pair_text_report_returns_rectangular_dataframe(monkeypatch):
    monkeypatch.setattr(ldpair_mod, "http_request", lambda *args, **kwargs: LDPAIR_TEXT_REPORT)

    df = ldpair_mod.ldpair(
        var1="rs7742053",
        var2="rs17142617",
        pop="EUR",
        genome_build="grch37",
        output="table",
    )

    assert list(df.columns) == [
        "SNP_A",
        "Coord_A",
        "SNP_B",
        "Coord_B",
        "Population",
        "Dprime",
        "R2",
        "ChiSq",
        "PValue",
        "Haplotypes",
        "Correlated_Alleles",
    ]
    assert df.shape == (1, 11)
    assert df.loc[0, "SNP_A"] == "rs7742053"
    assert df.loc[0, "Coord_A"] == "chr6:6841452"
    assert df.loc[0, "SNP_B"] == "rs17142617"
    assert df.loc[0, "Coord_B"] == "chr6:6838025"
    assert df.loc[0, "Population"] == "EUR"
    assert df.loc[0, "Dprime"] == "0.9906"
    assert df.loc[0, "R2"] == "0.9543"
    assert df.loc[0, "ChiSq"] == "959.9763"
    assert df.loc[0, "PValue"] == "<0.0001"
    assert "C_A=881 (0.876)" in df.loc[0, "Haplotypes"]
    assert (
        "rs7742053(A) allele is correlated with rs17142617(G) allele"
        in df.loc[0, "Correlated_Alleles"]
    )


def test_ldpair_multiple_pairs_post_returns_parsed_json(monkeypatch):
    def fake_http_request(
        path,
        token=None,
        api_root=None,
        method="GET",
        params=None,
        json_body=None,
    ):
        assert path == "ldpair"
        assert method == "POST"
        assert json_body is not None
        assert json_body["pop"] == "CEU"
        assert json_body["genome_build"] == "grch37"
        assert json_body["snp_pairs"] == [["rs1", "rs2"], ["rs3", "rs4"]]
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


def test_ldpair_accepts_population_list_and_high_coverage_build(monkeypatch):
    def fake_http_request(path, token=None, api_root=None, method="GET", params=None, json_body=None):
        assert path == "ldpair"
        assert method == "GET"
        assert params is not None
        assert params["pop"] == "CEU+YRI"
        assert params["genome_build"] == "grch38_high_coverage"
        return "SNP_A\tSNP_B\tR2\nrs1\trs2\t0.42\n"

    monkeypatch.setattr(ldpair_mod, "http_request", fake_http_request)

    out = ldpair_mod.ldpair(
        var1="rs1",
        var2="rs2",
        pop=["ceu", "yri"],
        genome_build="grch38_high_coverage",
    )
    assert out.shape == (1, 3)


def test_ldpair_writes_output_file(tmp_path, monkeypatch):
    monkeypatch.setattr(ldpair_mod, "http_request", lambda *args, **kwargs: "SNP_A\tSNP_B\tR2\nrs1\trs2\t0.42\n")

    out_file = tmp_path / "nested" / "ldpair.tsv"
    df = ldpair_mod.ldpair(var1="rs1", var2="rs2", token="x", file=str(out_file))

    assert out_file.exists()
    assert "SNP_A\tSNP_B\tR2" in out_file.read_text(encoding="utf-8")
    assert df.shape == (1, 3)


def test_ldpair_writes_text_report_table_as_tsv(tmp_path, monkeypatch):
    monkeypatch.setattr(ldpair_mod, "http_request", lambda *args, **kwargs: LDPAIR_TEXT_REPORT)

    out_file = tmp_path / "ldpair_table.tsv"
    df = ldpair_mod.ldpair(
        var1="rs7742053",
        var2="rs17142617",
        pop="EUR",
        token="x",
        file=str(out_file),
    )

    written = out_file.read_text(encoding="utf-8")
    assert written.startswith("SNP_A\tCoord_A\tSNP_B\tCoord_B\tPopulation")
    assert "Query SNPs:" not in written
    assert "0.9543" in written
    assert df.shape == (1, 11)


def test_ldpair_validates_variant_pop_genome_build_and_file():
    with pytest.raises(ValueError, match="var1 must be an rsID"):
        ldpair_mod.ldpair(var1="bad", var2="rs2")

    with pytest.raises(ValueError, match="Not a valid population code"):
        ldpair_mod.ldpair(var1="rs1", var2="rs2", pop="BAD")

    with pytest.raises(ValueError, match="Invalid genome build"):
        ldpair_mod.ldpair(var1="rs1", var2="rs2", genome_build="hg19")

    with pytest.raises(ValueError, match="file must be a string path or False"):
        ldpair_mod.ldpair(var1="rs1", var2="rs2", file=123)
