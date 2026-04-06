from __future__ import annotations

import logging
from collections import defaultdict

import pandas as pd

logger = logging.getLogger(__name__)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dataframe columns to safe lowercase strings and de-duplicate."""
    original = list(df.columns)
    seen = defaultdict(int)
    normalized = []

    for col in original:
        base = str(col).strip().lower()
        idx = seen[base]
        if idx == 0:
            normalized_col = base
        else:
            normalized_col = f"{base}_{idx}"
        seen[base] += 1
        normalized.append(normalized_col)

    if original != normalized:
        logger.info("Standardized columns from %s to %s", original, normalized)

    out = df.copy()
    out.columns = normalized
    return out
