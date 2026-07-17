"""Narrow transition request/response schemas — not the public ReviewCase DTO (H06a)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TransitionRequest(BaseModel):
    action: str = Field(..., description="Process §4 action code")
    actor: str = Field(..., min_length=1)
    actor_kind: str = Field(default="human", description="human | system; agent/llm rejected")
    reason_code: Optional[str] = None
    review_at: Optional[datetime] = None
    advisor_ref: Optional[str] = None
    monitoring_until: Optional[datetime] = None


class TransitionResponse(BaseModel):
    case_id: str
    state: str
    advisor_ref: Optional[str] = None
    review_at: Optional[datetime] = None
    reason_code: Optional[str] = None
    monitoring_until: Optional[datetime] = None
    mapping_repair_queued: bool = False
    updated_at: Optional[datetime] = None


class TransitionErrorBody(BaseModel):
    detail: str
    code: str
    case_id: str
    state: str
    mapping_repair_queued: bool = False


class CaseCreateRequest(BaseModel):
    """Minimal seed for transition tests / system New Signal creation."""

    case_id: str = Field(..., min_length=1)
    state: str = Field(default="new_signal")
    advisor_ref: Optional[str] = None
