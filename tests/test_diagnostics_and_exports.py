import json

import pandas as pd

from actuarygpt_workbench.actuarial.diagnostics import generate_findings
from actuarygpt_workbench.actuarial.reserving import deterministic_link_ratios
from actuarygpt_workbench.services.export_service import build_audit_pack, to_json_bytes


def test_diagnostics_structure():
    cum = pd.DataFrame({0: [100, 120], 1: [150, 1000]}, index=["2018", "2019"])
    ldf = deterministic_link_ratios(cum)
    findings = generate_findings(cum, ldf)
    if findings:
        keys = {"finding_id", "category", "title", "description", "evidence", "materiality", "confidence", "suggested_action"}
        assert keys.issubset(findings[0].keys())


def test_export_json_validity():
    state = {
        "dataset_info": {"name": "demo"},
        "mapping": {"origin_col": "origin"},
        "validation_results": {"valid": True},
        "triangle_definition": {},
        "triangle_summary": {},
        "diagnostics": [],
        "selected_factors": {},
        "reserve_outputs": {},
        "user_overrides": {},
        "ai_context": {},
        "ai_history": [],
    }
    pack = build_audit_pack(state)
    raw = to_json_bytes(pack)
    assert json.loads(raw.decode("utf-8"))["dataset_info"]["name"] == "demo"
