"""Narrow transition request/response schemas — not the public ReviewCase DTO (H06a)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TransitionRequest(BaseModel):
    action: str = Field(..., description="Process §4 action code")
    # Optional: ignored unless it matches server-derived identity (spoof → reject).
    actor: Optional[str] = Field(
        default=None,
        description="Must match server trusted actor when provided; never authoritative",
    )
    actor_kind: Optional[str] = Field(
        default=None,
        description="Must match server trusted kind when provided; agent/llm rejected",
    )
    reason_code: Optional[str] = None
    review_at: Optional[datetime] = None
    # Ignored on assign — H03 resolves advisor_ref from H08 only; kept for OpenAPI compat.
    advisor_ref: Optional[str] = None
    monitoring_until: Optional[datetime] = None


class TransitionResponse(BaseModel):
    """Public HTTP projection for /cases — must not leak advisor_ref."""

    case_id: str
    state: str
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
    """Seed-only create (local/dev/test). No advisor_ref on public create."""

    case_id: str = Field(..., min_length=1)
    state: str = Field(default="new_signal")
    # Internal routing identity for H08 assign resolve (never on TransitionResponse).
    student_ref: Optional[str] = None
    source_id: Optional[str] = None
