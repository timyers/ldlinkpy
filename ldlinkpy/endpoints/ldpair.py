from __future__ import annotations

import json as _json
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union, cast

import pandas as pd

from .. import DEFAULT_API_ROOT
from ..http import request as http_request
from ..parsing import is_json_response, parse_tsv
from ..validators import validate_genome_build


SnpPair = Tuple[str, str]
SnpPairsLike = Sequence[Union[SnpPair, Sequence[str]]]


def _normalize_pair(a: str, b: str) -> SnpPair:
    if a is None or b is None:
        raise ValueError("Both var1 and var2 must be provided for a single SNP pair.")
    a = str(a).strip()
    b = str(b).strip()
    if not a or not b:
        raise ValueError("var1 and var2 must be non-empty strings.")
    return a, b


def _normalize_snp_pairs(snp_pairs: SnpPairsLike) -> List[List[str]]:
    if snp_pairs is None:
        raise ValueError("snp_pairs cannot be None.")
    if not isinstance(snp_pairs, (list, tuple)):
        raise TypeError("snp_pairs must be a list/tuple of 2-item pairs like [('rs1','rs2'), ...].")

    out: List[List[str]] = []
    for i, pair in enumerate(snp_pairs):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError(f"snp_pairs[{i}] must be a 2-item pair (e.g., ('rs1','rs2')).")
        a = str(pair[0]).strip()
        b = str(pair[1]).strip()
        if not a or not b:
            raise ValueError(f"snp_pairs[{i}] contains an empty SNP id.")
        out.append([a, b])

    if len(out) == 0:
        raise ValueError("snp_pairs must contain at least one pair.")

    return out


def ldpair(
    var1: Optional[str] = None,
    var2: Optional[str] = None,
    snp_pairs: Optional[SnpPairsLike] = None,
    pop: str = "CEU",
    genome_build: str = "grch37",
    token: Optional[str] = None,
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
    validate_genome_build(genome_build)

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
            "pop": pop,
            "genome_build": genome_build,
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
            return cast(str, text)

        return parse_tsv(cast(str, text))

    # POST (multi or forced POST)
    payload = {
        "snp_pairs": pairs,
        "pop": pop,
        "genome_build": genome_build,
    }
    resp = http_request(
        "ldpair",
        token=token,
        api_root=api_root,
        method="POST",
        json=payload,
    )

    # Rule: If multiple pairs, always parse JSON and return dict/list regardless of output.
    if isinstance(resp, (dict, list)):
        return cast(Union[Dict[str, Any], List[Any]], resp)

    text_resp = cast(str, resp)
    if is_json_response(text_resp):
        return cast(Union[Dict[str, Any], List[Any]], _json.loads(text_resp))

    # If server returns non-JSON unexpectedly, keep it as a string to avoid data loss.
    return text_resp
