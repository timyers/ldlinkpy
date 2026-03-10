# ldlinkpython/endpoints/snpclip.py

from __future__ import annotations

import re
from io import StringIO
from typing import Sequence

import pandas as pd

from ldlinkpython import DEFAULT_API_ROOT
from ldlinkpython.exceptions import ValidationError
from ldlinkpython.http import request as http_request
from ldlinkpython.validators import ensure_token

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

_AVAIL_GENOME_BUILD = {"grch37", "grch38", "grch38_high_coverage"}

_RSID_RE = re.compile(r"^rs\d+$", flags=re.IGNORECASE)
_CHR_COORD_RE = re.compile(r"^chr(\d{1,2}|x|y):(\d{1,9})$", flags=re.IGNORECASE)


def _to_list(value: str | Sequence[str]) -> list[str]:
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


def _normalize_snps(snps: str | Sequence[str]) -> list[str]:
    vals = [str(s).strip() for s in _to_list(snps) if str(s).strip()]
    if not (1 <= len(vals) <= 5000):
        raise ValidationError("Input is between 1 to 5000 variants.")

    for v in vals:
        if not (_RSID_RE.match(v) or _CHR_COORD_RE.match(v)):
            raise ValidationError(f"Invalid query format for variant: {v}.")

    return vals


def _normalize_pop(pop: str | Sequence[str]) -> str:
    vals = [str(p).strip() for p in _to_list(pop) if str(p).strip()]
    if not vals:
        raise ValidationError("Not a valid population code.")

    vals = [v.upper() for v in vals]
    if not all(v in _AVAIL_POP for v in vals):
        raise ValidationError("Not a valid population code.")
    return "+".join(vals)


def _normalize_threshold(name: str, value: float | int | str) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"{name} must be between 0 and 1: {value}.") from e

    if not (0 <= v <= 1):
        raise ValidationError(f"{name} must be between 0 and 1: {value}.")

    return str(v)


def _normalize_genome_build(genome_build: str) -> str:
    v = str(genome_build).strip().lower()
    if v not in _AVAIL_GENOME_BUILD:
        raise ValidationError("Not an available genome build.")
    return v


def _normalize_return_type(return_type: str) -> str:
    v = str(return_type).strip().lower()
    if v not in {"dataframe", "raw"}:
        raise ValidationError("return_type must be 'dataframe' or 'raw'.")
    return v


def snpclip(
    snps: str | Sequence[str],
    pop: str | Sequence[str] = "CEU",
    r2_threshold: float | int | str = 0.1,
    maf_threshold: float | int | str = 0.01,
    genome_build: str = "grch37",
    token: str | None = None,
    file: str | bool = False,
    api_root: str = DEFAULT_API_ROOT,
    return_type: str = "dataframe",
):
    """Call LDlink SNPclip endpoint and return a DataFrame (or raw response)."""
    snp_list = _normalize_snps(snps)
    pop_norm = _normalize_pop(pop)
    r2_norm = _normalize_threshold("R2 threshold", r2_threshold)
    maf_norm = _normalize_threshold("MAF threshold", maf_threshold)
    genome_build_norm = _normalize_genome_build(genome_build)
    return_type_norm = _normalize_return_type(return_type)
    token_value = ensure_token(token)

    if not (file is False or isinstance(file, str)):
        raise ValidationError("Invalid input for file option.")

    body = {
        "snps": snp_list,
        "pop": pop_norm,
        "r2_threshold": r2_norm,
        "maf_threshold": maf_norm,
        "genome_build": genome_build_norm,
    }

    data = http_request(
        endpoint="snpclip",
        api_root=api_root,
        token=token_value,
        method="POST",
        json_body=body,
        timeout=120.0,
    )

    if return_type_norm == "raw":
        return data

    if not isinstance(data, str):
        data = str(data)

    data_out = pd.read_csv(
        StringIO(data),
        sep="\t",
        dtype="string",
        keep_default_na=False,
        na_values=[],
    )

    data_out.columns = [re.sub(r"(\.)+", "_", str(c)) for c in data_out.columns]

    if not data_out.empty:
        last_first_col = str(data_out.iloc[-1, 0])
        if "error" in last_first_col.lower() or "warning" in last_first_col.lower():
            raise RuntimeError(last_first_col)

    if file is not False and isinstance(file, str):
        data_out.to_csv(file, sep="\t", index=False)

    return data_out
