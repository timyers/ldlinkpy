"""Lookup helpers for packaged non-endpoint reference datasets.

This module intentionally contains non-endpoint lookup helpers for ldlinkpy.
It is the future home for additional packaged helpers such as ``list_pop()`` and
``list_gtex_tissues()`` that should remain separate from endpoint wrappers.
"""

from __future__ import annotations

from importlib import resources

import pandas as pd

from ldlinkpy.exceptions import ParseError

_EXPECTED_COLUMNS: list[str] = ["chip_code", "chip_name"]
_EXPECTED_POP_COLUMNS: list[str] = ["pop_code", "super_pop_code", "pop_name"]
_EXPECTED_GTEX_TISSUE_COLUMNS: list[str] = [
    "tissue_name_gtex",
    "tissue_name_ldexpress",
    "tissue_abbrev_ldexpress",
]

def list_chip_platforms() -> pd.DataFrame:
    """Return LDlink SNP chip platforms from packaged lookup data."""
    try:
        csv_path = resources.files("ldlinkpy").joinpath("data/chips.csv")
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            dataframe = pd.read_csv(handle, dtype=str)
    except Exception as exc:  # pragma: no cover - exception path validated by behavior
        raise ParseError(f"Failed to load packaged chip lookup table: {exc}") from exc

    columns: list[str] = list(dataframe.columns)
    if columns != _EXPECTED_COLUMNS:
        raise ParseError(
            "Invalid packaged chip lookup table columns. "
            f"Expected {_EXPECTED_COLUMNS} in order, got {columns}."
        )

    return dataframe


def list_chips() -> pd.DataFrame:
    """Alias for :func:`list_chip_platforms` kept for LDlinkR naming parity."""
    return list_chip_platforms()


def list_pop() -> pd.DataFrame:
    """Return LDlink reference populations from packaged lookup data."""
    try:
        csv_path = resources.files("ldlinkpy").joinpath("data/pops.csv")
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            dataframe = pd.read_csv(handle, dtype=str)
    except Exception as exc:  # pragma: no cover - exception path validated by behavior
        raise ParseError(f"Failed to load packaged population lookup table: {exc}") from exc

    columns: list[str] = list(dataframe.columns)
    if columns != _EXPECTED_POP_COLUMNS:
        raise ParseError(
            "Invalid packaged population lookup table columns. "
            f"Expected {_EXPECTED_POP_COLUMNS} in order, got {columns}."
        )

    return dataframe
    

def list_gtex_tissues() -> pd.DataFrame:
    """Return LDlink GTEx tissues from packaged lookup data."""
    try:
        csv_path = resources.files("ldlinkpy").joinpath("data/gtex_tissues.csv")
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            dataframe = pd.read_csv(handle, dtype=str)
    except Exception as exc:  # pragma: no cover - exception path validated by behavior
        raise ParseError(f"Failed to load packaged GTEx tissue lookup table: {exc}") from exc

    columns: list[str] = list(dataframe.columns)
    if columns != _EXPECTED_GTEX_TISSUE_COLUMNS:
        raise ParseError(
            "Invalid packaged GTEx tissue lookup table columns. "
            f"Expected {_EXPECTED_GTEX_TISSUE_COLUMNS} in order, got {columns}."
        )

    return dataframe
    