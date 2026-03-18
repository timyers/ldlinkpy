# tests/test_validators.py

import pytest

from ldlinkpy.exceptions import TokenMissingError, ValidationError
from ldlinkpy.validators import (
    ensure_token,
    normalize_list_arg,
    normalize_snps,
    validate_genome_build,
    validate_r2d,
    validate_threshold,
)


def test_ensure_token_reads_env_when_token_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LDLINK_TOKEN", " abc123 ")
    assert ensure_token(None) == "abc123"


def test_ensure_token_raises_when_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LDLINK_TOKEN", raising=False)
    with pytest.raises(TokenMissingError):
        ensure_token(None)


def test_normalize_list_arg_string() -> None:
    assert normalize_list_arg("  EUR ") == "EUR"


def test_normalize_list_arg_list_default_joiner() -> None:
    assert normalize_list_arg(["EUR", " AFR ", "", "AMR"]) == "EUR+AFR+AMR"


def test_normalize_list_arg_list_custom_joiner() -> None:
    assert normalize_list_arg(["EUR", "AFR"]) == "EUR+AFR"
    assert normalize_list_arg(["EUR", "AFR"], joiner=",") == "EUR,AFR"


def test_normalize_snps_trims_and_splits_string() -> None:
    assert normalize_snps(" rs1, rs2  rs3+rs4;;|rs5 ") == ["rs1", "rs2", "rs3", "rs4", "rs5"]


def test_normalize_snps_trims_list_and_drops_empty() -> None:
    assert normalize_snps([" rs1 ", "", "rs2", "   "]) == ["rs1", "rs2"]


def test_normalize_snps_rejects_empty_string() -> None:
    with pytest.raises(ValidationError):
        normalize_snps("   ")


def test_normalize_snps_rejects_empty_list() -> None:
    with pytest.raises(ValidationError):
        normalize_snps([])


def test_validate_r2d_accepts_and_normalizes() -> None:
    assert validate_r2d("R2") == "r2"
    assert validate_r2d(" d ") == "d"


def test_validate_r2d_rejects_bad_values() -> None:
    with pytest.raises(ValidationError):
        validate_r2d("r")
    with pytest.raises(ValidationError):
        validate_r2d("dprime")
    with pytest.raises(ValidationError):
        validate_r2d("")


def test_validate_genome_build_accepts_and_normalizes() -> None:
    assert validate_genome_build("GRCh37") == "grch37"
    assert validate_genome_build(" grch38 ") == "grch38"


def test_validate_genome_build_rejects_bad_values() -> None:
    with pytest.raises(ValidationError):
        validate_genome_build("hg19")
    with pytest.raises(ValidationError):
        validate_genome_build("hg38")
    with pytest.raises(ValidationError):
        validate_genome_build("")


def test_validate_threshold_boundaries() -> None:
    assert validate_threshold("thr", 0.0) == 0.0
    assert validate_threshold("thr", 1.0) == 1.0
    assert validate_threshold("thr", 0.5, minv=0.0, maxv=1.0) == 0.5


def test_validate_threshold_out_of_range() -> None:
    with pytest.raises(ValidationError):
        validate_threshold("thr", -0.0001)
    with pytest.raises(ValidationError):
        validate_threshold("thr", 1.0001)
    with pytest.raises(ValidationError):
        validate_threshold("thr", 2.0, minv=0.0, maxv=1.0)


def test_validate_threshold_non_numeric() -> None:
    with pytest.raises(ValidationError):
        validate_threshold("thr", "nope")  # type: ignore[arg-type]


def test_validate_threshold_bad_name() -> None:
    with pytest.raises(ValidationError):
        validate_threshold("", 0.5)
    with pytest.raises(ValidationError):
        validate_threshold("   ", 0.5)

