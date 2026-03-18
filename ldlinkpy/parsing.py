from __future__ import annotations

import json
import re
from io import StringIO
from typing import Any

import pandas as pd

from .exceptions import ParseError


_JSON_LEADING_RE = re.compile(r"^\s*[\{\[]", re.DOTALL)
_NUMERIC_TOKEN_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def is_json_response(text: str) -> bool:
    """Return True if text appears to be a JSON object/array (after leading whitespace)."""
    if text is None:
        return False
    return bool(_JSON_LEADING_RE.match(text))


def _strip_blank_lines(text: str) -> str:
    if text is None:
        return ""
    lines = [ln for ln in text.splitlines() if ln.strip() != ""]
    return "\n".join(lines)


def _looks_like_header(first_line: str) -> bool:
    """
    Heuristic: if any token contains letters or common header punctuation, treat as header.
    If all tokens are purely numeric-like, treat as no header.
    """
    tokens = [t.strip() for t in first_line.split("\t")]
    tokens = [t for t in tokens if t != ""]
    if not tokens:
        return True  # default to header-like; caller will fail more informatively if empty

    # If any token contains a letter, it's almost certainly a header.
    if any(any(ch.isalpha() for ch in tok) for tok in tokens):
        return True

    # If any token looks like an rsID, treat as header (rare but possible).
    if any(tok.lower().startswith("rs") and tok[2:].isdigit() for tok in tokens):
        return True

    # If all tokens numeric-ish, likely not a header.
    if all(_NUMERIC_TOKEN_RE.match(tok) for tok in tokens):
        return False

    # Otherwise default to header.
    return True


def parse_tsv(text: str) -> pd.DataFrame:
    """
    Parse a TSV string into a DataFrame.
    Robustness features:
      - skips blank lines
      - attempts to detect whether a header row is present
    """
    cleaned = _strip_blank_lines(text)
    if cleaned.strip() == "":
        raise ParseError("Unable to parse TSV: response is empty or only blank lines.")

    first_line = cleaned.splitlines()[0]
    has_header = _looks_like_header(first_line)

    try:
        df = pd.read_csv(
            StringIO(cleaned),
            sep="\t",
            header=0 if has_header else None,
            comment=None,
            dtype="string",
            keep_default_na=False,
            na_values=[],
        )
    except Exception as e:
        snippet = cleaned[:300].replace("\n", "\\n")
        raise ParseError(f"Unable to parse TSV: {e}. Response starts with: '{snippet}'") from e

    # If no header, give default column names like V1, V2, ...
    if not has_header:
        df.columns = [f"V{i}" for i in range(1, len(df.columns) + 1)]

    return df


def parse_matrix(text: str) -> pd.DataFrame:
    """
    Parse an LDmatrix-style TSV matrix into a DataFrame:
      - first row contains column headers
      - first column contains row names (index)
    """
    cleaned = _strip_blank_lines(text)
    if cleaned.strip() == "":
        raise ParseError("Unable to parse matrix: response is empty or only blank lines.")

    try:
        df = pd.read_csv(
            StringIO(cleaned),
            sep="\t",
            header=0,
            index_col=0,
            dtype="string",
            keep_default_na=False,
            na_values=[],
        )
    except Exception as e:
        snippet = cleaned[:300].replace("\n", "\\n")
        raise ParseError(f"Unable to parse matrix: {e}. Response starts with: '{snippet}'") from e

    # Some matrices may include an empty top-left cell leading to an "Unnamed: 0" column.
    if "Unnamed: 0" in df.columns and df.index.name is None:
        try:
            df = df.set_index("Unnamed: 0", drop=True)
        except Exception:
            pass

    return df


def coerce_response(text: str, kind: str) -> Any:
    """
    Coerce a response body into the requested kind.

    kind in {"tsv","matrix","raw","json_auto"}:
      - tsv: DataFrame via parse_tsv
      - matrix: DataFrame via parse_matrix
      - raw: original string
      - json_auto: dict/list via json.loads if looks like JSON, else raw string
    """
    if kind not in {"tsv", "matrix", "raw", "json_auto"}:
        raise ValueError("kind must be one of {'tsv','matrix','raw','json_auto'}")

    if kind == "raw":
        return text

    if kind == "tsv":
        return parse_tsv(text)

    if kind == "matrix":
        return parse_matrix(text)

    # json_auto
    if is_json_response(text):
        try:
            return json.loads(text)
        except Exception as e:
            snippet = (text or "")[:300].replace("\n", "\\n")
            raise ParseError(
                f"Response looked like JSON but could not be decoded: {e}. "
                f"Response starts with: '{snippet}'"
            ) from e
    return text
