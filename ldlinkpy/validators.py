# ldlinkpy/validators.py
from __future__ import annotations

import os
import re
from typing import Iterable

from .exceptions import TokenMissingError, ValidationError


def ensure_token(token: str | None) -> str:
    """
    Return an LDlink API token.

    If `token` is None, reads from environment variable LDLINK_TOKEN.
    Raises TokenMissingError if no token is available.
    """
    if token is not None:
        tok = token.strip()
        if not tok:
            raise TokenMissingError(
                "LDlink token was provided but is empty. Provide a non-empty token or set LDLINK_TOKEN."
            )
        return tok

    env_tok = os.getenv("LDLINK_TOKEN")
    if env_tok is None or not env_tok.strip():
        raise TokenMissingError(
            "LDlink token is missing. Pass `token=` or set environment variable LDLINK_TOKEN."
        )
    return env_tok.strip()


def normalize_list_arg(x: str | list[str] | tuple[str, ...], joiner: str = "+") -> str:
    """
    Normalize list-like arguments into a single string joined by `joiner`.

    - If x is a string, returns stripped string.
    - If x is a list/tuple of strings, strips each item, drops empty items, and joins with `joiner`.
    """
    if isinstance(x, str):
        return x.strip()

    if not isinstance(x, (list, tuple)):
        raise ValidationError(f"Expected str, list[str], or tuple[str,...] but got {type(x).__name__}.")

    parts: list[str] = []
    for item in x:
        if not isinstance(item, str):
            raise ValidationError(f"All items must be strings, but got {type(item).__name__}.")
        s = item.strip()
        if s:
            parts.append(s)

    return joiner.join(parts)


_SPLIT_SNPS_RE = re.compile(r"[,\s+;|]+")


def normalize_snps(snps: str | list[str] | tuple[str, ...]) -> list[str]:
    """
    Normalize SNP inputs into a list of SNP strings.

    - Strips whitespace
    - Drops empty entries
    - Preserves order
    - Raises ValidationError if the resulting list is empty
    """
    items: list[str] = []

    if isinstance(snps, str):
        raw = snps.strip()
        if raw:
            items = [s for s in _SPLIT_SNPS_RE.split(raw) if s and s.strip()]
            items = [s.strip() for s in items if s.strip()]
    elif isinstance(snps, (list, tuple)):
        for item in snps:
            if not isinstance(item, str):
                raise ValidationError(f"All SNPs must be strings, but got {type(item).__name__}.")
            s = item.strip()
            if s:
                items.append(s)
    else:
        raise ValidationError(f"Expected str, list[str], or tuple[str,...] but got {type(snps).__name__}.")

    if not items:
        raise ValidationError("No SNPs provided after normalization.")
    return items


def validate_r2d(r2d: str) -> str:
    """
    Validate r2/d selector. Allowed values: {'r2', 'd'} (case-insensitive).
    Returns normalized value.
    """
    if not isinstance(r2d, str):
        raise ValidationError(f"r2d must be a string, got {type(r2d).__name__}.")
    v = r2d.strip().lower()
    if v not in {"r2", "d"}:
        raise ValidationError("Invalid r2d value. Allowed values are 'r2' or 'd'.")
    return v


def validate_genome_build(build: str) -> str:
    """
    Validate genome build. Allowed values: {'grch37', 'grch38'} (case-insensitive).
    Returns normalized value.
    """
    if not isinstance(build, str):
        raise ValidationError(f"build must be a string, got {type(build).__name__}.")
    v = build.strip().lower()
    if v not in {"grch37", "grch38"}:
        raise ValidationError("Invalid genome build. Allowed values are 'grch37' or 'grch38'.")
    return v


def validate_threshold(name: str, value: float, minv: float = 0.0, maxv: float = 1.0) -> float:
    """
    Validate numeric threshold within [minv, maxv] (inclusive).
    Returns the value as float.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValidationError("Threshold name must be a non-empty string.")

    try:
        v = float(value)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"{name} must be a number.") from e

    if v < minv or v > maxv:
        raise ValidationError(f"{name} must be between {minv} and {maxv} (inclusive).")
    return v
