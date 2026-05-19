#!/usr/bin/env python3
"""End-to-end LDlinkPy example for the RREB1 Ewing sarcoma locus.

This workflow evaluates published SNP tags at the Ewing sarcoma
6p25.1/RREB1 susceptibility locus using LDlinkPy outputs only.

It does not measure, infer, or reproduce GGAA microsatellite length.
The original biological result depends on targeted long-read sequencing
of the GGAA microsatellite; this example evaluates whether the published
SNP tags and haplotype markers look practical for standard SNP-based
analyses across 1000 Genomes populations.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from ldlinkpy import __version__, ldhap, ldmatrix, ldpair, ldpop, snpchip
except ModuleNotFoundError:
    # Allow `python examples/rreb1_haplotype_feasibility_grch37.py` from a
    # source checkout before the package has been installed.
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    from ldlinkpy import __version__, ldhap, ldmatrix, ldpair, ldpop, snpchip


LEAD_SNP = "rs7742053"
SURROGATE_SNP = "rs17142617"

HAPLOTYPE_SNPS = [
    "rs17142617",
    "rs74781311",
    "rs2876045",
]

RREB1_FOUR_SNPS = [
    "rs7742053",
    "rs17142617",
    "rs74781311",
    "rs2876045",
]

DEFAULT_POPULATIONS = ["EUR", "AFR", "AMR", "EAS", "SAS"]
DEFAULT_GENOME_BUILD = "grch37"
DEFAULT_OUT_DIR = Path("examples/output/rreb1_haplotype_feasibility_grch37")

KEY_PAIRS = [
    ("rs7742053", "rs17142617"),
    ("rs17142617", "rs74781311"),
    ("rs17142617", "rs2876045"),
    ("rs74781311", "rs2876045"),
]

VARIANT_METADATA = [
    {
        "variant": "rs7742053",
        "role": "published lead GWAS SNP",
        "notes": "Lead 6p25.1/RREB1 Ewing sarcoma GWAS SNP.",
    },
    {
        "variant": "rs17142617",
        "role": "published high-LD surrogate/tag SNP and 3-SNP haplotype marker",
        "notes": (
            "Published surrogate SNP in high LD with rs7742053; part of the "
            "3-SNP haplotype."
        ),
    },
    {
        "variant": "rs74781311",
        "role": "published 3-SNP haplotype marker",
        "notes": (
            "Part of the published 3-SNP haplotype associated with longer "
            "GGAA microsatellite alleles."
        ),
    },
    {
        "variant": "rs2876045",
        "role": "published 3-SNP haplotype marker",
        "notes": (
            "Part of the published 3-SNP haplotype associated with longer "
            "GGAA microsatellite alleles."
        ),
    },
]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate published RREB1 SNP tags using LDpair, LDpop, "
            "LDmatrix, LDhap, and SNPchip."
        )
    )
    parser.add_argument(
        "--token",
        default=None,
        help=(
            "LDlink API token. If omitted, LDLINK_TOKEN is read from the "
            "environment. The token is never printed or saved."
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"Output directory. Default: {DEFAULT_OUT_DIR}",
    )
    parser.add_argument(
        "--genome-build",
        default=DEFAULT_GENOME_BUILD,
        help="Genome build for LDlink calls. Default: grch37",
    )
    parser.add_argument(
        "--populations",
        nargs="+",
        default=DEFAULT_POPULATIONS,
        help="1000 Genomes super-populations for LDmatrix and LDhap.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned LDlinkPy calls without requiring a token.",
    )
    return parser.parse_args(argv)


def resolve_token(cli_token: str | None) -> str:
    token = cli_token or os.environ.get("LDLINK_TOKEN")
    if not token:
        raise SystemExit(
            "No LDlink token found. Set LDLINK_TOKEN or pass --token. "
            "Use --dry-run to preview calls without a token."
        )
    return token


def result_to_dataframe(result: Any) -> pd.DataFrame:
    if isinstance(result, pd.DataFrame):
        return result

    if isinstance(result, Mapping):
        if result and all(isinstance(value, pd.DataFrame) for value in result.values()):
            frames = []
            for key, value in result.items():
                frame = value.copy()
                frame.insert(0, "table", str(key))
                frames.append(frame)
            return pd.concat(frames, ignore_index=True)
        try:
            return pd.json_normalize(result)
        except Exception:
            return pd.DataFrame(
                [{"key": str(key), "value": json.dumps(value, default=str)} for key, value in result.items()]
            )

    if isinstance(result, list):
        try:
            return pd.json_normalize(result)
        except Exception:
            return pd.DataFrame({"value": [json.dumps(item, default=str) for item in result]})

    if isinstance(result, str):
        if "\t" in result:
            try:
                return pd.read_csv(StringIO(result), sep="\t")
            except Exception:
                pass
        return pd.DataFrame({"response": [result]})

    return pd.DataFrame({"value": [str(result)]})


def save_csv(result: Any, path: Path) -> None:
    dataframe = result_to_dataframe(result)
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(dataframe.index, pd.RangeIndex):
        dataframe.to_csv(path, index=False)
    else:
        dataframe.to_csv(path, index=True, index_label="variant")


def write_variant_metadata(out_dir: Path, genome_build: str) -> Path:
    metadata = []
    for row in VARIANT_METADATA:
        metadata.append({"genome_build": genome_build, **row})

    out_path = out_dir / "rreb1_variant_metadata.csv"
    pd.DataFrame(metadata).to_csv(out_path, index=False)
    return out_path


def print_plan(populations: Sequence[str], genome_build: str, out_dir: Path) -> None:
    print("Dry run: no LDlink API calls will be made.")
    print(f"Output directory: {out_dir}")
    print(f"Genome build: {genome_build}")
    print(f"Lead SNP: {LEAD_SNP}")
    print(f"Surrogate SNP: {SURROGATE_SNP}")
    print(f"Haplotype SNPs: {', '.join(HAPLOTYPE_SNPS)}")
    print(f"4-SNP set: {', '.join(RREB1_FOUR_SNPS)}")
    print("")
    print("Planned calls:")
    for var1, var2 in KEY_PAIRS:
        print(f"- LDpair {var1} {var2} pop=EUR")
    for var1, var2 in KEY_PAIRS:
        print(f"- LDpop {var1} {var2} pop=ALL")
    for pop in populations:
        print(f"- LDmatrix {','.join(RREB1_FOUR_SNPS)} pop={pop}")
    for pop in populations:
        print(f"- LDhap {','.join(HAPLOTYPE_SNPS)} pop={pop}")
    print(f"- SNPchip {','.join(RREB1_FOUR_SNPS)} chip=ALL")


def run_call(
    endpoint: str,
    output_path: Path,
    call: Callable[[], Any],
    completed: list[str],
    failed: list[dict[str, str]],
) -> None:
    print(f"Running {endpoint}: writing {output_path.name}")
    try:
        result = call()
    except Exception as exc:
        print(f"  Skipped after error: {exc}")
        failed.append({"endpoint": endpoint, "error": str(exc)})
        return

    save_csv(result, output_path)
    completed.append(endpoint)
    print("  Saved")


def write_manifest(
    out_dir: Path,
    genome_build: str,
    populations: Sequence[str],
    attempted: Sequence[str],
    completed: Sequence[str],
    failed: Sequence[Mapping[str, str]],
    skipped_optional: Sequence[str],
) -> Path:
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "example": "RREB1 haplotype feasibility example, GRCh37",
        "internal_planning_name": "RREB1 Plan B",
        "ldlinkpy_version": __version__,
        "genome_build": genome_build,
        "lead_snp": LEAD_SNP,
        "surrogate_snp": SURROGATE_SNP,
        "haplotype_snps": HAPLOTYPE_SNPS,
        "rreb1_four_snp_set": RREB1_FOUR_SNPS,
        "populations": list(populations),
        "endpoints_attempted": list(attempted),
        "endpoints_completed": list(completed),
        "failed_calls": list(failed),
        "skipped_optional_endpoints": list(skipped_optional),
    }
    out_path = out_dir / "manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out_path


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    genome_build = str(args.genome_build).lower()
    populations = [str(pop).upper() for pop in args.populations]

    if args.dry_run:
        print_plan(populations=populations, genome_build=genome_build, out_dir=args.out_dir)
        return 0

    token = resolve_token(args.token)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    attempted: list[str] = []
    completed: list[str] = []
    failed: list[dict[str, str]] = []
    skipped_optional = [
        "SNPclip (not used in this focused first version; no LD pruning needed)",
    ]

    metadata_path = write_variant_metadata(args.out_dir, genome_build)
    print(f"Wrote {metadata_path.name}")

    for var1, var2 in KEY_PAIRS:
        endpoint = f"LDpair {var1}/{var2} EUR"
        attempted.append(endpoint)
        out_path = args.out_dir / f"ldpair_{var1}_{var2}_EUR.csv"
        run_call(
            endpoint,
            out_path,
            lambda var1=var1, var2=var2: ldpair(
                var1=var1,
                var2=var2,
                pop="EUR",
                genome_build=genome_build,
                token=token,
            ),
            completed,
            failed,
        )

    for var1, var2 in KEY_PAIRS:
        endpoint = f"LDpop {var1}/{var2} ALL"
        attempted.append(endpoint)
        out_path = args.out_dir / f"ldpop_{var1}_{var2}_ALL.csv"
        run_call(
            endpoint,
            out_path,
            lambda var1=var1, var2=var2: ldpop(
                var1=var1,
                var2=var2,
                pop="ALL",
                genome_build=genome_build,
                token=token,
            ),
            completed,
            failed,
        )

    for pop in populations:
        endpoint = f"LDmatrix RREB1 4-SNP set {pop}"
        attempted.append(endpoint)
        out_path = args.out_dir / f"ldmatrix_rreb1_4snp_{pop}.csv"
        run_call(
            endpoint,
            out_path,
            lambda pop=pop: ldmatrix(
                snps=RREB1_FOUR_SNPS,
                pop=pop,
                genome_build=genome_build,
                token=token,
            ),
            completed,
            failed,
        )

    for pop in populations:
        endpoint = f"LDhap RREB1 3-SNP haplotype {pop}"
        attempted.append(endpoint)
        out_path = args.out_dir / f"ldhap_rreb1_3snp_{pop}.csv"
        run_call(
            endpoint,
            out_path,
            lambda pop=pop: ldhap(
                snps=HAPLOTYPE_SNPS,
                pop=pop,
                table_type="haplotype",
                genome_build=genome_build,
                token=token,
            ),
            completed,
            failed,
        )

    endpoint = "SNPchip RREB1 4-SNP set ALL chips"
    attempted.append(endpoint)
    run_call(
        endpoint,
        args.out_dir / "snpchip_rreb1_4snp.csv",
        lambda: snpchip(
            snps=RREB1_FOUR_SNPS,
            chip="ALL",
            genome_build=genome_build,
            token=token,
        ),
        completed,
        failed,
    )

    manifest_path = write_manifest(
        out_dir=args.out_dir,
        genome_build=genome_build,
        populations=populations,
        attempted=attempted,
        completed=completed,
        failed=failed,
        skipped_optional=skipped_optional,
    )
    print(f"Wrote {manifest_path.name}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
