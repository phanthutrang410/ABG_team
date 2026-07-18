"""M06 — deterministic domain-table transform + data-quality report.

Reads a **gate-admitted** (M05a/`evaluate_source`), M05b/H15-approved source and
emits the normalized domain tables + `source_manifest` + `data_quality_report`
described in the EPU contract §2–§4 and Data-ML §7. Pseudonymous only; no PII,
no token, no cross-source join. Column names match the `dwh` persistence schema
(H19 `app/dwh/models.py`) so H20 can load the output without remapping.

Two independent source snapshots (never joined by identity — EPU §2):

* semester grades (`v59-empty-program-students`,
  `data/approved/semester/domain_package.json`) → `build_semester_dataset`
* attendance-over-time (`mvp-attendance-over-time`,
  `data/approved/attendance/`) → `build_attendance_dataset`

`is_dropout_outcome` is carried **only** on `academic_status` for internal
M02/M03 evaluation — it never appears in scoring features / public case / agent
context (Data-ML §2.3, §5).
"""

from __future__ import annotations

from app.ml.domain.attendance import build_attendance_dataset
from app.ml.domain.models import (
    GRADE_MAX,
    GRADE_MIN,
    AcademicStatusRow,
    AdvisorAssignmentRow,
    AttendanceDataset,
    AttendanceEventRow,
    DataQualityReport,
    DomainSourceManifest,
    DropoutOutcome,
    RejectReason,
    SemesterDataset,
    StudentDimensionRow,
    TermGradeRow,
)
from app.ml.domain.transform import (
    build_semester_dataset,
    map_academic_status,
    normalize_term_code,
)

__all__ = [
    "GRADE_MAX",
    "GRADE_MIN",
    "AcademicStatusRow",
    "AdvisorAssignmentRow",
    "AttendanceDataset",
    "AttendanceEventRow",
    "DataQualityReport",
    "DomainSourceManifest",
    "DropoutOutcome",
    "RejectReason",
    "SemesterDataset",
    "StudentDimensionRow",
    "TermGradeRow",
    "build_attendance_dataset",
    "build_semester_dataset",
    "map_academic_status",
    "normalize_term_code",
]
