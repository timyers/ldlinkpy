# Codex implementation

from __future__ import annotations

import pandas as pd
import pytest

import ldlinkpy.endpoints.ldhap as ldhap_mod


def test_ldhap_calls_endpoint_and_parses_haplotype_table(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    tsv = (
        "RS_Number\tPosition (hg19)\tAllele Frequency\n"
        "rs3\tchr1:101\tA=0.5, G=0.5\n"
        "rs4\tchr1:202\tC=0.6, T=0.4\n"
        "#\t\t\n"
        "Haplotype\tCount\tFrequency\n"
        "A_C\t10\t0.10\n"
        "G_T\t90\t0.90\n"
    )

    def fake_request(**kwargs):
        captured.update(kwargs)
        return tsv

    monkeypatch.setattr(ldhap_mod, "http_request", fake_request)

    out = ldhap_mod.ldhap(
        snps=["rs3", "rs4"],
        pop=["ceu", "yri"],
        token="tok-123",
        genome_build="grch38_high_coverage",
        api_root="https://example.org/LDlinkRest",
    )

    assert captured["endpoint"] == "ldhap"
    assert captured["method"] == "GET"
    params = captured["params"]
    assert isinstance(params, dict)
    assert params["snps"] == "rs3\nrs4"
    assert params["pop"] == "CEU+YRI"
    assert params["genome_build"] == "grch38_high_coverage"

    assert isinstance(out, pd.DataFrame)
    assert list(out.columns) == ["rs3", "rs4", "Count", "Frequency"]
    assert out.shape == (2, 4)
    assert out.iloc[0].tolist() == ["A", "C", "10", "0.10"]


def test_ldhap_variant_and_both_outputs(monkeypatch: pytest.MonkeyPatch) -> None:
    tsv = (
        "RS_Number\tPosition (hg19)\tAllele Frequency\n"
        "rs3\tchr1:101\tA=0.5, G=0.5\n"
        "#\t\t\n"
        "Haplotype\tCount\tFrequency\n"
        "A\t10\t1.00\n"
    )

    monkeypatch.setattr(ldhap_mod, "http_request", lambda **kwargs: tsv)

    variant_df = ldhap_mod.ldhap(snps=["rs3"], token="tok", table_type="variant")
    assert isinstance(variant_df, pd.DataFrame)
    assert "Position_grch37" in variant_df.columns
    assert "Allele_Frequency" in variant_df.columns

    both_out = ldhap_mod.ldhap(snps=["rs3"], token="tok", table_type="both")
    assert isinstance(both_out, dict)
    assert set(both_out.keys()) == {"variant", "haplotype"}
    assert isinstance(both_out["variant"], pd.DataFrame)
    assert isinstance(both_out["haplotype"], pd.DataFrame)

    preview = both_out.head(1)
    assert isinstance(preview, dict)
    assert list(preview["variant"].index) == [0]
    assert list(preview["haplotype"].index) == [0]


def test_ldhap_validates_inputs() -> None:
    with pytest.raises(Exception, match="1 to 30 variants"):
        ldhap_mod.ldhap(snps=[], token="x")

    with pytest.raises(Exception, match="Invalid query format"):
        ldhap_mod.ldhap(snps=["bad_variant"], token="x")

    with pytest.raises(Exception, match="Not a valid population code"):
        ldhap_mod.ldhap(snps=["rs3"], pop="BAD", token="x")

    with pytest.raises(Exception, match="Not a valid option for table_type"):
        ldhap_mod.ldhap(snps=["rs3"], table_type="nope", token="x")

    with pytest.raises(Exception, match="Not an available genome build"):
        ldhap_mod.ldhap(snps=["rs3"], genome_build="hg19", token="x")


def test_ldhap_merged_output_no_duplicate_column_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    tsv = (
        "RS_Number\tPosition (hg19)\tAllele Frequency\n"
        "rs3\tchr13:32446842\tC=0.874, T=0.126\n"
        "rs4\tchr13:32447222\tA=0.874, G=0.126\n"
        "#\t\t\n"
        "Haplotype\tCount\tFrequency\n"
        "C_A\t362\t0.8744\n"
        "T_G\t52\t0.1256\n"
    )

    monkeypatch.setattr(ldhap_mod, "http_request", lambda **kwargs: tsv)

    merged = ldhap_mod.ldhap(snps=["rs3", "rs4"], token="tok", table_type="merged")
    assert isinstance(merged, pd.DataFrame)
    assert not merged.empty
    # Expect variant rows plus two summary rows (count/frequency)
    assert merged.shape == (4, 5)
    assert merged.loc[0, "Haplotypes"] == "C"
    assert merged.loc[1, "Haplotypes"] == "A"
    assert merged.iloc[2, 2] == "Haplotype_Count"
    assert merged.iloc[3, 2] == "Haplotype_Frequency"
