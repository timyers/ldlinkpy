from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest



def test_ldproxy_batch_writes_one_file_per_snp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from ldlinkpy.endpoints import ldproxy_batch as ldproxy_batch_mod

    calls: list[str] = []

    def fake_ldproxy(**kwargs):
        calls.append(kwargs["snp"])
        return pd.DataFrame({"RS_Number": [kwargs["snp"]], "Coord": ["1:100"]})

    monkeypatch.setattr(ldproxy_batch_mod, "ldproxy", fake_ldproxy)
    monkeypatch.chdir(tmp_path)

    files = ldproxy_batch_mod.ldproxy_batch(
        snp="rs1\nrs2",
        pop="CEU",
        r2d="r2",
        token="tok",
        append=False,
        genome_build="grch37",
        win_size=500000,
    )

    assert calls == ["rs1", "rs2"]
    assert len(files) == 2
    assert (tmp_path / "rs1_grch37.txt").exists()
    assert (tmp_path / "rs2_grch37.txt").exists()


def test_ldproxy_batch_append_writes_combined_file_with_query_snp(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from ldlinkpy.endpoints import ldproxy_batch as ldproxy_batch_mod

    def fake_ldproxy(**kwargs):
        return pd.DataFrame(
            {
                "RS_Number": [kwargs["snp"], "rsX"],
                "Coord": ["1:100", "1:101"],
            }
        )

    monkeypatch.setattr(ldproxy_batch_mod, "ldproxy", fake_ldproxy)
    monkeypatch.chdir(tmp_path)

    files = ldproxy_batch_mod.ldproxy_batch(
        snp=["rs1", "rs2"],
        append=True,
        genome_build="grch38_high_coverage",
    )

    combined = tmp_path / "combined_query_snp_list_grch38_high_coverage.txt"
    assert files == [str(combined)]
    assert combined.exists()

    text = combined.read_text()
    assert "query_snp" in text
    assert "rs1" in text
    assert "rs2" in text


def test_ldproxy_batch_dataframe_input_supported(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from ldlinkpy.endpoints import ldproxy_batch as ldproxy_batch_mod

    called: list[str] = []

    def fake_ldproxy(**kwargs):
        called.append(kwargs["snp"])
        return pd.DataFrame({"RS_Number": [kwargs["snp"]], "Coord": ["1:100"]})

    monkeypatch.setattr(ldproxy_batch_mod, "ldproxy", fake_ldproxy)
    monkeypatch.chdir(tmp_path)

    snp_df = pd.DataFrame(["rs1", "chr7:24966446"])
    files = ldproxy_batch_mod.ldproxy_batch(snp=snp_df)

    assert len(files) == 2
    assert called == ["rs1", "chr7:24966446"]


def test_ldproxy_batch_validates_genome_build_and_window() -> None:
    from ldlinkpy.endpoints.ldproxy_batch import ldproxy_batch

    with pytest.raises(ValueError, match="genome_build"):
        ldproxy_batch(snp="rs1", genome_build="hg19")

    with pytest.raises(ValueError, match="win_size"):
        ldproxy_batch(snp="rs1", win_size=0)

    with pytest.raises(ValueError, match="win_size"):
        ldproxy_batch(snp="rs1", win_size=1_000_001)


def test_ldproxy_batch_real_api_calls_with_multiple_rsids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Real integration test against LDlink API (requires LDLINK_TOKEN)."""
    token = os.getenv("LDLINK_TOKEN")
    if not token:
        pytest.skip("LDLINK_TOKEN not set; skipping real API integration test.")

    from ldlinkpy.endpoints.ldproxy_batch import ldproxy_batch

    monkeypatch.chdir(tmp_path)

    snps = ["rs3", "rs7412"]
    try:
        files = ldproxy_batch(
            snp=snps,
            pop="CEU",
            r2d="r2",
            token=token,
            append=True,
            genome_build="grch37",
            win_size=50000,
        )
    except Exception as exc:  # pragma: no cover - environment/network dependent
        msg = str(exc)
        network_markers = (
            "ProxyError",
            "Tunnel connection failed",
            "Max retries exceeded",
            "Name or service not known",
            "Temporary failure in name resolution",
            "Connection refused",
            "timed out",
        )
        if any(marker in msg for marker in network_markers):
            pytest.skip(f"LDlink API not reachable from this environment: {exc}")
        raise

    combined = tmp_path / "combined_query_snp_list_grch37.txt"
    assert files == [str(combined)]
    assert combined.exists()

    text = combined.read_text()
    assert "query_snp" in text
    assert "rs3" in text
    assert "rs7412" in text
