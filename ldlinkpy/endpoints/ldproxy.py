from __future__ import annotations

from io import StringIO
from typing import Iterable, Union, overload

import pandas as pd

from ldlinkpy import DEFAULT_API_ROOT
from ldlinkpy.client import LDlinkClient


_VALID_GENOME_BUILDS = {"grch37", "grch38"}
_VALID_R2D = {"r2", "d"}


def _normalize_pop(pop: Union[str, Iterable[str]]) -> str:
    if isinstance(pop, str):
        pop_str = pop.strip()
        if not pop_str:
            raise ValueError("pop must be a non-empty string or a non-empty list of strings.")
        return pop_str
    pops = [str(p).strip() for p in pop]
    pops = [p for p in pops if p]
    if not pops:
        raise ValueError("pop must be a non-empty string or a non-empty list of strings.")
    return "+".join(pops)


@overload
def ldproxy(
    snp: str,
    pop: Union[str, list[str]] = "CEU",
    r2d: str = "r2",
    win_size: int = 500000,
    genome_build: str = "grch37",
    token: str | None = None,
    api_root: str = DEFAULT_API_ROOT,
    return_type: str = "dataframe",
) -> pd.DataFrame: ...


@overload
def ldproxy(
    snp: str,
    pop: Union[str, list[str]] = "CEU",
    r2d: str = "r2",
    win_size: int = 500000,
    genome_build: str = "grch37",
    token: str | None = None,
    api_root: str = DEFAULT_API_ROOT,
    return_type: str = "raw",
) -> str: ...


def ldproxy(
    snp: str,
    pop: Union[str, list[str]] = "CEU",
    r2d: str = "r2",
    win_size: int = 500000,
    genome_build: str = "grch37",
    token: str | None = None,
    api_root: str = DEFAULT_API_ROOT,
    return_type: str = "dataframe",
):
    """
    Query LDproxy from the NIH LDlink REST API.

    Parameters
    ----------
    snp:
        Query variant (e.g., rsID).
    pop:
        Population code(s). If a list is provided, it will be joined with '+'.
    r2d:
        'r2' or 'd' (maps to LDlink parameter r2_d).
    win_size:
        Window size in base pairs.
    genome_build:
        'grch37' or 'grch38'.
    token:
        LDlink API token (or use env var LDLINK_TOKEN).
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

    gb = str(genome_build).strip().lower()
    if gb not in _VALID_GENOME_BUILDS:
        raise ValueError(f"genome_build must be one of {sorted(_VALID_GENOME_BUILDS)} (got: {genome_build!r}).")

    r2d_norm = str(r2d).strip().lower()
    if r2d_norm not in _VALID_R2D:
        raise ValueError(f"r2d must be one of {sorted(_VALID_R2D)} (got: {r2d!r}).")

    if not isinstance(win_size, int) or win_size <= 0:
        raise ValueError("win_size must be a positive integer.")

    pop_joined = _normalize_pop(pop)

    client = LDlinkClient(token=token, api_root=api_root)
    text = client.get(
        endpoint="ldproxy",
        params={
            "var": snp.strip(),
            "pop": pop_joined,
            "r2_d": r2d_norm,
            "window": win_size,
            "genome_build": gb,
        },
    )

    rt = str(return_type).strip().lower()
    if rt == "dataframe":
        return pd.read_csv(StringIO(text), sep="\t", dtype=str)
    if rt == "raw":
        return text

    raise ValueError("return_type must be 'dataframe' or 'raw'.")
