from __future__ import annotations

import uuid
from typing import Dict, List

import numpy as np
import pandas as pd

from actuarygpt_workbench.domain.models import Finding


def generate_findings(cumulative_df: pd.DataFrame, link_ratio_df: pd.DataFrame) -> List[Dict]:
    findings: List[Finding] = []

    missing = cumulative_df.isna().sum().sum()
    if missing > 0:
        findings.append(
            Finding(
                finding_id=str(uuid.uuid4()),
                category="data_quality",
                title="Missing triangle cells",
                description=f"Triangle contains {int(missing)} missing cells.",
                evidence={"missing_cells": int(missing)},
                materiality="medium",
                confidence="high",
                suggested_action="Review source completeness and consider exclusions.",
            )
        )

    for col in link_ratio_df.columns:
        s = link_ratio_df[col].dropna()
        if len(s) < 4:
            continue
        med = s.median()
        mad = (s - med).abs().median() or 1e-9
        z = 0.6745 * (s - med) / mad
        outliers = s[z.abs() > 3.5]
        if not outliers.empty:
            findings.append(
                Finding(
                    finding_id=str(uuid.uuid4()),
                    category="outlier",
                    title=f"Outlier link ratios in {col}",
                    description=f"Detected {len(outliers)} robust-z outlier(s) in development link ratios.",
                    evidence={"column": col, "rows": outliers.index.astype(str).tolist(), "values": outliers.round(4).tolist()},
                    materiality="high",
                    confidence="medium",
                    suggested_action="Assess whether these years should be excluded or adjusted.",
                )
            )

    vol = link_ratio_df.std(numeric_only=True).fillna(0)
    for col, val in vol.items():
        if val > 0.35:
            findings.append(
                Finding(
                    finding_id=str(uuid.uuid4()),
                    category="volatility",
                    title=f"High volatility in {col}",
                    description="Link ratio variation exceeds stability threshold (0.35).",
                    evidence={"column": col, "std": float(val)},
                    materiality="medium",
                    confidence="medium",
                    suggested_action="Consider a credibility-weighted factor selection.",
                )
            )

    # simplistic calendar effect proxy via anti-diagonal changes
    arr = cumulative_df.to_numpy(dtype=float)
    cal_diffs = []
    for i in range(arr.shape[0] - 1):
        for j in range(arr.shape[1] - 1):
            if np.isfinite(arr[i, j]) and np.isfinite(arr[i + 1, j + 1]) and arr[i, j] != 0:
                cal_diffs.append((arr[i + 1, j + 1] / arr[i, j]) - 1)
    if cal_diffs and np.nanstd(cal_diffs) > 0.5:
        findings.append(
            Finding(
                finding_id=str(uuid.uuid4()),
                category="calendar_effect",
                title="Potential calendar year effect",
                description="Calendar-year style movement variability appears elevated.",
                evidence={"calendar_diff_std": float(np.nanstd(cal_diffs))},
                materiality="medium",
                confidence="low",
                suggested_action="Perform explicit calendar-year analysis and stress testing.",
            )
        )

    return [f.model_dump() for f in findings]
