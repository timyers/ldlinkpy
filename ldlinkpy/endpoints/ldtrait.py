from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from ldlinkpy import DEFAULT_API_ROOT
from ldlinkpy.http import request
from ldlinkpy.validators import (
    ensure_token,
    normalize_snps,
    validate_genome_build,
    validate_r2d,
    validate_threshold,
)
_VALID_POP_CODES: set[str] = {
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

_RSID_RE = re.compile(r"^rs\d{1,}$", flags=re.IGNORECASE)
_CHR_COORD_RE = re.compile(r"^chr(\d{1,2}|x|y):(\d{1,9})$", flags=re.IGNORECASE)


def _normalize_pop(pop: str | Sequence[str]) -> str:
    if isinstance(pop, str):
        raw_items = [pop]
    elif isinstance(pop, Sequence):
        raw_items = [str(p) for p in pop]
    else:
        raise ValueError("pop must be a population code string or a sequence of population code strings.")

    pops = [p.strip().upper() for p in raw_items if str(p).strip()]
    if not pops:
        raise ValueError("pop must contain at least one population code.")
    if any(p not in _VALID_POP_CODES for p in pops):
        raise ValueError("Not a valid population code.")
    return "+".join(pops)


def _validate_snps_for_ldtrait(snps: list[str]) -> list[str]:
    if len(snps) < 1 or len(snps) > 50:
        raise ValueError("Input is between 1 to 50 variants.")

    for snp in snps:
        if not (_RSID_RE.match(snp) or _CHR_COORD_RE.match(snp)):
            raise ValueError(f"Invalid query format for variant: {snp}.")
    return snps


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

    # Most common: list of dict records
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
            # Some responses might have a dict-of-columns shape
            if isinstance(records, Mapping):
                return pd.DataFrame(records)

        # If it looks like an error, surface something helpful
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
    pop: str | Sequence[str] = "CEU",
    r2d: str = "r2",
    r2d_threshold: float = 0.1,
    win_size: int = 500000,
    genome_build: str = "grch37",
    token: str | None = None,
    file: str | bool = False,
    api_root: str = DEFAULT_API_ROOT,
    return_type: str = "dataframe",
    on_no_hits: str = "empty",
    request_method: str = "auto",
    timeout: float = 600.0,
) -> pd.DataFrame | Any:
    """
    Query LDtrait from the LDlink REST API.

    Parameters
    ----------
    snps
        Between 1 and 50 variants, each an rsID or coordinate like "chr7:24966446".
    pop
        One or more 1000G population codes (e.g., "CEU", "EUR", "AFR").
    r2d
        "r2" or "d".
    r2d_threshold
        Threshold for r2/d.
    win_size
        Window size in base pairs.
    genome_build
        "grch37" or "grch38".
    token
        LDlink token. If None, reads LDLINK_TOKEN from environment.
    file
        Optional output file path. If False, no file is written.
    api_root
        Base API root URL.
    return_type
        "dataframe" (default) or "raw".
    on_no_hits
        Behavior when LDtrait reports no GWAS matches. "empty" returns an empty DataFrame;
        "raise" raises RuntimeError.
    request_method
        "auto" (default), "post", or "get". Prefer POST by default for robustness.

    Returns
    -------
    pandas.DataFrame or raw payload
        By default returns a DataFrame. If return_type="raw", returns the parsed JSON (dict/list)
        or raw text as provided by the API layer.
    """
    if return_type not in {"dataframe", "raw"}:
        raise ValueError("return_type must be 'dataframe' or 'raw'.")
    if on_no_hits not in {"empty", "raise"}:
        raise ValueError("on_no_hits must be 'empty' or 'raise'.")

    request_method_norm = str(request_method).strip().lower()
    if request_method_norm not in {"auto", "post", "get"}:
        raise ValueError("request_method must be 'auto', 'post', or 'get'.")

    if not (file is False or isinstance(file, str)):
        raise ValueError("Invalid input for file option.")

    snp_list = _validate_snps_for_ldtrait(normalize_snps(snps))
    pop_joined = _normalize_pop(pop)
    r2d_norm = validate_r2d(r2d)
    threshold = validate_threshold("r2d_threshold", r2d_threshold)
    gb = validate_genome_build(genome_build)

    if isinstance(win_size, bool) or not isinstance(win_size, int) or win_size < 0 or win_size > 1_000_000:
        raise ValueError("Window size must be between 0 and 1000000 bp.")

    token_value = ensure_token(token)

    params: dict[str, Any] = {
        "snps": "\n".join(snp_list),
        "pop": pop_joined,
        "r2_d": str(r2d_norm),
        "r2_d_threshold": str(threshold),
        "window": str(win_size),
        "genome_build": str(gb),
    }

    # Choose correct endpoint. Per LDlink docs:
    # - POST JSON endpoint: /ldtrait
    # - GET endpoint: /ldtraitget
    if request_method_norm == "get":
        method = "GET"
        endpoint = "ldtraitget"
    else:
        method = "POST"
        endpoint = "ldtrait"

    payload = request(
        endpoint=endpoint,
        params=params,
        token=token_value,
        api_root=api_root,
        method=method,
        timeout=timeout,
    )

    if return_type == "raw":
        if isinstance(payload, str) and file is not False and isinstance(file, str):
            Path(file).write_text(payload, encoding="utf-8")
        return payload

    # DataFrame coercion:
    if isinstance(payload, str):
        # Default: parse TSV
        from ldlinkpy.parsing import parse_tsv

        try:
            df = parse_tsv(payload)
            if file is not False and isinstance(file, str):
                df.to_csv(file, sep="\t", index=False)
            return df
        except Exception as e:
            raise RuntimeError(
                "LDtrait returned text that could not be parsed as TSV. "
                "Use return_type='raw' to inspect the response."
            ) from e

    # JSON (dict/list) auto-parsed by http layer
    if isinstance(payload, Mapping):
        no_hits_text = "No entries in the GWAS Catalog are identified using the LDtrait search criteria."
        for err_key in ("error", "Error", "message", "Message", "detail", "Detail"):
            msg = payload.get(err_key)
            if isinstance(msg, str) and no_hits_text in msg:
                if on_no_hits == "empty":
                    empty = pd.DataFrame()
                    if file is not False and isinstance(file, str):
                        empty.to_csv(file, sep="\t", index=False)
                    return empty
                break

    df = _json_to_dataframe(payload)
    if file is not False and isinstance(file, str):
        df.to_csv(file, sep="\t", index=False)
    return df
