"""Simple local smoke tests for ldproxy_batch.

Run from repo root:
    PYTHONPATH=. python examples/ldproxy_batch_smoke_test.py
"""

from __future__ import annotations

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


def main() -> None:
    # Monkeypatch endpoint dependency so this runs without token/network.
    ldproxy_batch_mod.ldproxy = _fake_ldproxy  # type: ignore[assignment]

    with TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        print(f"[smoke] using temp dir: {workdir}")
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


if __name__ == "__main__":
    main()
