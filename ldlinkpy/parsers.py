from __future__ import annotations

from io import StringIO
from typing import Any, Iterable, List, Optional, Sequence, Tuple

import pandas as pd


def parse_matrix(payload: Any) -> pd.DataFrame:
    """
    Parse an LDlink matrix response into a pandas DataFrame.

    Supports common LDlink response shapes:
      1) TSV text (string), with leading TAB in header.
      2) dict containing TSV under common keys.
      3) list-of-lists (JSON matrix). Optionally labeled if first row contains labels.
      4) dict containing a list-of-lists matrix under common keys.

    Returns
    -------
    pandas.DataFrame
    """
    # 1) TSV / text path
    text = _try_extract_matrix_text(payload)
    if text is not None:
        return _parse_tsv_matrix(text)

    # 2) list-of-lists / JSON matrix path
    matrix, row_labels, col_labels = _try_extract_matrix_array(payload)
    if matrix is not None:
        df = pd.DataFrame(matrix, index=row_labels, columns=col_labels)
        df = df.apply(pd.to_numeric, errors="coerce")
        if df.shape[0] != df.shape[1]:
            raise ValueError(f"Parsed matrix is not square: shape={df.shape}")
        return df

    # 3) error-like payloads
    msg = _try_extract_error_message(payload)
    if msg:
        raise ValueError(f"LDlink returned an error payload: {msg}")

    raise TypeError(
        "Unsupported matrix payload type/shape. Expected TSV text, dict containing text/matrix, "
        "or list-of-lists matrix."
    )


def _parse_tsv_matrix(text: str) -> pd.DataFrame:
    # IMPORTANT: do NOT strip() the whole text, it can remove the leading TAB in header.
    lines = [ln for ln in text.splitlines() if ln.strip() != ""]
    if not lines:
        raise ValueError("Empty matrix response.")

    buf = StringIO("\n".join(lines))
    df = pd.read_csv(buf, sep="\t", header=0, dtype=str)

    # First column is row labels; header is often blank so pandas uses "Unnamed: 0"
    first_col = df.columns[0]
    df = df.set_index(first_col)

    df = df.apply(pd.to_numeric, errors="coerce")

    if df.shape[0] != df.shape[1]:
        raise ValueError(f"Parsed matrix is not square: shape={df.shape}")
    return df


def _try_extract_matrix_text(payload: Any) -> Optional[str]:
    if isinstance(payload, bytes):
        try:
            return payload.decode("utf-8", errors="replace")
        except Exception:
            return None

    if isinstance(payload, str):
        return payload

    if isinstance(payload, dict):
        # Try common keys that might contain the TSV
        for key in ("matrix", "data", "result", "results", "output", "text", "tsv"):
            val = payload.get(key)
            if isinstance(val, str) and val.strip():
                return val

        # Sometimes nested
        for key in ("response", "payload"):
            val = payload.get(key)
            if isinstance(val, dict):
                for subkey in ("matrix", "data", "result", "output", "text", "tsv"):
                    subval = val.get(subkey)
                    if isinstance(subval, str) and subval.strip():
                        return subval

    return None


def _try_extract_matrix_array(
    payload: Any,
) -> Tuple[Optional[List[List[Any]]], Optional[List[str]], Optional[List[str]]]:
    """
    Try to extract a numeric matrix and (optional) labels from JSON-like payloads.
    Returns (matrix, row_labels, col_labels) or (None, None, None).
    """
    # Direct list-of-lists
    if isinstance(payload, list) and payload:
        return _coerce_list_payload_to_matrix(payload)

    # Dict containing matrix under common keys
    if isinstance(payload, dict):
        for key in ("matrix", "data", "result", "results"):
            val = payload.get(key)
            if isinstance(val, list) and val:
                return _coerce_list_payload_to_matrix(val)

        # Sometimes nested
        for key in ("response", "payload"):
            val = payload.get(key)
            if isinstance(val, dict):
                for subkey in ("matrix", "data", "result", "results"):
                    subval = val.get(subkey)
                    if isinstance(subval, list) and subval:
                        return _coerce_list_payload_to_matrix(subval)

    return None, None, None


def _coerce_list_payload_to_matrix(
    val: list,
) -> Tuple[Optional[List[List[Any]]], Optional[List[str]], Optional[List[str]]]:
    # Must be list-of-lists
    if not all(isinstance(r, list) for r in val):
        return None, None, None

    rows: List[list] = val  # type: ignore[assignment]
    if not rows:
        return None, None, None

    # Case A: labeled table where first row is header strings (often with blank first cell)
    if all(isinstance(x, str) for x in rows[0]) and len(rows[0]) >= 2:
        header = rows[0]
        # If header[0] is blank (common), labels are header[1:]
        col_labels = [str(x) for x in header[1:]]
        matrix: List[List[Any]] = []
        row_labels: List[str] = []

        for r in rows[1:]:
            if not isinstance(r, list) or len(r) != len(col_labels) + 1:
                return None, None, None
            row_labels.append(str(r[0]))
            matrix.append(r[1:])

        return matrix, row_labels, col_labels

    # Case B: unlabeled pure numeric matrix
    # Validate rectangular
    ncols = len(rows[0])
    if ncols == 0:
        return None, None, None
    if not all(len(r) == ncols for r in rows):
        return None, None, None

    # If square, add generic labels 0..n-1
    nrows = len(rows)
    if nrows == ncols:
        labels = [str(i) for i in range(nrows)]
        return rows, labels, labels

    # Not square: still return, but caller will reject later
    return rows, None, None


def _try_extract_error_message(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        for key in ("error", "errors", "message", "detail", "status"):
            val = payload.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return None
