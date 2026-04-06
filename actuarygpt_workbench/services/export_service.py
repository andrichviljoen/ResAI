from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List

import pandas as pd

from actuarygpt_workbench.domain.models import AuditPack


def build_audit_pack(state: Dict) -> Dict:
    pack = AuditPack.default()
    pack.app_run_metadata.update(
        {
            "generated_at": datetime.utcnow().isoformat(),
            "app": "ActuaryGPT Triangle Diagnostic Workbench",
        }
    )
    pack.dataset_info = state.get("dataset_info", {})
    pack.field_mapping = state.get("mapping", {})
    pack.validation_results = state.get("validation_results", {})
    pack.triangle_definition = state.get("triangle_definition", {})
    pack.triangle_summary = state.get("triangle_summary", {})
    pack.diagnostics = state.get("diagnostics", [])
    pack.selected_factors = state.get("selected_factors", {})
    pack.reserve_outputs = state.get("reserve_outputs", {})
    pack.user_overrides = state.get("user_overrides", {})
    pack.ai_context = state.get("ai_context", {})
    pack.generated_commentary = state.get("ai_history", [])
    return pack.model_dump()


def to_json_bytes(data: Dict) -> bytes:
    return json.dumps(data, indent=2, default=str).encode("utf-8")


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")
