from __future__ import annotations

import re
from io import StringIO
from typing import Iterable, Union, overload

import pandas as pd

from ldlinkpy import DEFAULT_API_ROOT
from ldlinkpy.client import LDlinkClient


_VALID_GENOME_BUILDS = {"grch37", "grch38", "grch38_high_coverage"}
_VALID_R2D = {"r2", "d"}
_AVAIL_POP: set[str] = {
    "YRI",
    "LWK",
    "GWD",
    "MSL",
    "ESN",
    "ASW",
    "ACB",
    "MXL",
    "PUR",
    "CLM",
    "PEL",
    "CHB",
    "JPT",
    "CHS",
    "CDX",
    "KHV",
    "CEU",
    "TSI",
    "FIN",
    "GBR",
    "IBS",
    "GIH",
    "PJL",
    "BEB",
    "STU",
    "ITU",
    "ALL",
    "AFR",
    "AMR",
    "EAS",
    "EUR",
    "SAS",
}

_RSID_RE = re.compile(r"^rs\\d+$", flags=re.IGNORECASE)
_CHR_COORD_RE = re.compile(r"^chr(\\d{1,2}|x|y):(\\d{1,9})$", flags=re.IGNORECASE)


def _normalize_pop(pop: Union[str, Iterable[str]]) -> str:
    if isinstance(pop, str):
        pop_vals = [pop]
    else:
        pop_vals = [str(p) for p in pop]

    pops = [p.strip().upper() for p in pop_vals if str(p).strip()]
    if not pops:
        raise ValueError("pop must be a non-empty string or a non-empty list of strings.")

    if not all(p in _AVAIL_POP for p in pops):
        raise ValueError("Not a valid population code.")

    return "+".join(pops)


def _validate_snp(snp: str) -> str:
    snp_norm = snp.strip()
    if not (_RSID_RE.match(snp_norm) or _CHR_COORD_RE.match(snp_norm)):
        raise ValueError(f"Invalid query format for variant: {snp_norm}.")
    return snp_norm


@overload
def ldproxy(
    snp: str,
    pop: Union[str, list[str]] = "CEU",
    r2d: str = "r2",
    token: str | None = None,
    file: str | bool = False,
    genome_build: str = "grch37",
    win_size: int = 500000,
    api_root: str = DEFAULT_API_ROOT,
    return_type: str = "dataframe",
) -> pd.DataFrame: ...


@overload
def ldproxy(
    snp: str,
    pop: Union[str, list[str]] = "CEU",
    r2d: str = "r2",
    token: str | None = None,
    file: str | bool = False,
    genome_build: str = "grch37",
    win_size: int = 500000,
    api_root: str = DEFAULT_API_ROOT,
    return_type: str = "raw",
) -> str: ...


def ldproxy(
    snp: str,
    pop: Union[str, list[str]] = "CEU",
    r2d: str = "r2",
    token: str | None = None,
    file: str | bool = False,
    genome_build: str = "grch37",
    win_size: int = 500000,
    api_root: str = DEFAULT_API_ROOT,
    return_type: str = "dataframe",
):
    """
    Query LDproxy from the NIH LDlink REST API.

    Parameters
    ----------
    snp:
        Query variant (rsID or GRCh37 coordinate like "chr7:24966446").
    pop:
        One or more 1000G population codes; default "CEU".
    r2d:
        'r2' or 'd' (maps to LDlink parameter r2_d).
    token:
        LDlink API token (or use env var LDLINK_TOKEN).
    file:
        Optional output file path. If False, no file is written.
    genome_build:
        'grch37', 'grch38', or 'grch38_high_coverage'.
    win_size:
        Window size in base pairs; must be >0 and <=1,000,000.
    api_root:
        Base URL for LDlink REST API.
    return_type:
        'dataframe' (default) to return a pandas DataFrame parsed from TSV, or 'raw' for raw text.

    Returns
    -------
    pandas.DataFrame or str
    """
    if not isinstance(snp, str) or not snp.strip():
        raise ValueError("snp must be a non-empty string.")
    snp_norm = _validate_snp(snp)

    gb = str(genome_build).strip().lower()
    if gb not in _VALID_GENOME_BUILDS:
        raise ValueError(f"genome_build must be one of {sorted(_VALID_GENOME_BUILDS)} (got: {genome_build!r}).")

    r2d_norm = str(r2d).strip().lower()
    if r2d_norm not in _VALID_R2D:
        raise ValueError(f"r2d must be one of {sorted(_VALID_R2D)} (got: {r2d!r}).")

    if not isinstance(win_size, int) or win_size <= 0 or win_size > 1_000_000:
        raise ValueError("win_size must be an integer greater than 0 and less than or equal to 1,000,000.")

    if not (file is False or isinstance(file, str)):
        raise ValueError("Invalid input for file option.")

    pop_joined = _normalize_pop(pop)

    client = LDlinkClient(token=token, api_root=api_root)
    text = client.get(
        endpoint="ldproxy",
        params={
            "var": snp_norm,
            "pop": pop_joined,
            "r2_d": r2d_norm,
            "window": win_size,
            "genome_build": gb,
        },
    )

    rt = str(return_type).strip().lower()
    if rt == "raw":
        if file is not False and isinstance(file, str):
            with open(file, "w", encoding="utf-8") as f:
                f.write(text)
        return text

    if rt == "dataframe":
        df = pd.read_csv(StringIO(text), sep="\t", dtype=str)
        if file is not False and isinstance(file, str):
            df.to_csv(file, sep="\t", index=False)
        return df

    raise ValueError("return_type must be 'dataframe' or 'raw'.")
