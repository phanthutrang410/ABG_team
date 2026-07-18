"""NormalizedStudentRecord — H08 internal DTO (not public ReviewCase).

Carries pseudonymous domain rows + coverage/provenance for M02/H03.
Never includes is_dropout_outcome, PII, or audit group attributes.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.contracts.coverage import Coverage


class NormalizedTermGrade(BaseModel):
    model_config = ConfigDict(extra="forbid")

    term_code: str
    course_ref: str
    credits: Optional[float] = None
    final_grade: Optional[float] = None
    grade_status: Optional[str] = None


class NormalizedAttendanceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observed_at: datetime
    course_ref: str = ""
    presence_status: Optional[str] = None
    excused: Optional[bool] = None


class NormalizedStudentRecord(BaseModel):
    """One student scoped to a single approved `source_id` (no cross-source join)."""

    model_config = ConfigDict(extra="forbid")

    student_ref: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    snapshot_sha256: str = Field(min_length=64, max_length=64)
    provenance_approved: bool

    cohort: Optional[str] = None
    department: Optional[str] = None
    program: Optional[str] = None
    major: Optional[str] = None
    class_code: Optional[str] = None

    term_grades: List[NormalizedTermGrade] = Field(default_factory=list)
    attendance_events: List[NormalizedAttendanceEvent] = Field(default_factory=list)

    # Routing-only (H03). Never copied into ScoringFeatures.
    advisor_ref: Optional[str] = None
    mapping_repair: bool = False

    coverage: Coverage
