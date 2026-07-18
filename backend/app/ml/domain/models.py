"""Pydantic models + constants cho M06 domain transform.

Tên trường khớp cột `dwh` (H19 `app/dwh/models.py`) để H20 nạp không cần remap.
`extra="forbid"` trên mọi model — field lạ (kể cả PII rò rỉ) làm fail-closed
ngay ở tầng validate.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# --- Miền giá trị công bố (EPU §3.2) --------------------------------------
#: Thang điểm 10 chuẩn của EPU. `final_grade` ngoài [GRADE_MIN, GRADE_MAX] bị
#: reject vào `data_quality_report`, không nạp.
GRADE_MIN = 0.0
GRADE_MAX = 10.0

#: Nhãn evaluation nội bộ (decision #17). CHỈ trên `academic_status`.
DropoutOutcome = Literal["true", "false", "unknown"]

#: Lý do reject bản ghi (row-level) → đếm trong `data_quality_report`.
RejectReason = Literal[
    "missing_required_field",
    "invalid_term_code",
    "grade_out_of_domain",
    "duplicate_key",
]

#: Lý do coverage/insufficient (student- hoặc source-level) — Data-ML §3.
CoverageReasonCode = Literal[
    "single_term",
    "grade_coverage_insufficient",
    "attendance_coverage_insufficient",
    "attendance_source_unapproved",
    "status_unknown",
]

#: Ngưỡng tối thiểu nhánh attendance (Data-ML §2.2).
ATTENDANCE_MIN_EVENTS = 4
ATTENDANCE_MIN_TREND_POINTS = 2
#: Ngưỡng tối thiểu trend điểm theo kỳ (Data-ML §2.1 / EPU §3.6).
TERM_MIN_FOR_TREND = 2


class DomainSourceManifest(BaseModel):
    """Provenance của **một** snapshot đã qua gate. Không mang raw path/token/PII.

    Trùng nghĩa `dwh.source_manifest`; `snapshot_sha256` là hash file nguồn đã
    được `evaluate_source` kiểm (M05a).
    """

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1, max_length=128)
    snapshot_sha256: str = Field(min_length=64, max_length=64)
    provenance_approved: bool
    schema_version: str = Field(min_length=1, max_length=64)
    record_count: int = Field(ge=0)
    extracted_at: datetime


class StudentDimensionRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    student_ref: str
    cohort: Optional[str] = None
    department: Optional[str] = None
    program: Optional[str] = None
    major: Optional[str] = None
    class_code: Optional[str] = None


class TermGradeRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    student_ref: str
    term_code: str
    course_ref: str
    credits: Optional[float] = None
    final_grade: Optional[float] = None
    grade_status: Optional[str] = None


class AttendanceEventRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    student_ref: str
    observed_at: datetime
    # Chuỗi rỗng khi không có course grain — giữ khóa unique ổn định (khớp dwh).
    course_ref: str = ""
    presence_status: Optional[str] = None
    excused: Optional[bool] = None


class AcademicStatusRow(BaseModel):
    """Evaluation nội bộ. `is_dropout_outcome` KHÔNG được chiếu vào scoring/public."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    student_ref: str
    status_code: Optional[str] = None
    status_observed_at: Optional[datetime] = None
    is_dropout_outcome: DropoutOutcome = "unknown"


class AdvisorAssignmentRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    student_ref: str
    advisor_ref: Optional[str] = None
    scope_source: Optional[str] = None


class StudentTermCoverage(BaseModel):
    """Coverage/freshness theo `student_ref` (semester). Không PII."""

    model_config = ConfigDict(extra="forbid")

    student_ref: str
    n_valid_terms: int
    n_courses: int
    last_term_code: Optional[str] = None
    reason_codes: List[CoverageReasonCode] = Field(default_factory=list)


class StudentAttendanceCoverage(BaseModel):
    """Coverage nhánh attendance theo `student_ref` (Data-ML §2.2)."""

    model_config = ConfigDict(extra="forbid")

    student_ref: str
    n_attendance_events: int
    n_counted_events: int
    n_excused: int
    attendance_rate_window: Optional[float] = None
    last_attendance_at: Optional[datetime] = None
    trend_eligible: bool = False
    reason_codes: List[CoverageReasonCode] = Field(default_factory=list)


class DataQualityReport(BaseModel):
    """Report phát hành cho mọi snapshot — kể cả khi zero row hợp lệ.

    Cấu trúc hóa (dwh lưu summary dạng Text/JSON). Không chứa field nhận diện
    sinh viên ngoài `student_ref` pseudonym.
    """

    model_config = ConfigDict(extra="forbid")

    source_id: str
    report_version: str
    generated_at: datetime
    row_count: int = Field(ge=0)
    reject_count: int = Field(ge=0)
    reject_reasons: dict = Field(default_factory=dict)
    missingness: dict = Field(default_factory=dict)
    term_coverage: List[StudentTermCoverage] = Field(default_factory=list)
    attendance_coverage: List[StudentAttendanceCoverage] = Field(default_factory=list)
    freshness: dict = Field(default_factory=dict)
    reason_codes: List[CoverageReasonCode] = Field(default_factory=list)


class SemesterDataset(BaseModel):
    """Output nhánh semester: 4 bảng domain + manifest + quality report."""

    model_config = ConfigDict(extra="forbid")

    source_manifest: DomainSourceManifest
    student_dimension: List[StudentDimensionRow] = Field(default_factory=list)
    term_grade: List[TermGradeRow] = Field(default_factory=list)
    academic_status: List[AcademicStatusRow] = Field(default_factory=list)
    advisor_assignment: List[AdvisorAssignmentRow] = Field(default_factory=list)
    data_quality_report: DataQualityReport


class AttendanceDataset(BaseModel):
    """Output nhánh attendance: `attendance_event` + manifest + quality report.

    Nguồn tách biệt semester — KHÔNG cross-join `student_ref` giữa hai snapshot.
    """

    model_config = ConfigDict(extra="forbid")

    source_manifest: DomainSourceManifest
    attendance_event: List[AttendanceEventRow] = Field(default_factory=list)
    data_quality_report: DataQualityReport
