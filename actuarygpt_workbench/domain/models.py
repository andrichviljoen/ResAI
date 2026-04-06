from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FieldMapping(BaseModel):
    origin_col: str
    value_col: str
    development_col: Optional[str] = None
    valuation_col: Optional[str] = None
    grain: str = "annual"
    input_type: str = "cumulative"


class ValidationResult(BaseModel):
    valid: bool
    messages: List[str] = Field(default_factory=list)


class Finding(BaseModel):
    finding_id: str
    category: str
    title: str
    description: str
    evidence: Dict[str, Any]
    materiality: str
    confidence: str
    suggested_action: str


class OverrideAction(BaseModel):
    ratio_key: str
    status: str
    rationale: str = ""


class AuditPack(BaseModel):
    app_run_metadata: Dict[str, Any]
    dataset_info: Dict[str, Any]
    field_mapping: Dict[str, Any]
    validation_results: Dict[str, Any]
    triangle_definition: Dict[str, Any]
    triangle_summary: Dict[str, Any]
    diagnostics: List[Dict[str, Any]]
    selected_factors: Dict[str, Any]
    reserve_outputs: Dict[str, Any]
    user_overrides: Dict[str, Any]
    ai_context: Dict[str, Any]
    generated_commentary: List[Dict[str, Any]]

    @staticmethod
    def default() -> "AuditPack":
        return AuditPack(
            app_run_metadata={"generated_at": datetime.utcnow().isoformat()},
            dataset_info={},
            field_mapping={},
            validation_results={},
            triangle_definition={},
            triangle_summary={},
            diagnostics=[],
            selected_factors={},
            reserve_outputs={},
            user_overrides={},
            ai_context={},
            generated_commentary=[],
        )
