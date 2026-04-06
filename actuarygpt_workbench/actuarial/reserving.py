from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def deterministic_link_ratios(cumulative_df: pd.DataFrame) -> pd.DataFrame:
    ratios = pd.DataFrame(index=cumulative_df.index)
    cols = list(cumulative_df.columns)
    for i in range(len(cols) - 1):
        c0, c1 = cols[i], cols[i + 1]
        ratios[f"{c0}->{c1}"] = cumulative_df[c1] / cumulative_df[c0]
    return ratios.replace([np.inf, -np.inf], np.nan)


def run_chainladder_models(chainladder_triangle) -> Dict:
    import chainladder as cl

    dev = cl.Development().fit(chainladder_triangle)
    cl_model = cl.Chainladder().fit(chainladder_triangle)
    mack = cl.MackChainladder().fit(chainladder_triangle)

    try:
        boot = cl.BootstrapODPSample(n_sims=200).fit(chainladder_triangle)
        boot_summary = {"status": "ok", "n_sims": 200}
    except Exception as exc:  # pragma: no cover
        boot_summary = {"status": "unavailable", "reason": str(exc)}

    ldf = dev.ldf_.to_frame(origin_as_datetime=False).reset_index(drop=True)
    cdf = dev.cdf_.to_frame(origin_as_datetime=False).reset_index(drop=True)

    ultimate = cl_model.ultimate_.to_frame(origin_as_datetime=False)
    ibnr = cl_model.ibnr_.to_frame(origin_as_datetime=False)
    latest = chainladder_triangle.latest_diagonal.to_frame(origin_as_datetime=False)

    reserve_summary = ultimate.join(ibnr, lsuffix="_ultimate", rsuffix="_ibnr")
    reserve_summary = reserve_summary.join(latest, rsuffix="_latest")

    mack_std_err = getattr(mack, "mack_std_err_", None)
    mack_info = (
        mack_std_err.to_frame(origin_as_datetime=False).reset_index(drop=True).to_dict(orient="records")
        if mack_std_err is not None
        else []
    )

    return {
        "ldf_table": ldf.to_dict(orient="records"),
        "cdf_table": cdf.to_dict(orient="records"),
        "reserve_summary": reserve_summary.reset_index().to_dict(orient="records"),
        "latest_diagonal": latest.reset_index().to_dict(orient="records"),
        "mack_std_err": mack_info,
        "bootstrap": boot_summary,
    }
