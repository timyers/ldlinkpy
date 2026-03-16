from __future__ import annotations

import pandas as pd

from ldlinkpython.lookups import list_pop


def test_list_pop_shape_order_and_mappings() -> None:
    dataframe = list_pop()

    assert isinstance(dataframe, pd.DataFrame)
    assert list(dataframe.columns) == ["pop_code", "super_pop_code", "pop_name"]
    assert len(dataframe) == 32

    mappings: dict[str, tuple[str, str]] = {
        row.pop_code: (row.super_pop_code, row.pop_name)
        for row in dataframe.itertuples(index=False)
    }
    assert mappings["ALL"] == ("ALL", "ALL POPULATIONS")
    assert mappings["CEU"] == ("EUR", "Utah Residents from North and West Europe")
    assert mappings["YRI"] == ("AFR", "Yoruba in Ibadan, Nigera")

    assert dataframe.iloc[0]["pop_code"] == "ALL"
    assert dataframe.iloc[1]["pop_code"] == "AFR"

