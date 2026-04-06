from __future__ import annotations

from typing import Dict, List

import pandas as pd

from actuarygpt_workbench.utils.data_utils import standardize_columns


SAMPLE_DATASETS = ["genins", "raa"]


def list_samples() -> List[str]:
    return SAMPLE_DATASETS


def load_sample(name: str) -> pd.DataFrame:
    import chainladder as cl

    tri = cl.load_sample(name)
    # convert to long dataframe with origin/development/value
    frame = tri.to_frame(origin_as_datetime=False).reset_index()
    frame = standardize_columns(frame)

    # normalize likely columns
    origin_col = "origin" if "origin" in frame.columns else frame.columns[0]
    dev_col = "development" if "development" in frame.columns else frame.columns[1]
    value_col = [c for c in frame.columns if c not in {origin_col, dev_col}][0]
    out = frame[[origin_col, dev_col, value_col]].rename(
        columns={origin_col: "origin", dev_col: "development", value_col: "value"}
    )
    return out


def sample_default_mapping() -> Dict[str, str]:
    return {
        "origin_col": "origin",
        "development_col": "development",
        "valuation_col": None,
        "value_col": "value",
        "grain": "annual",
        "input_type": "cumulative",
    }
