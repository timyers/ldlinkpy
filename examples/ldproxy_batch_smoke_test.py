"""Simple local smoke tests for ldproxy_batch.

Run from repo root:
    # ephemeral run (files are auto-deleted)
    PYTHONPATH=. python examples/ldproxy_batch_smoke_test.py

        # persistent run (files are saved for inspection)
    PYTHONPATH=. python examples/ldproxy_batch_smoke_test.py --outdir ./tmp_ldproxy_batch_outputs

    # persistent run to the repo-local ignored tmp/ directory
    PYTHONPATH=. python examples/ldproxy_batch_smoke_test.py --repo-tmp
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from ldlinkpy.endpoints import ldproxy_batch as ldproxy_batch_mod


def _fake_ldproxy(**kwargs):
    snp = kwargs["snp"]
    return pd.DataFrame(
        {
            "RS_Number": [snp, "rsX"],
            "Coord": ["1:100", "1:101"],
            "R2": ["1.0", "0.8"],
        }
    )


def _run_examples(workdir: Path) -> None:
    old_cwd = Path.cwd()
    os.chdir(workdir)
    try:
        # Example 1: one output file per SNP (append=False)
        ldproxy_batch_mod.ldproxy_batch(
            snp="rs123\nchr7:24966446",
            pop="CEU",
            r2d="r2",
            append=False,
            genome_build="grch37",
            win_size=500000,
            token="fake-token",
        )
        print("[smoke] append=False files:")
        for p in sorted(workdir.glob("*_grch37.txt")):
            print(f"  - {p.name}")

        # Example 2: append to a single combined output file
        ldproxy_batch_mod.ldproxy_batch(
            snp=["rs123", "rs456"],
            pop=["CEU", "YRI"],
            r2d="d",
            append=True,
            genome_build="grch38_high_coverage",
            win_size=250000,
            token="fake-token",
        )
        print("[smoke] append=True file:")
        for p in sorted(workdir.glob("combined_query_snp_list_*.txt")):
            print(f"  - {p.name}")

        # Example 3: DataFrame input
        ldproxy_batch_mod.ldproxy_batch(
            snp=pd.DataFrame(["rs111", "rs222"]),
            append=False,
            token="fake-token",
        )
        print("[smoke] dataframe input files:")
        for p in sorted(workdir.glob("rs*_grch37.txt")):
            print(f"  - {p.name}")
    finally:
        os.chdir(old_cwd)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local no-network ldproxy_batch smoke examples.")
    parser.add_argument(
        "--outdir",
        type=Path,
        default=None,
        help="Optional output directory to keep generated files. If omitted, a temporary directory is used and removed.",
    )
    parser.add_argument(
        "--repo-tmp",
        action="store_true",
        help="Write files to <repo_root>/tmp/ldproxy_batch_outputs (useful for local inspection).",
    )
    args = parser.parse_args()

    # Monkeypatch endpoint dependency so this runs without token/network.
    ldproxy_batch_mod.ldproxy = _fake_ldproxy  # type: ignore[assignment]

    if args.repo_tmp and args.outdir is not None:
        raise SystemExit("Use only one of --outdir or --repo-tmp.")

    if args.repo_tmp:
        repo_root = Path(__file__).resolve().parents[1]
        workdir = (repo_root / "tmp" / "ldproxy_batch_outputs").resolve()
        workdir.mkdir(parents=True, exist_ok=True)
        print(f"[smoke] repo tmp mode, files will remain in: {workdir}")
        _run_examples(workdir)
        print(f"[smoke] done. inspect files in: {workdir}")
        return

    if args.outdir is not None:
        workdir = args.outdir.resolve()
        workdir.mkdir(parents=True, exist_ok=True)
        print(f"[smoke] persistent mode, files will remain in: {workdir}")
        _run_examples(workdir)
        print(f"[smoke] done. inspect files in: {workdir}")
        return

    with TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        print(f"[smoke] ephemeral mode, using temp dir: {workdir}")
        _run_examples(workdir)
        print("[smoke] done. temp directory has now been removed.")


if __name__ == "__main__":
    main()
