from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional, Sequence, Union

import pandas as pd

from ldlinkpy import DEFAULT_API_ROOT
from ldlinkpy.http import request as http_request
from ldlinkpy.parsing import parse_matrix
from ldlinkpy.validators import (
    ValidationError,
    normalize_snps,
    validate_genome_build,
    validate_r2d,
)

_VALID_POPS = {
    "YRI", "LWK", "GWD", "MSL", "ESN", "ASW", "ACB",
    "MXL", "PUR", "CLM", "PEL", "CHB", "JPT", "CHS",
    "CDX", "KHV", "CEU", "TSI", "FIN", "GBR", "IBS",
    "GIH", "PJL", "BEB", "STU", "ITU",
    "ALL", "AFR", "AMR", "EAS", "EUR", "SAS",
}
_RSID_RE = re.compile(r"^rs\d+$", re.IGNORECASE)
_CHR_COORD_RE = re.compile(r"^chr(\d{1,2}|X|Y):(\d{1,9})$", re.IGNORECASE)


def _validate_ldmatrix_snps(snps: list[str]) -> list[str]:
    if len(snps) < 2 or len(snps) > 2500:
        raise ValidationError("snps must include between 2 and 2500 variants.")
    for snp in snps:
        if not (_RSID_RE.match(snp) or _CHR_COORD_RE.match(snp)):
            raise ValidationError(
                f"Invalid variant format '{snp}'. Use an rsID (e.g. rs123) or chromosome coordinate (e.g. chr7:24966446)."
            )
    return snps


def _normalize_pop(pop: Union[str, Sequence[str]]) -> str:
    if isinstance(pop, str):
        tokens = [p for p in re.split(r"[\s,+]+", pop.strip().upper()) if p]
    elif isinstance(pop, Sequence):
        tokens = [str(p).strip().upper() for p in pop if str(p).strip()]
    else:
        raise ValidationError("pop must be a population code string or sequence of population code strings.")
    if not tokens:
        raise ValidationError("pop is required.")
    if not all(p in _VALID_POPS for p in tokens):
        raise ValidationError("Not a valid population code.")
    return "+".join(tokens)


def ldmatrix(
    snps: Union[str, Sequence[str]],
    pop: Union[str, Sequence[str]] = "CEU",
    r2d: str = "r2",
    genome_build: str = "grch37",
    token: Optional[str] = None,
    api_root: str = DEFAULT_API_ROOT,
    return_type: str = "dataframe",
    request_method: str = "auto",
    file: Union[str, bool] = False,
) -> Union[pd.DataFrame, Any]:
    """
    Call the LDlink 'ldmatrix' endpoint.

    Parameters
    ----------
    snps:
        List of between 2 and 2500 variant identifiers. Variants must be rsIDs
        or chromosome coordinates (e.g., "chr7:24966446").
    pop:
        One or more 1000G population codes (e.g., "CEU", "YRI"). Multiple values supported.
    r2d:
        "r2" or "d" (LD measure).
    genome_build:
        "grch37", "grch38", or "grch38_high_coverage".
    token:
        LDlink API token. If None, reads environment variable LDLINK_TOKEN.
    api_root:
        Base LDlink REST API root.
    return_type:
        "dataframe" to parse with parse_matrix; otherwise returns the raw response.
    request_method:
        "auto" (GET if len(snps)<=300 else POST), or "get", or "post".
    file:
        Optional output path. If False (default), does not write a file.

    Returns
    -------
    pandas.DataFrame or raw response
    """
    snp_list = _validate_ldmatrix_snps(normalize_snps(snps))

    pop_norm = _normalize_pop(pop)

    r2d_norm = validate_r2d(r2d)
    genome_build_norm = validate_genome_build(genome_build)
    if file is not False:
        if not isinstance(file, str) or not file.strip():
            raise ValidationError("file must be False or a non-empty string path.")

    return_type_norm = str(return_type).strip().lower()
    if return_type_norm not in {"dataframe", "raw"}:
        raise ValidationError("return_type must be 'dataframe' or 'raw'.")

    req_method = str(request_method).strip().lower()
    if req_method not in {"auto", "get", "post"}:
        raise ValidationError("request_method must be 'auto', 'get', or 'post'.")

    if req_method == "auto":
        req_method = "get" if len(snp_list) <= 300 else "post"

    headers = {"Accept": "application/json"}

    if req_method == "get":
        params = {
            "snps": "\n".join(snp_list),
            "pop": pop_norm,
            "r2_d": r2d_norm,
            "genome_build": genome_build_norm,
        }
        data = http_request(
            "ldmatrix",
            api_root=api_root,
            token=token,
            method="GET",
            params=params,
            headers=headers,
            timeout=120.0,
        )
    else:
        body = {
            # LDlink expects newline-delimited SNPs for ldmatrix POST payloads.
            # Sending a JSON array can trigger 500 responses from the API.
            "snps": "\n".join(snp_list),
            "pop": pop_norm,
            "r2_d": r2d_norm,
            "genome_build": genome_build_norm,
        }
        data = http_request(
            "ldmatrix",
            api_root=api_root,
            token=token,
            method="POST",
            json_body=body,
            headers=headers,
            timeout=120.0,
        )

    if return_type_norm == "raw":
        if isinstance(file, str):
            file_path = Path(file)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(str(data), encoding="utf-8")
        return data

    if not isinstance(data, str):
        data = str(data)

    try:
        df = parse_matrix(data)
    except Exception as e:
        raise RuntimeError(f"Failed to parse ldmatrix response with parse_matrix: {e}") from e

    if not isinstance(df, pd.DataFrame):
        raise RuntimeError("parse_matrix did not return a pandas.DataFrame as expected.")
    if isinstance(file, str):
        file_path = Path(file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(file_path, sep="\t", index=True)
    return df
