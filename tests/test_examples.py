from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RREB1_EXAMPLE = REPO_ROOT / "examples" / "rreb1_haplotype_feasibility_grch37.py"
RREB1_SUMMARY_EXAMPLE = REPO_ROOT / "examples" / "rreb1_summarize_haplotype_feasibility.py"


def test_rreb1_example_help() -> None:
    result = subprocess.run(
        [sys.executable, str(RREB1_EXAMPLE), "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "RREB1" in result.stdout
    assert "--dry-run" in result.stdout


def test_rreb1_example_dry_run_without_token() -> None:
    result = subprocess.run(
        [sys.executable, str(RREB1_EXAMPLE), "--dry-run"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={},
    )

    assert result.returncode == 0
    assert "Dry run: no LDlink API calls will be made." in result.stdout
    assert "LDpair rs7742053 rs17142617 pop=EUR" in result.stdout
    assert "SNPchip rs7742053,rs17142617,rs74781311,rs2876045 chip=ALL" in result.stdout


def test_rreb1_summary_example_help() -> None:
    result = subprocess.run(
        [sys.executable, str(RREB1_SUMMARY_EXAMPLE), "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "LDlink API calls" in result.stdout
    assert "--make-plots" in result.stdout


def test_rreb1_summary_example_creates_report_from_minimal_inputs(tmp_path: Path) -> None:
    input_dir = tmp_path / "inputs"
    out_dir = tmp_path / "summary"
    input_dir.mkdir()

    (input_dir / "rreb1_variant_metadata.csv").write_text(
        "genome_build,variant,role,notes\n"
        "grch37,rs7742053,published lead GWAS SNP,Lead SNP.\n"
        "grch37,rs17142617,published high-LD surrogate/tag SNP and 3-SNP haplotype marker,Surrogate SNP.\n",
        encoding="utf-8",
    )
    (input_dir / "manifest.json").write_text(
        '{"example": "synthetic RREB1 example"}',
        encoding="utf-8",
    )
    (input_dir / "ldpair_rs7742053_rs17142617_EUR.csv").write_text(
        "SNP_A,Coord_A,SNP_B,Coord_B,Population,Dprime,R2,ChiSq,PValue,Haplotypes,Correlated_Alleles\n"
        "rs7742053,chr6:6841452,rs17142617,chr6:6838025,EUR,0.99,0.95,10,<0.0001,A_G=1,alleles\n",
        encoding="utf-8",
    )
    (input_dir / "ldpop_rs7742053_rs17142617_ALL.csv").write_text(
        "Population,Abbrev,N,rs7742053 Allele Freq,rs17142617 Allele Freq,R2,D',Chisq,P\n"
        "European,EUR,503,A: 12%,G: 12%,0.95,0.99,10,0\n",
        encoding="utf-8",
    )
    (input_dir / "ldmatrix_rreb1_4snp_EUR.csv").write_text(
        "variant,rs7742053,rs17142617\n"
        "rs7742053,1,0.95\n"
        "rs17142617,0.95,1\n",
        encoding="utf-8",
    )
    (input_dir / "ldhap_rreb1_3snp_EUR.csv").write_text(
        "rs17142617,rs74781311,rs2876045,Count,Frequency\n"
        "A,T,T,10,0.8\n"
        "G,G,C,2,0.2\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(RREB1_SUMMARY_EXAMPLE),
            "--input-dir",
            str(input_dir),
            "--out-dir",
            str(out_dir),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={},
    )

    assert result.returncode == 0
    assert (out_dir / "report.md").exists()
    assert (out_dir / "workflow_diagram.mmd").exists()
    assert (out_dir / "rreb1_variant_summary.csv").exists()
    assert (out_dir / "rreb1_pairwise_ld_summary.csv").exists()
    assert (out_dir / "rreb1_ldmatrix_file_index.csv").exists()
    assert (out_dir / "rreb1_haplotype_frequency_summary.csv").exists()
    assert (out_dir / "rreb1_practical_feasibility_summary.csv").exists()
    assert (out_dir / "rreb1_ldmatrix_long_format.csv").exists()
    assert not (out_dir / "rreb1_snpchip_summary.csv").exists()

    report = (out_dir / "report.md").read_text(encoding="utf-8")
    assert "No LDlink API calls were made." in report
    assert "## Key findings" in report
    assert "### Lead SNP / surrogate SNP LD by population" in report
    assert "R2 and Dprime capture different aspects" in report
    assert "allele orientation and variant order should be confirmed" in report
    assert "rare haplotypes may not appear" in report
    assert "## Conclusion" in report
    assert "published RREB1 SNP-tag strategy" in report
    assert "## References" in report
    assert "- LDlinkPy workflow diagram" not in report
    assert "SNPchip output was not detected" in report
