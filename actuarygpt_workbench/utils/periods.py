from __future__ import annotations

import re
from typing import Any

import pandas as pd


GRAIN_TO_MONTHS = {
    "monthly": 1,
    "quarterly": 3,
    "semi-annual": 6,
    "annual": 12,
}


def parse_period_label(value: Any) -> pd.Period:
    """Parse period labels across common formats including YYYY-MM-DD."""
    if pd.isna(value):
        raise ValueError("Empty period label")

    if isinstance(value, pd.Period):
        return value
    if isinstance(value, (pd.Timestamp,)):
        return value.to_period("M")

    s = str(value).strip()
    if re.fullmatch(r"\d{4}", s):
        return pd.Period(s, freq="Y")
    if re.fullmatch(r"\d{6}", s):
        return pd.Period(f"{s[:4]}-{s[4:]}", freq="M")
    if re.fullmatch(r"\d{4}Q[1-4]", s, flags=re.IGNORECASE):
        return pd.Period(s.upper(), freq="Q")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return pd.Timestamp(s).to_period("M")

    dt = pd.to_datetime(s, errors="coerce")
    if pd.notna(dt):
        return dt.to_period("M")

    raise ValueError(f"Could not parse period label '{value}'")


def period_distance(origin: pd.Period, valuation: pd.Period, grain: str) -> int:
    months = GRAIN_TO_MONTHS[grain]
    return max(0, (valuation.year - origin.year) * 12 + valuation.month - origin.month) // months
