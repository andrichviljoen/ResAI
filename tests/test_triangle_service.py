import pandas as pd

from actuarygpt_workbench.services.triangle_service import build_triangle


def test_build_triangle_with_valuation_dates_and_duplicates():
    df = pd.DataFrame(
        {
            "origin": ["2018-01-01", "2018-01-01", "2018-01-01", "2019-01-01"],
            "valuation": ["2018-12-31", "2019-12-31", "2019-12-31", "2019-12-31"],
            "value": [100, 50, 25, 120],
        }
    )
    mapping = {
        "origin_col": "origin",
        "valuation_col": "valuation",
        "development_col": None,
        "value_col": "value",
        "grain": "annual",
        "input_type": "incremental",
    }
    res = build_triangle(df, mapping)
    assert list(res.incremental_df.columns) == [0, 1]
    assert res.incremental_df.loc["2018-01", 1] == 75


def test_incremental_cumulative_conversion():
    df = pd.DataFrame(
        {
            "origin": ["2018", "2018", "2019", "2019"],
            "dev": [0, 1, 0, 1],
            "value": [100, 50, 120, 60],
        }
    )
    mapping = {
        "origin_col": "origin",
        "development_col": "dev",
        "valuation_col": None,
        "value_col": "value",
        "grain": "annual",
        "input_type": "incremental",
    }
    res = build_triangle(df, mapping)
    assert res.cumulative_df.loc["2018", 1] == 150
    assert res.cumulative_df.loc["2019", 1] == 180
