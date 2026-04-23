from __future__ import annotations

import pytest

from ldlinkpy.endpoints.ldtrait import ldtrait


def test_ldtrait_posts_expected_body_and_parses_tsv(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_request(  # type: ignore[no-untyped-def]
        endpoint: str,
        *,
        params: dict | None = None,
        json_body: dict | None = None,
        headers: dict | None = None,
        token: str | None = None,
        api_root: str,
        method: str = "GET",
        timeout: float = 180.0,
    ) -> str:
        captured["method"] = method
        captured["endpoint"] = endpoint
        captured["token"] = token
        captured["params"] = params
        captured["json_body"] = json_body
        captured["headers"] = headers
        captured["timeout"] = timeout

        return "RS_Number\tR2\nrs3\t0.99\n"

    monkeypatch.setattr("ldlinkpy.endpoints.ldtrait.request", fake_request)
    monkeypatch.setenv("LDLINK_TOKEN", "TESTTOKEN")

    df = ldtrait(
        snps=["rs3", "chr7:24966446"],
        pop=["YRI", "CEU"],
        r2d="r2",
        r2d_threshold=0.2,
        win_size=0,
        genome_build="grch38",
    )

    assert captured["method"] == "POST"
    assert captured["endpoint"] == "ldtrait"
    assert captured["token"] == "TESTTOKEN"
    assert isinstance(captured["params"], dict)
    assert captured["json_body"] is None

    params = captured["params"]
    assert isinstance(params, dict)
    assert params["snps"] == "rs3\nchr7:24966446"
    assert params["pop"] == "YRI+CEU"
    assert params["r2_d"] == "r2"
    assert params["r2_d_threshold"] == "0.2"
    assert params["window"] == "0"
    assert params["genome_build"] == "grch38"

    assert list(df.columns) == ["RS_Number", "R2"]
    assert df.loc[0, "RS_Number"] == "rs3"


def test_ldtrait_get_mode_calls_ldtraitget(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_request(  # type: ignore[no-untyped-def]
        endpoint: str,
        *,
        params: dict | None = None,
        json_body: dict | None = None,
        headers: dict | None = None,
        token: str | None = None,
        api_root: str,
        method: str = "GET",
        timeout: float = 180.0,
    ) -> str:
        captured["method"] = method
        captured["endpoint"] = endpoint
        captured["params"] = params
        return "A\tB\n1\t2\n"

    monkeypatch.setattr("ldlinkpy.endpoints.ldtrait.request", fake_request)
    monkeypatch.setenv("LDLINK_TOKEN", "TESTTOKEN")

    _ = ldtrait(snps="rs3", request_method="get")

    assert captured["method"] == "GET"
    assert captured["endpoint"] == "ldtraitget"


def test_ldtrait_validates_parity_constraints() -> None:
    with pytest.raises(ValueError, match="Input is between 1 to 50 variants"):
        ldtrait(snps=[f"rs{i}" for i in range(60)], token="tok")

    with pytest.raises(ValueError, match="Invalid query format for variant"):
        ldtrait(snps=["not-a-snp"], token="tok")

    with pytest.raises(ValueError, match="Not a valid population code"):
        ldtrait(snps="rs3", pop="BAD", token="tok")

    with pytest.raises(ValueError, match="Window size must be between 0 and 1000000 bp"):
        ldtrait(snps="rs3", win_size=1_000_001, token="tok")

    with pytest.raises(ValueError, match="Invalid input for file option"):
        ldtrait(snps="rs3", file=123, token="tok")  # type: ignore[arg-type]
