from __future__ import annotations

import json as _json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union, cast

import pandas as pd

from .. import DEFAULT_API_ROOT
from ..http import request as http_request
from ..parsing import is_json_response, parse_tsv


SnpPair = Tuple[str, str]
SnpPairsLike = Sequence[Union[SnpPair, Sequence[str]]]

_RSID_RE = re.compile(r"^rs\d+$", flags=re.IGNORECASE)
_CHR_COORD_RE = re.compile(r"^chr(\d{1,2}|x|y):(\d{1,9})$", flags=re.IGNORECASE)
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


def _normalize_pair(a: str, b: str) -> SnpPair:
    if a is None or b is None:
        raise ValueError("Both var1 and var2 must be provided for a single SNP pair.")
    a = str(a).strip()
    b = str(b).strip()
    if not a or not b:
        raise ValueError("var1 and var2 must be non-empty strings.")
    return _normalize_variant(a, label="var1"), _normalize_variant(b, label="var2")


def _normalize_variant(var: str, *, label: str) -> str:
    val = str(var).strip()
    if not (_RSID_RE.match(val) or _CHR_COORD_RE.match(val)):
        raise ValueError(
            f"{label} must be an rsID (e.g. rs123) or GRCh37 coordinate (e.g. chr7:24966446), got: {val!r}."
        )
    return val


def _normalize_pop(pop: str | Sequence[str]) -> str:
    vals = [str(pop).strip()] if isinstance(pop, str) else [str(p).strip() for p in pop]
    vals = [v.upper() for v in vals if v]
    if not vals or not all(v in _AVAIL_POP for v in vals):
        raise ValueError("Not a valid population code.")
    return "+".join(vals)


def _normalize_genome_build(genome_build: str) -> str:
    v = str(genome_build).strip().lower()
    if v not in _AVAIL_GENOME_BUILD:
        raise ValueError("Invalid genome build. Allowed values: grch37, grch38, grch38_high_coverage.")
    return v


def _resolve_output_path(file: str | bool) -> Path | None:
    if file is False:
        return None
    if not isinstance(file, str):
        raise ValueError("file must be a string path or False.")
    normalized = file.strip()
    if not normalized or normalized.upper() == "FALSE":
        return None
    out_path = Path(normalized)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    return out_path


def _normalize_snp_pairs(snp_pairs: SnpPairsLike) -> List[List[str]]:
    if snp_pairs is None:
        raise ValueError("snp_pairs cannot be None.")
    if not isinstance(snp_pairs, (list, tuple)):
        raise TypeError("snp_pairs must be a list/tuple of 2-item pairs like [('rs1','rs2'), ...].")

    out: List[List[str]] = []
    for i, pair in enumerate(snp_pairs):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError(f"snp_pairs[{i}] must be a 2-item pair (e.g., ('rs1','rs2')).")
        a = _normalize_variant(str(pair[0]).strip(), label=f"snp_pairs[{i}][0]")
        b = _normalize_variant(str(pair[1]).strip(), label=f"snp_pairs[{i}][1]")
        out.append([a, b])

    if len(out) == 0:
        raise ValueError("snp_pairs must contain at least one pair.")

    return out


def ldpair(
    var1: Optional[str] = None,
    var2: Optional[str] = None,
    snp_pairs: Optional[SnpPairsLike] = None,
    pop: str | Sequence[str] = "CEU",
    genome_build: str = "grch37",
    token: Optional[str] = None,
    file: str | bool = False,
    api_root: str = DEFAULT_API_ROOT,
    output: str = "table",
    request_method: str = "auto",
) -> Union[pd.DataFrame, str, Dict[str, Any], List[Any]]:
    """
    Query LDlink LDpair.

    Rules:
    - accept either (var1,var2) or snp_pairs (list of 2-tuples)
    - auto: GET for single pair, POST for multiple pairs
    - GET endpoint: "ldpair" with params var1,var2,pop,genome_build
    - POST endpoint: "ldpair" with json {"snp_pairs":[["rs1","rs2"],...], "pop":"...", "genome_build":"..."}
    - If multiple pairs, always parse JSON and return python dict/list regardless of output.
    - If single pair and output="table": parse TSV to DataFrame; output="text": raw string.
    """
    pop_norm = _normalize_pop(pop)
    genome_build_norm = _normalize_genome_build(genome_build)
    out_path = _resolve_output_path(file)

    if output not in {"table", "text"}:
        raise ValueError("output must be either 'table' or 'text'.")

    rm = str(request_method or "").strip().lower()
    if rm not in {"auto", "get", "post"}:
        raise ValueError("request_method must be one of: 'auto', 'get', 'post'.")

    using_single_vars = (var1 is not None) or (var2 is not None)
    if snp_pairs is not None and using_single_vars:
        raise ValueError("Provide either (var1, var2) OR snp_pairs, not both.")

    if snp_pairs is None:
        a, b = _normalize_pair(cast(str, var1), cast(str, var2))
        pairs = [[a, b]]
    else:
        pairs = _normalize_snp_pairs(snp_pairs)

    is_multi = len(pairs) > 1
    if rm == "get" and is_multi:
        raise ValueError("request_method='get' is only allowed for a single SNP pair.")
    if rm == "post" and len(pairs) == 1 and not is_multi:
        # allowed, but still treated as POST multi-style payload
        pass

    method: str
    if rm == "auto":
        method = "POST" if is_multi else "GET"
    else:
        method = rm.upper()

    if method == "GET":
        # Single pair only
        params = {
            "var1": pairs[0][0],
            "var2": pairs[0][1],
            "pop": pop_norm,
            "genome_build": genome_build_norm,
        }
        text = http_request(
            "ldpair",
            token=token,
            api_root=api_root,
            method="GET",
            params=params,
        )

        # http_request may auto-parse JSON; for LDpair GET we expect text/TSV.
        if isinstance(text, (dict, list)):
            # Unexpected, but return as-is.
            return cast(Union[Dict[str, Any], List[Any]], text)

        if output == "text":
            text_out = cast(str, text)
            if out_path is not None:
                out_path.write_text(text_out, encoding="utf-8")
            return text_out

        data_out = parse_tsv(cast(str, text))
        if out_path is not None:
            data_out.to_csv(out_path, sep="\t", index=False)
        return data_out

    # POST (multi or forced POST)
    payload = {
        "snp_pairs": pairs,
        "pop": pop_norm,
        "genome_build": genome_build_norm,
    }
    resp = http_request(
        "ldpair",
        token=token,
        api_root=api_root,
        method="POST",
        json_body=payload,
    )

    # Rule: If multiple pairs, always parse JSON and return dict/list regardless of output.
    if isinstance(resp, (dict, list)):
        if out_path is not None:
            out_path.write_text(_json.dumps(resp, ensure_ascii=False, indent=2), encoding="utf-8")
        return cast(Union[Dict[str, Any], List[Any]], resp)

    text_resp = cast(str, resp)
    if is_json_response(text_resp):
        parsed = cast(Union[Dict[str, Any], List[Any]], _json.loads(text_resp))
        if out_path is not None:
            out_path.write_text(_json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
        return parsed

    # If server returns non-JSON unexpectedly, keep it as a string to avoid data loss.
    if out_path is not None:
        out_path.write_text(text_resp, encoding="utf-8")
    return text_resp
