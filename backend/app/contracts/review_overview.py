"""Aggregate review overview for management UI (H02 summary fix).

This contract deliberately separates the approved roster denominator from the
review queue.  It never treats ``case_state=new_signal`` as a weekly delta and
never exposes per-student rows, model scores, advisor mappings, or PII.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.contracts.integration import IntegrationProblem

SummaryState = Literal["ok", "empty", "stale", "error"]
ComparisonStatus = Literal["unavailable"]


class PriorityBandCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    uu_tien_som: int = Field(default=0, ge=0)
    can_ra_soat: int = Field(default=0, ge=0)


class CaseStateCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_signal: int = Field(default=0, ge=0)
    pending_review: int = Field(default=0, ge=0)
    approved_for_follow_up: int = Field(default=0, ge=0)
    dismissed: int = Field(default=0, ge=0)
    assigned: int = Field(default=0, ge=0)
    follow_up_in_progress: int = Field(default=0, ge=0)
    resolved: int = Field(default=0, ge=0)
    monitoring: int = Field(default=0, ge=0)


class CoverageStatusCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: int = Field(default=0, ge=0)
    partial: int = Field(default=0, ge=0)
    insufficient: int = Field(default=0, ge=0)


class ReviewDataStateCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: int = Field(default=0, ge=0)
    partial: int = Field(default=0, ge=0)
    insufficient_data: int = Field(default=0, ge=0)


class ReviewOverviewSummary(BaseModel):
    """Organization-scoped aggregate; no roster or per-case payloads."""

    model_config = ConfigDict(extra="forbid")

    state: SummaryState
    scope: Literal["organization"] = "organization"
    source_id: str = Field(min_length=1)
    dataset_version: Optional[str] = None
    source_extracted_at: Optional[datetime] = None
    generated_at: datetime

    total_students: int = Field(ge=0)
    review_case_count: int = Field(ge=0)
    review_student_count: int = Field(ge=0)
    limited_student_count: int = Field(ge=0)
    limited_review_case_count: int = Field(ge=0)

    priority_band_counts: PriorityBandCounts = Field(default_factory=PriorityBandCounts)
    case_state_counts: CaseStateCounts = Field(default_factory=CaseStateCounts)
    student_coverage_counts: CoverageStatusCounts = Field(default_factory=CoverageStatusCounts)
    review_data_state_counts: ReviewDataStateCounts = Field(default_factory=ReviewDataStateCounts)

    # A workflow state is not a temporal delta. Until a weekly comparison is
    # actually materialized, the API must say so instead of returning zero.
    comparison_status: ComparisonStatus = "unavailable"
    new_since_previous_snapshot: None = None
    problem: Optional[IntegrationProblem] = None

    @model_validator(mode="after")
    def _consistent_counts(self) -> "ReviewOverviewSummary":
        if self.review_case_count > self.total_students:
            raise ValueError("review_case_count không được lớn hơn total_students")
        if self.review_student_count > self.review_case_count:
            raise ValueError("review_student_count không được lớn hơn review_case_count")
        if self.limited_student_count > self.total_students:
            raise ValueError("limited_student_count không được lớn hơn total_students")
        if self.limited_review_case_count > self.review_case_count:
            raise ValueError("limited_review_case_count không được lớn hơn review_case_count")

        priority_total = (
            self.priority_band_counts.uu_tien_som + self.priority_band_counts.can_ra_soat
        )
        if priority_total != self.review_case_count:
            raise ValueError("priority_band_counts phải cộng bằng review_case_count")

        state_total = sum(
            getattr(self.case_state_counts, field) for field in CaseStateCounts.model_fields
        )
        if state_total != self.review_case_count:
            raise ValueError("case_state_counts phải cộng bằng review_case_count")

        coverage_total = (
            self.student_coverage_counts.ok
            + self.student_coverage_counts.partial
            + self.student_coverage_counts.insufficient
        )
        if coverage_total != self.total_students:
            raise ValueError("student_coverage_counts phải cộng bằng total_students")

        review_data_total = (
            self.review_data_state_counts.ok
            + self.review_data_state_counts.partial
            + self.review_data_state_counts.insufficient_data
        )
        if review_data_total != self.review_case_count:
            raise ValueError("review_data_state_counts phải cộng bằng review_case_count")

        if self.state == "empty" and self.total_students != 0:
            raise ValueError("state=empty đòi hỏi total_students=0")
        if self.state == "error":
            if self.total_students != 0 or self.review_case_count != 0:
                raise ValueError("state=error không được mang aggregate")
            if self.problem is None:
                raise ValueError("state=error đòi hỏi problem")
        if self.state == "stale":
            if self.problem is None or self.problem.code != "stale_snapshot":
                raise ValueError("state=stale đòi hỏi stale_snapshot problem")
        if self.state == "ok" and self.problem is not None:
            raise ValueError("state=ok không kèm problem")
        return self
