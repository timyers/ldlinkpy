from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from ldlinkpy import DEFAULT_API_ROOT
from ldlinkpy.endpoints.ldproxy import ldproxy

_VALID_GENOME_BUILDS = {"grch37", "grch38", "grch38_high_coverage"}


def _normalize_snps(snp: str | Iterable[str] | pd.DataFrame) -> list[str]:
    if isinstance(snp, pd.DataFrame):
        values = snp.astype(str).stack().tolist()
        out = [v.strip() for v in values if isinstance(v, str) and v.strip()]
        if not out:
            raise ValueError("snp DataFrame must contain at least one non-empty SNP value.")
        return out

    if isinstance(snp, str):
        parts = [line.strip() for line in snp.replace(",", "\n").splitlines()]
        out = [p for p in parts if p]
        if not out:
            raise ValueError("snp must include at least one non-empty SNP value.")
        return out

    out = [str(v).strip() for v in snp]
    out = [v for v in out if v]
    if not out:
        raise ValueError("snp must include at least one non-empty SNP value.")
    return out


def ldproxy_batch(
    snp: str | Iterable[str] | pd.DataFrame,
    pop: str | list[str] = "CEU",
    r2d: str = "r2",
    token: str | None = None,
    append: bool = False,
    genome_build: str = "grch37",
    win_size: int = 500000,
    api_root: str = DEFAULT_API_ROOT,
) -> list[str]:
    """
    Submit multiple LDproxy requests and write results to local text file(s).

    Parameters follow LDlinkR::LDproxy_batch semantics.

    Returns
    -------
    list[str]
        Paths to file(s) written.
    """
    if not isinstance(append, bool):
        raise ValueError("append must be a boolean.")

    gb = str(genome_build).strip().lower()
    if gb not in _VALID_GENOME_BUILDS:
        raise ValueError(
            f"genome_build must be one of {sorted(_VALID_GENOME_BUILDS)} (got: {genome_build!r})."
        )

    if not isinstance(win_size, int) or win_size <= 0 or win_size > 1_000_000:
        raise ValueError("win_size must be an integer greater than 0 and less than or equal to 1,000,000.")

    snps = _normalize_snps(snp)
    written_files: list[str] = []

    if append:
        out_file = Path.cwd() / f"combined_query_snp_list_{gb}.txt"
        for query_snp in snps:
            df_proxy = ldproxy(
                snp=query_snp,
                pop=pop,
                r2d=r2d,
                win_size=win_size,
                genome_build=gb,
                token=token,
                api_root=api_root,
                return_type="dataframe",
            )
            if not isinstance(df_proxy, pd.DataFrame) or df_proxy.empty:
                continue

            first_cell = str(df_proxy.iloc[0, 0]).lower() if df_proxy.shape[0] and df_proxy.shape[1] else ""
            if "error" in first_cell:
                continue

            df_to_write = df_proxy.copy()
            df_to_write.insert(0, "query_snp", query_snp)
            df_to_write.to_csv(
                out_file,
                sep="\t",
                index=True,
                mode="a",
                header=not out_file.exists(),
            )

        if out_file.exists():
            written_files.append(str(out_file))

        return written_files

    for query_snp in snps:
        out_file = Path.cwd() / f"{query_snp}_{gb}.txt"
        df_proxy = ldproxy(
            snp=query_snp,
            pop=pop,
            r2d=r2d,
            win_size=win_size,
            genome_build=gb,
            token=token,
            api_root=api_root,
            return_type="dataframe",
        )
        if not isinstance(df_proxy, pd.DataFrame) or df_proxy.empty:
            continue

        first_cell = str(df_proxy.iloc[0, 0]).lower() if df_proxy.shape[0] and df_proxy.shape[1] else ""
        if "error" in first_cell:
            continue

        df_proxy.to_csv(out_file, sep="\t", index=True)
        written_files.append(str(out_file))

    return written_files
