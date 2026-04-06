from __future__ import annotations

import io
from typing import Dict, List, Tuple

import pandas as pd

from actuarygpt_workbench.utils.data_utils import standardize_columns


def read_uploaded_file(file) -> pd.DataFrame:
    name = file.name.lower()
    content = file.read()
    if name.endswith(".csv"):
        return standardize_columns(pd.read_csv(io.BytesIO(content)))
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return standardize_columns(pd.read_excel(io.BytesIO(content)))
    raise ValueError("Unsupported file type. Use CSV or XLSX.")


def infer_schema(df: pd.DataFrame) -> List[Dict[str, str]]:
    return [{"column": c, "dtype": str(df[c].dtype)} for c in df.columns]


def validate_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> Tuple[bool, List[str]]:
    msgs = []
    required = ["origin_col", "value_col"]
    for r in required:
        if not mapping.get(r):
            msgs.append(f"Missing required mapping: {r}")
        elif mapping[r] not in df.columns:
            msgs.append(f"Mapped column not found: {mapping[r]}")

    if not mapping.get("development_col") and not mapping.get("valuation_col"):
        msgs.append("Provide either development_col or valuation_col")

    return len(msgs) == 0, msgs
