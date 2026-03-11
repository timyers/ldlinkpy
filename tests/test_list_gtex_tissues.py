from __future__ import annotations

import pandas as pd

from ldlinkpython.lookups import list_gtex_tissues


def test_list_gtex_tissues_shape_order_and_mappings() -> None:
    dataframe = list_gtex_tissues()

    assert isinstance(dataframe, pd.DataFrame)
    assert list(dataframe.columns) == [
        "tissue_name_gtex",
        "tissue_name_ldexpress",
        "tissue_abbrev_ldexpress",
    ]
    assert len(dataframe) == 55

    assert dataframe.iloc[0]["tissue_name_gtex"] == "Adipose - Subcutaneous"
    assert dataframe.iloc[-1]["tissue_name_gtex"] == "Select All Tissues"

    mappings: dict[str, tuple[str, str]] = {
        row.tissue_name_gtex: (row.tissue_name_ldexpress, row.tissue_abbrev_ldexpress)
        for row in dataframe.itertuples(index=False)
    }
    assert mappings["Whole Blood"] == ("Whole_Blood", "WHO_BLO")
    assert mappings["Adipose - Visceral (Omentum)"] == (
        "Adipose_Visceral_Omentum",
        "ADI_VIS_OME",
    )
    assert mappings["Brain - Frontal Cortex (BA9)"] == (
        "Brain_Frontal_Cortex_BA9",
        "BRA_FRO_COR_BA9",
    )
    assert mappings["Select All Tissues"] == ("ALL", "ALL")

