from __future__ import annotations

import pandas as pd
import pandas.testing as pdt

from ldlinkpython.lookups import list_chip_platforms, list_chips


def test_list_chip_platforms_shape_and_mappings() -> None:
    dataframe = list_chip_platforms()

    assert isinstance(dataframe, pd.DataFrame)
    assert list(dataframe.columns) == ["chip_code", "chip_name"]
    assert len(dataframe) == 81

    mappings: dict[str, str] = dict(
        zip(dataframe["chip_code"], dataframe["chip_name"], strict=True)
    )
    assert mappings["I_100"] == "Illumina Infinium Human100kv1"
    assert mappings["I_GSA-v1"] == "Illumina Global Screening version 1"
    assert mappings["A_PMRA"] == "Affymetrix Axiom Precision Medicine Research"
    assert mappings["A_UKBA"] == "Affymetrix Axiom UK Biobank"


def test_list_chips_alias_matches_list_chip_platforms() -> None:
    expected = list_chip_platforms()
    observed = list_chips()

    pdt.assert_frame_equal(observed, expected)

