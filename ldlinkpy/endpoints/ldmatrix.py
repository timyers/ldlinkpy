from __future__ import annotations

from typing import Any, Sequence, Union, Optional

import pandas as pd

from ldlinkpy import DEFAULT_API_ROOT
from ldlinkpy.http import request as http_request
from ldlinkpy.parsing import parse_matrix
from ldlinkpy.validators import normalize_snps, validate_genome_build, validate_r2d


def ldmatrix(
    snps: Union[str, Sequence[str]],
    pop: str = "CEU",
    r2d: str = "r2",
    genome_build: str = "grch37",
    token: Optional[str] = None,
    api_root: str = DEFAULT_API_ROOT,
    return_type: str = "dataframe",
    request_method: str = "auto",
) -> Union[pd.DataFrame, Any]:
    """
    Call the LDlink 'ldmatrix' endpoint.

    Parameters
    ----------
    snps:
        SNP identifiers. String or sequence of strings. If string, common separators
        (whitespace, comma, newline) are supported.
    pop:
        1000G population code (e.g., "CEU").
    r2d:
        "r2" or "d" (LD measure).
    genome_build:
        "grch37" or "grch38".
    token:
        LDlink API token. If None, reads environment variable LDLINK_TOKEN.
    api_root:
        Base LDlink REST API root.
    return_type:
        "dataframe" to parse with parse_matrix; otherwise returns the raw response.
    request_method:
        "auto" (GET if len(snps)<=300 else POST), or "get", or "post".

    Returns
    -------
    pandas.DataFrame or raw response
    """
    snp_list = normalize_snps(snps)

    pop = str(pop).strip()
    if not pop:
        raise ValueError("pop is required.")

    r2d_norm = validate_r2d(r2d)
    genome_build_norm = validate_genome_build(genome_build)

    return_type_norm = str(return_type).strip().lower()
    if return_type_norm not in {"dataframe", "raw"}:
        raise ValueError("return_type must be 'dataframe' or 'raw'.")

    req_method = str(request_method).strip().lower()
    if req_method not in {"auto", "get", "post"}:
        raise ValueError("request_method must be 'auto', 'get', or 'post'.")

    if req_method == "auto":
        req_method = "get" if len(snp_list) <= 300 else "post"

    headers = {"Accept": "application/json"}

    if req_method == "get":
        params = {
            "snps": "\n".join(snp_list),
            "pop": pop,
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
            "snps": snp_list,
            "pop": pop,
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
        return data

    if not isinstance(data, str):
        data = str(data)

    try:
        df = parse_matrix(data)
    except Exception as e:
        raise RuntimeError(f"Failed to parse ldmatrix response with parse_matrix: {e}") from e

    if not isinstance(df, pd.DataFrame):
        raise RuntimeError("parse_matrix did not return a pandas.DataFrame as expected.")
    return df