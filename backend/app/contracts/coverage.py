"""Coverage envelope (H06a).

Semantics: docs/04-engineering/08-data-ml-scoring-fairness-contract.md §§1–3.
Default attendance branch: fail-closed with ``attendance_source_unapproved`` until H15.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

CoverageStatus = Literal["ok", "partial", "insufficient"]

#: Machine-readable reason codes from Data-ML §3 — do not invent outside this set.
ReasonCode = Literal[
    "source_unapproved",
    "attendance_source_unapproved",
    "single_term",
    "grade_coverage_insufficient",
    "attendance_coverage_insufficient",
    "status_unknown",
    "no_approved_audit_attribute",
    "insufficient_group_data",
]

ATTENDANCE_SOURCE_UNAPPROVED: ReasonCode = "attendance_source_unapproved"


class Coverage(BaseModel):
    """Coverage/freshness accompanying every ScoringFeatures / ReviewCase projection."""

    model_config = ConfigDict(extra="forbid")

    n_valid_terms: int = Field(ge=0)
    n_courses: int = Field(ge=0)
    n_attendance_events: int = Field(ge=0)
    last_term_code: Optional[str] = None
    last_attendance_at: Optional[datetime] = None
    status: CoverageStatus
    reason_codes: List[ReasonCode] = Field(default_factory=list)

    @model_validator(mode="after")
    def _consistent(self) -> "Coverage":
        if self.status == "insufficient" and not self.reason_codes:
            raise ValueError("coverage status=insufficient phải có ít nhất một reason_code")
        if (
            ATTENDANCE_SOURCE_UNAPPROVED in self.reason_codes
            and self.n_attendance_events != 0
        ):
            raise ValueError(
                "attendance_source_unapproved đòi hỏi n_attendance_events=0 "
                "(không impute / không nạp nguồn chưa duyệt)"
            )
        if ATTENDANCE_SOURCE_UNAPPROVED in self.reason_codes and self.last_attendance_at is not None:
            raise ValueError(
                "attendance_source_unapproved đòi hỏi last_attendance_at=null"
            )
        return self


def attendance_unapproved_defaults(
    *,
    n_valid_terms: int,
    n_courses: int,
    last_term_code: Optional[str] = None,
) -> Coverage:
    """Fail-closed attendance branch until H15 approval (Data-ML §2.2 default).

    Always ``n_attendance_events=0`` and ``attendance_source_unapproved``.
    Term-only (≥2 kỳ) → ``partial``; một kỳ → ``partial`` + ``single_term``;
    không kỳ → ``insufficient`` + ``grade_coverage_insufficient``.
    """
    reasons: List[ReasonCode] = [ATTENDANCE_SOURCE_UNAPPROVED]
    if n_valid_terms <= 0:
        reasons.append("grade_coverage_insufficient")
        status: CoverageStatus = "insufficient"
    elif n_valid_terms == 1:
        reasons.append("single_term")
        status = "partial"
    else:
        status = "partial"

    return Coverage(
        n_valid_terms=n_valid_terms,
        n_courses=n_courses,
        n_attendance_events=0,
        last_term_code=last_term_code,
        last_attendance_at=None,
        status=status,
        reason_codes=reasons,
    )
