# tests/test_parsing.py

from __future__ import annotations

import pandas as pd
import pytest

from ldlinkpy.parsing import coerce_response, is_json_response, parse_matrix, parse_tsv


def test_is_json_response_true_cases() -> None:
    assert is_json_response('{"a": 1}') is True
    assert is_json_response('   {"a": 1}') is True
    assert is_json_response("\n\t[{\"a\": 1}]") is True
    assert is_json_response("  [1,2,3]") is True


def test_is_json_response_false_cases() -> None:
    assert is_json_response("") is False
    assert is_json_response("   ") is False
    assert is_json_response("not json") is False
    assert is_json_response(" (not json)") is False
    assert is_json_response("<xml></xml>") is False


def test_parse_tsv_with_header_and_blank_lines() -> None:
    text = "\n\ncol1\tcol2\nA\t1\nB\t2\n\n"
    df = parse_tsv(text)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["col1", "col2"]
    assert df.shape == (2, 2)
    assert df.loc[0, "col1"] == "A"
    assert df.loc[1, "col2"] == "2"


def test_parse_tsv_without_header_numeric_first_row() -> None:
    # First row is purely numeric-like => should be treated as data (no header)
    text = "1\t2\n3\t4\n"
    df = parse_tsv(text)

    assert list(df.columns) == ["V1", "V2"]
    assert df.shape == (2, 2)
    assert df.loc[0, "V1"] == "1"
    assert df.loc[1, "V2"] == "4"


def test_parse_matrix_ldmatrix_style() -> None:
    text = "\n\tRS1\tRS2\tRS3\nRS1\t1\t0.2\t0\nRS2\t0.2\t1\t0.8\nRS3\t0\t0.8\t1\n\n"
    df = parse_matrix(text)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["RS1", "RS2", "RS3"]
    assert list(df.index) == ["RS1", "RS2", "RS3"]
    assert df.loc["RS1", "RS1"] == "1"
    assert df.loc["RS2", "RS3"] == "0.8"


def test_coerce_response_json_auto_json_and_non_json() -> None:
    obj = coerce_response('{"x": 1, "y": [2, 3]}', kind="json_auto")
    assert isinstance(obj, dict)
    assert obj["x"] == 1
    assert obj["y"] == [2, 3]

    raw = coerce_response("not json", kind="json_auto")
    assert isinstance(raw, str)
    assert raw == "not json"


def test_coerce_response_kinds() -> None:
    tsv_text = "a\tb\n1\t2\n"
    df_tsv = coerce_response(tsv_text, kind="tsv")
    assert isinstance(df_tsv, pd.DataFrame)
    assert list(df_tsv.columns) == ["a", "b"]

    matrix_text = "\tA\tB\nA\t1\t0\nB\t0\t1\n"
    df_mat = coerce_response(matrix_text, kind="matrix")
    assert isinstance(df_mat, pd.DataFrame)
    assert list(df_mat.index) == ["A", "B"]

    raw = coerce_response("hello", kind="raw")
    assert raw == "hello"


def test_coerce_response_invalid_kind() -> None:
    with pytest.raises(ValueError):
        coerce_response("x", kind="nope")  # type: ignore[arg-type]
