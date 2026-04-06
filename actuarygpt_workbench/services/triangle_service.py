from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from actuarygpt_workbench.utils.periods import parse_period_label, period_distance


@dataclass
class TriangleBuildResult:
    triangle_df: pd.DataFrame
    incremental_df: pd.DataFrame
    cumulative_df: pd.DataFrame
    metadata: Dict


def _to_period_series(series: pd.Series) -> pd.Series:
    return series.map(parse_period_label)


def build_triangle(df: pd.DataFrame, mapping: Dict[str, str]) -> TriangleBuildResult:
    grain = mapping.get("grain", "annual")
    input_type = mapping.get("input_type", "cumulative")
    work = df.copy()

    work["_origin_period"] = _to_period_series(work[mapping["origin_col"]])

    if mapping.get("development_col"):
        work["development_age"] = pd.to_numeric(work[mapping["development_col"]], errors="coerce").astype("Int64")
    else:
        work["_valuation_period"] = _to_period_series(work[mapping["valuation_col"]])
        work["development_age"] = [
            period_distance(o, v, grain)
            for o, v in zip(work["_origin_period"], work["_valuation_period"])
        ]

    work = work.dropna(subset=["development_age"])
    work["development_age"] = work["development_age"].astype(int)
    work["origin_label"] = work["_origin_period"].astype(str)

    grouped = (
        work.groupby(["origin_label", "development_age"], as_index=False)[mapping["value_col"]]
        .sum()
        .rename(columns={mapping["value_col"]: "value"})
    )
    tri = grouped.pivot(index="origin_label", columns="development_age", values="value").sort_index().sort_index(axis=1)

    if input_type == "incremental":
        incr = tri.fillna(0)
        cum = incr.cumsum(axis=1)
    else:
        cum = tri.ffill(axis=1)
        incr = cum.diff(axis=1)
        first_col = cum.columns.min() if len(cum.columns) else 0
        if len(cum.columns):
            incr[first_col] = cum[first_col]
        incr = incr.fillna(0)

    return TriangleBuildResult(
        triangle_df=tri,
        incremental_df=incr,
        cumulative_df=cum,
        metadata={"grain": grain, "input_type": input_type, "max_development_age": int(tri.columns.max()) if len(tri.columns) else 0},
    )


def to_chainladder_triangle(cumulative_df: pd.DataFrame):
    try:
        import chainladder as cl
    except ImportError as exc:
        raise RuntimeError("chainladder is required for actuarial calculations") from exc

    long_df = cumulative_df.reset_index().melt(id_vars=["origin_label"], var_name="development", value_name="value")
    long_df = long_df.dropna(subset=["value"])
    long_df["origin"] = pd.to_datetime(long_df["origin_label"], errors="coerce")
    long_df["origin"] = long_df["origin"].fillna(pd.to_datetime(long_df["origin_label"].str[:4] + "-01-01"))
    long_df["development"] = long_df["development"].astype(int)

    tri = cl.Triangle(
        long_df,
        origin="origin",
        development="development",
        columns=["value"],
        cumulative=True,
    )
    return tri
