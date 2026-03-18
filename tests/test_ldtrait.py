from __future__ import annotations

from typing import Any, Mapping, Sequence

import pandas as pd

from ldlinkpy import DEFAULT_API_ROOT
from ldlinkpy.http import request
from ldlinkpy.validators import (
    normalize_snps,
    validate_genome_build,
    validate_r2d,
    validate_threshold,
)


def _pick_records_field(obj: Mapping[str, Any]) -> Any:
    """
    Try common field names that might contain a list of JSON records.
    """
    for key in (
        "records",
        "Record",
        "data",
        "Data",
        "results",
        "Results",
        "result",
        "Result",
        "ldtrait",
        "LDtrait",
        "LDTRAIT",
        "associations",
        "Associations",
        "variants",
        "Variants",
    ):
        if key in obj:
            return obj[key]
    return None


def _json_to_dataframe(payload: Any) -> pd.DataFrame:
    """
    Coerce LDtrait JSON into a DataFrame when it is list-like or contains a clear records field.
    """
    if isinstance(payload, pd.DataFrame):
        return payload

    if isinstance(payload, list):
        if len(payload) == 0:
            return pd.DataFrame()
        if all(isinstance(x, Mapping) for x in payload):
            return pd.DataFrame(payload)
        raise RuntimeError(
            "LDtrait JSON response is a list but not a list of objects; cannot coerce to DataFrame."
        )

    if isinstance(payload, Mapping):
        # Sometimes API returns an embedded TSV string even when JSON-parsed
        for key in ("output", "Output", "text", "Text", "tsv", "TSV"):
            if key in payload and isinstance(payload[key], str):
                try:
                    from ldlinkpy.parsing import parse_tsv

                    return parse_tsv(payload[key])
                except Exception as e:  # pragma: no cover
                    raise RuntimeError(
                        "LDtrait response contained a text field but it could not be parsed as TSV."
                    ) from e

        records = _pick_records_field(payload)
        if records is not None:
            if isinstance(records, list) and all(isinstance(x, Mapping) for x in records):
                return pd.DataFrame(records)
            if isinstance(records, list) and len(records) == 0:
                return pd.DataFrame()
            if isinstance(records, Mapping):
                return pd.DataFrame(records)

        for err_key in ("error", "Error", "message", "Message", "detail", "Detail"):
            if err_key in payload:
                raise RuntimeError(
                    f"LDtrait returned JSON that does not contain records. "
                    f"Found '{err_key}': {payload[err_key]!r}"
                )

        raise RuntimeError(
            "LDtrait returned JSON but it does not look like a list of records and no clear records field "
            "was found, so it cannot be coerced to a DataFrame. Use return_type='raw' to inspect the payload."
        )

    raise RuntimeError(
        f"LDtrait returned unsupported JSON type {type(payload).__name__}; cannot coerce to DataFrame."
    )


def ldtrait(
    snps: str | Sequence[str],
    pop: str = "CEU",
    r2d: str = "r2",
    r2d_threshold: float = 0.1,
    win_size: int = 500000,
    genome_build: str = "grch37",
    token: str | None = None,
    api_root: str = DEFAULT_API_ROOT,
    return_type: str = "dataframe",
    request_method: str = "auto",
) -> pd.DataFrame | Any:
    """
    Query LDtrait from the LDlink REST API.
    """
    if return_type not in {"dataframe", "raw"}:
        raise ValueError("return_type must be 'dataframe' or 'raw'.")

    request_method_norm = str(request_method).strip().lower()
    if request_method_norm not in {"auto", "post", "get"}:
        raise ValueError("request_method must be 'auto', 'post', or 'get'.")

    snp_list = normalize_snps(snps)
    validate_r2d(r2d)

    # validators.validate_threshold expects (name, value)
    validate_threshold("r2d_threshold", r2d_threshold)

    validate_genome_build(genome_build)

    if not isinstance(win_size, int) or win_size <= 0:
        raise ValueError("win_size must be a positive integer.")

    params: dict[str, Any] = {
        "snps": ",".join(snp_list),
        "pop": pop,
        "r2_d": r2d,
        "r2_d_threshold": r2d_threshold,
        "window": win_size,
        "genome_build": genome_build,
    }

    method = "POST" if request_method_norm in {"auto", "post"} else "GET"

    payload = request(
        endpoint="ldtrait",
        params=params,
        token=token,
        api_root=api_root,
        method=method,
        request_method=request_method_norm,
    )

    if return_type == "raw":
        return payload

    if isinstance(payload, str):
        from ldlinkpy.parsing import parse_tsv

        try:
            return parse_tsv(payload)
        except Exception as e:
            raise RuntimeError(
                "LDtrait returned text that could not be parsed as TSV. "
                "Use return_type='raw' to inspect the response."
            ) from e

    return _json_to_dataframe(payload)
    