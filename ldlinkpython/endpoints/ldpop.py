# ldlinkpython/endpoints/ldpop.py

from __future__ import annotations

import re
from io import StringIO
from pathlib import Path
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

_AVAIL_LD = {"r2", "d"}
_AVAIL_GENOME_BUILD = {"grch37", "grch38", "grch38_high_coverage"}

_RSID_RE = re.compile(r"^rs\d+$", flags=re.IGNORECASE)
_CHR_COORD_RE = re.compile(r"^chr(\d{1,2}|x|y):(\d{1,9})$", flags=re.IGNORECASE)



def _to_list(value: str | Sequence[str]) -> list[str]:
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


def _normalize_variant(var: str, *, label: str) -> str:
    if isinstance(var, (list, tuple, set)):
        raise ValidationError(f"Input one SNP for {label} only.")

    val = str(var).strip()
    if not (_RSID_RE.match(val) or _CHR_COORD_RE.match(val)):
        raise ValidationError(f"Invalid query SNP format for {label}: {val}.")
    return val


def _normalize_pop(pop: str | Sequence[str]) -> str:
    vals = [str(p).strip() for p in _to_list(pop) if str(p).strip()]
    if not vals:
        raise ValidationError("Not a valid population code.")

    vals = [v.upper() for v in vals]
    if not all(v in _AVAIL_POP for v in vals):
        raise ValidationError("Not a valid population code.")

    return "+".join(vals)


def _normalize_r2d(r2d: str) -> str:
    v = str(r2d).strip().lower()
    if v not in _AVAIL_LD:
        raise ValidationError("Not a valid r2d. Enter 'r2' or 'd'.")
    return v


def _normalize_genome_build(genome_build: str) -> str:
    v = str(genome_build).strip().lower()
    if v not in _AVAIL_GENOME_BUILD:
        raise ValidationError("Not an available genome build.")
    return v


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out = out.rename(columns={"D.": "D'"})

    renamed: list[str] = []
    chr_pos_re = re.compile(r"^(chr(?:\d{1,2}|X|Y))\.(\d+)$", flags=re.IGNORECASE)
    for col in out.columns.astype(str):
        m = chr_pos_re.match(col)
        name = f"{m.group(1)}:{m.group(2)}" if m else col
        name = re.sub(r"\.+", "_", name)
        renamed.append(name)

    out.columns = renamed
    return out


def ldpop(
    var1: str,
    var2: str,
    pop: str | Sequence[str] = "CEU",
    r2d: str = "r2",
    token: str | None = None,
    file: str | bool = False,
    genome_build: str = "grch37",
    api_root: str = DEFAULT_API_ROOT,
) -> pd.DataFrame:
    """Query LDpop from the NIH LDlink REST API."""
    var1_norm = _normalize_variant(var1, label="Variant 1")
    var2_norm = _normalize_variant(var2, label="Variant 2")
    pop_norm = _normalize_pop(pop)
    r2d_norm = _normalize_r2d(r2d)
    genome_build_norm = _normalize_genome_build(genome_build)
    token_value = ensure_token(token)

    params = {
        "var1": var1_norm,
        "var2": var2_norm,
        "pop": pop_norm,
        "r2_d": r2d_norm,
        "genome_build": genome_build_norm,
        "token": token_value,
    }

    payload = http_request(
        endpoint="ldpop",
        api_root=api_root,
        token=token_value,
        method="GET",
        params=params,
        timeout=120.0,
    )

    if not isinstance(payload, str):
        payload = str(payload)

    data_out = pd.read_csv(
        StringIO(payload),
        sep="\t",
        dtype="string",
        keep_default_na=False,
        na_values=[],
    )

    if not data_out.empty:
        first_col = data_out.iloc[:, 0].astype(str)
        errors = first_col[first_col.str.contains("error", case=False, na=False)].tolist()
        if errors:
            raise RuntimeError(" ".join(errors))

    data_out = _normalize_columns(data_out)

    if isinstance(file, str) and file.strip() and file.strip().upper() != "FALSE":
        out_path = Path(file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        data_out.to_csv(out_path, sep="\t", index=False)

    return data_out
