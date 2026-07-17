"""Public ReviewCase safe projection (H06a).

Semantics: Data-ML §§1–4 + architecture §3 ReviewCase.
Public MUST NOT include model_score, PII, is_dropout_outcome, audit group attrs, advisor_ref.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.contracts.coverage import Coverage

#: Process §4.1 API state codes — public projection mirrors case workflow state.
CaseState = Literal[
    "new_signal",
    "pending_review",
    "approved_for_follow_up",
    "dismissed",
    "assigned",
    "follow_up_in_progress",
    "resolved",
    "monitoring",
]

#: Data-ML §4 band mapping (public). No raw score.
ReviewPriorityBand = Literal["uu_tien_som", "can_ra_soat"]

DataState = Literal["ok", "partial", "insufficient_data"]


class ContributingFactor(BaseModel):
    """Machine-readable factor + evidence refs — no weights, no Vietnamese copy (H12a)."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    evidence_refs: List[str] = Field(default_factory=list)


class ReviewCase(BaseModel):
    """Safe public projection for UI / agent context (not TransitionResponse)."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    student_ref: str = Field(min_length=1, description="Pseudonym only")
    case_state: CaseState
    review_priority_band: ReviewPriorityBand
    contributing_factors: List[ContributingFactor] = Field(default_factory=list)
    coverage: Coverage
    data_state: DataState
    limitations: List[str] = Field(
        default_factory=list,
        description="Machine codes / copy keys for UI (vd. attendance_source_unapproved)",
    )
    dataset_version: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    threshold_config_version: str = Field(min_length=1)
    calculated_at: datetime

    @model_validator(mode="after")
    def _align_data_state_with_coverage(self) -> "ReviewCase":
        if self.coverage.status == "insufficient" and self.data_state != "insufficient_data":
            raise ValueError(
                "coverage.status=insufficient đòi hỏi data_state=insufficient_data"
            )
        if self.coverage.status == "partial" and self.data_state == "ok":
            raise ValueError("coverage.status=partial không được data_state=ok")
        return self
