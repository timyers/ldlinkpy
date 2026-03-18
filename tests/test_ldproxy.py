from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pandas as pd
import pytest
import responses

from ldlinkpy.endpoints.ldproxy import ldproxy


@responses.activate
def test_ldproxy_hits_correct_url_and_params_and_returns_dataframe() -> None:
    api_root = "https://example.org/LDlinkRest"
    token = "test-token-123"
    expected_url = f"{api_root}/ldproxy"

    snp = "rs123"
    pop = ["CEU", "YRI"]
    r2d = "r2"
    win_size = 500000
    genome_build = "grch37"

    tsv = (
        "RS_Number\tCoord\tR2\n"
        "rs123\t1:1000\t1.0\n"
        "rs456\t1:1100\t0.8\n"
    )

    def _callback(request):
        parsed = urlparse(request.url)
        assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == expected_url

        qs = parse_qs(parsed.query)

        def one(key: str) -> str:
            assert key in qs, f"missing query param: {key}"
            assert len(qs[key]) == 1, f"expected single value for {key}"
            return qs[key][0]

        assert one("var") == snp
        assert one("pop") == "CEU+YRI"
        assert one("r2_d") == r2d
        assert one("window") == str(win_size)
        assert one("genome_build") == genome_build
        assert one("token") == token

        return (200, {"Content-Type": "text/plain"}, tsv)

    responses.add_callback(
        method=responses.GET,
        url=expected_url,
        callback=_callback,
        content_type="text/plain",
    )

    df = ldproxy(
        snp=snp,
        pop=pop,
        r2d=r2d,
        win_size=win_size,
        genome_build=genome_build,
        token=token,
        api_root=api_root,
        return_type="dataframe",
    )

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["RS_Number", "Coord", "R2"]
    assert df.shape == (2, 3)

    # dtype=str is used by the endpoint parser, so values should be strings
    assert df.loc[0, "RS_Number"] == "rs123"
    assert df.loc[0, "Coord"] == "1:1000"
    assert df.loc[0, "R2"] == "1.0"
    assert df.loc[1, "RS_Number"] == "rs456"
    assert df.loc[1, "R2"] == "0.8"
