"""M06 — domain transform + data-quality report tests.

Chứng minh (EPU §2–§4, Data-ML §7): chuẩn hóa deterministic, taxonomy `Trạng
thái`, miền điểm, khóa unique, fail-closed PII/token, reason codes theo nhánh,
không cross-join, và biên `is_dropout_outcome` chỉ ở evaluation. Không nạp dữ
liệu "đã duyệt" vào repo — records semester là pseudonym ephemeral trong test;
nhánh attendance dùng fixture allowlisted H15 sẵn có.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.dwh import models as dwh
from app.ml.domain import (
    GRADE_MAX,
    build_attendance_dataset,
    build_semester_dataset,
    map_academic_status,
    normalize_term_code,
)
from app.ml.domain.models import DomainSourceManifest
from app.ml.domain.transform import PiiFieldError

_EXTRACTED = datetime(2026, 7, 18, tzinfo=timezone.utc)
_REPO_ROOT = Path(__file__).resolve().parents[2]
_ATTENDANCE_DIR = _REPO_ROOT / "data" / "approved" / "attendance"
_ATTENDANCE_FIXTURE = _ATTENDANCE_DIR / "mvp_attendance_over_time.json"


def _semester_manifest(**kw) -> DomainSourceManifest:
    defaults = dict(
        source_id="v59-empty-program-students",
        snapshot_sha256="a" * 64,
        provenance_approved=True,
        schema_version="epu-1",
        record_count=0,
        extracted_at=_EXTRACTED,
    )
    defaults.update(kw)
    return DomainSourceManifest(**defaults)


def _build_semester(records, **manifest_kw):
    return build_semester_dataset(
        records,
        manifest=_semester_manifest(**manifest_kw),
        report_version="m06-semester-1",
        generated_at=_EXTRACTED,
    )


_TWO_TERM_STUDENT = {
    "student_ref": "s-0001",
    "cohort": "K2021",
    "department": "CNTT",
    "program": "KTPM",
    "major": "KTPM",
    "class_code": "KTPM01",
    "status_raw": "Đang học",
    "status_observed_at": "2023-06-30",
    "advisor_ref": "a-01",
    "scope_source": "v59",
    "grades": [
        {"term_code": "HK1 (2022-2023)", "course_ref": "c-001", "credits": 3, "final_grade": 7.5},
        {"term_code": "HK2 (2022-2023)", "course_ref": "c-002", "credits": 3, "final_grade": 6.0},
    ],
}


# --- term_code normalization ----------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("HK1 (2022-2023)", "2022-2023-T1"),
        ("HK2 (2022-2023)", "2022-2023-T2"),
        ("hk3 (2021-2022)", "2021-2022-T3"),
        ("2022-2023-T1", "2022-2023-T1"),
        ("HK1 2022-2023", None),
        ("garbage", None),
        (None, None),
        (123, None),
    ],
)
def test_normalize_term_code(raw, expected):
    assert normalize_term_code(raw) == expected


# --- Trạng thái taxonomy (decision #17) -----------------------------------


@pytest.mark.parametrize(
    "raw,code,outcome",
    [
        ("Thôi học", "thoi_hoc", "true"),
        ("Buộc thôi học", "buoc_thoi_hoc", "true"),
        ("Đang học", "dang_hoc", "false"),
        ("Rút học phí", "rut_hoc_phi", "unknown"),
        ("Bảo lưu", "bao_luu", "unknown"),
        ("Chuyển trường", "other", "unknown"),
        ("", "unknown", "unknown"),
        (None, "unknown", "unknown"),
    ],
)
def test_map_academic_status(raw, code, outcome):
    assert map_academic_status(raw) == (code, outcome)


# --- Semester happy path ---------------------------------------------------


def test_semester_happy_path_builds_all_tables():
    ds = _build_semester([_TWO_TERM_STUDENT])
    assert len(ds.student_dimension) == 1
    assert len(ds.term_grade) == 2
    assert len(ds.academic_status) == 1
    assert len(ds.advisor_assignment) == 1
    assert ds.data_quality_report.row_count == 2
    assert ds.data_quality_report.reject_count == 0
    cov = ds.data_quality_report.term_coverage[0]
    assert cov.n_valid_terms == 2 and cov.n_courses == 2
    assert cov.last_term_code == "2022-2023-T2"
    assert cov.reason_codes == []  # 2 kỳ + outcome=false ⇒ không reason


def test_term_grade_rows_scoped_to_single_source_no_cross_join():
    ds = _build_semester([_TWO_TERM_STUDENT], source_id="v59-empty-program-students")
    all_rows = (
        ds.student_dimension + ds.term_grade + ds.academic_status + ds.advisor_assignment
    )
    assert {r.source_id for r in all_rows} == {"v59-empty-program-students"}


# --- is_dropout_outcome boundary (Data-ML §2.3/§5) ------------------------


def test_dropout_outcome_only_on_academic_status():
    ds = _build_semester([_TWO_TERM_STUDENT])
    # Nhãn evaluation chỉ trên academic_status.
    assert ds.academic_status[0].is_dropout_outcome == "false"
    forbidden = {"is_dropout_outcome", "status_raw", "status_code"}
    for row in ds.student_dimension + ds.term_grade + ds.advisor_assignment:
        assert forbidden.isdisjoint(row.model_dump().keys())


def test_status_unknown_flags_reason_code():
    student = {**_TWO_TERM_STUDENT, "status_raw": "Bảo lưu"}
    ds = _build_semester([student])
    assert ds.academic_status[0].is_dropout_outcome == "unknown"
    assert "status_unknown" in ds.data_quality_report.term_coverage[0].reason_codes


# --- Reject layers ---------------------------------------------------------


@pytest.mark.parametrize("bad_grade", [10.5, -0.1, GRADE_MAX + 1, 100])
def test_grade_out_of_domain_rejected(bad_grade):
    student = {
        "student_ref": "s-1",
        "grades": [{"term_code": "2022-2023-T1", "course_ref": "c-1", "final_grade": bad_grade}],
    }
    ds = _build_semester([student])
    assert ds.term_grade == []
    assert ds.data_quality_report.reject_reasons.get("grade_out_of_domain") == 1


def test_missing_required_field_rejected():
    student = {
        "student_ref": "s-1",
        "grades": [
            {"term_code": "2022-2023-T1", "final_grade": 7.0},  # thiếu course_ref
            {"term_code": "2022-2023-T1", "course_ref": "c-2"},  # thiếu final_grade
        ],
    }
    ds = _build_semester([student])
    assert ds.term_grade == []
    assert ds.data_quality_report.reject_reasons.get("missing_required_field") == 2


def test_invalid_term_code_rejected():
    student = {
        "student_ref": "s-1",
        "grades": [{"term_code": "not-a-term", "course_ref": "c-1", "final_grade": 7.0}],
    }
    ds = _build_semester([student])
    assert ds.data_quality_report.reject_reasons.get("invalid_term_code") == 1


def test_duplicate_key_rejected():
    student = {
        "student_ref": "s-1",
        "grades": [
            {"term_code": "2022-2023-T1", "course_ref": "c-1", "final_grade": 7.0},
            {"term_code": "2022-2023-T1", "course_ref": "c-1", "final_grade": 9.0},
        ],
    }
    ds = _build_semester([student])
    assert len(ds.term_grade) == 1
    assert ds.data_quality_report.reject_reasons.get("duplicate_key") == 1


def test_single_term_reason():
    student = {
        "student_ref": "s-1",
        "status_raw": "Đang học",
        "grades": [{"term_code": "2022-2023-T1", "course_ref": "c-1", "final_grade": 7.0}],
    }
    ds = _build_semester([student])
    assert "single_term" in ds.data_quality_report.term_coverage[0].reason_codes


def test_grade_coverage_insufficient_reason():
    student = {"student_ref": "s-1", "status_raw": "Đang học", "grades": []}
    ds = _build_semester([student])
    cov = ds.data_quality_report.term_coverage[0]
    assert cov.n_valid_terms == 0
    assert "grade_coverage_insufficient" in cov.reason_codes


def test_advisor_missing_tracked_but_row_present():
    student = {**_TWO_TERM_STUDENT, "advisor_ref": None}
    ds = _build_semester([student])
    assert ds.advisor_assignment[0].advisor_ref is None
    assert ds.data_quality_report.missingness["advisor_ref_missing"] == 1


# --- Fail-closed PII/token -------------------------------------------------


@pytest.mark.parametrize(
    "pii_field", ["MSSV", "Họ và tên", "Email", "Số điện thoại", "Ngày sinh", "token"]
)
def test_semester_pii_field_fails_closed(pii_field):
    student = {"student_ref": "s-1", pii_field: "leak", "grades": []}
    with pytest.raises(PiiFieldError):
        _build_semester([student])


def test_nested_pii_field_in_grades_fails_closed():
    student = {
        "student_ref": "s-1",
        "grades": [
            {"term_code": "2022-2023-T1", "course_ref": "c-1", "final_grade": 7.0, "email": "x"}
        ],
    }
    with pytest.raises(PiiFieldError):
        _build_semester([student])


def test_pseudonym_fields_not_flagged_as_pii():
    ds = _build_semester([_TWO_TERM_STUDENT])  # có student_ref + advisor_ref
    assert ds.advisor_assignment[0].advisor_ref == "a-01"


# --- Determinism -----------------------------------------------------------


def test_semester_build_is_deterministic():
    first = _build_semester([_TWO_TERM_STUDENT])
    second = _build_semester([_TWO_TERM_STUDENT])
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


# --- Schema alignment với dwh (H20/H08 consumer) ---------------------------


def test_domain_row_fields_align_with_dwh_columns():
    from app.ml.domain.models import (
        AcademicStatusRow,
        AdvisorAssignmentRow,
        AttendanceEventRow,
        StudentDimensionRow,
        TermGradeRow,
    )

    pairs = [
        (StudentDimensionRow, dwh.StudentDimension),
        (TermGradeRow, dwh.TermGrade),
        (AttendanceEventRow, dwh.AttendanceEvent),
        (AcademicStatusRow, dwh.AcademicStatus),
        (AdvisorAssignmentRow, dwh.AdvisorAssignment),
    ]
    for row_model, orm in pairs:
        row_fields = set(row_model.model_fields)
        orm_cols = {c.name for c in orm.__table__.columns}
        # Mọi field M06 phải là cột dwh (H20 nạp không cần remap).
        assert row_fields <= orm_cols, (row_model.__name__, row_fields - orm_cols)


# --- Attendance branch (Data-ML §2.2) --------------------------------------


def _attendance_manifest(**kw) -> DomainSourceManifest:
    raw = _ATTENDANCE_FIXTURE.read_bytes()
    defaults = dict(
        source_id="mvp-attendance-over-time",
        snapshot_sha256=hashlib.sha256(raw).hexdigest(),
        provenance_approved=True,
        schema_version="epu-1",
        record_count=len(json.loads(raw)["events"]),
        extracted_at=_EXTRACTED,
    )
    defaults.update(kw)
    return DomainSourceManifest(**defaults)


def _build_attendance(payload, **manifest_kw):
    return build_attendance_dataset(
        payload,
        manifest=_attendance_manifest(**manifest_kw),
        report_version="m06-attendance-1",
        generated_at=_EXTRACTED,
    )


def test_attendance_fixture_coverage_and_rates():
    payload = json.loads(_ATTENDANCE_FIXTURE.read_text(encoding="utf-8"))
    ds = _build_attendance(payload)
    assert len(ds.attendance_event) == 7_360
    counts: dict[str, int] = {}
    for event in ds.attendance_event:
        counts[event.student_ref] = counts.get(event.student_ref, 0) + 1
    assert len(counts) == 460
    assert set(counts.values()) == {16}
    assert len(ds.data_quality_report.attendance_coverage) == 460
    assert all(c.trend_eligible for c in ds.data_quality_report.attendance_coverage)
    assert ds.data_quality_report.reason_codes == []


def test_attendance_excused_excluded_from_denominator():
    payload = {
        "source_id": "mvp-attendance-over-time",
        "events": [
            {"student_ref": "s-9", "observed_at": "2026-05-01", "presence_status": "present"},
            {"student_ref": "s-9", "observed_at": "2026-05-08", "presence_status": "present"},
            {"student_ref": "s-9", "observed_at": "2026-05-15", "presence_status": "present"},
            {"student_ref": "s-9", "observed_at": "2026-05-22", "presence_status": "absent",
             "excused": True},
        ],
    }
    ds = _build_attendance(payload)
    cov = ds.data_quality_report.attendance_coverage[0]
    assert cov.n_attendance_events == 4  # đủ mốc
    assert cov.n_counted_events == 3  # excused loại khỏi mẫu số
    assert cov.n_excused == 1
    assert cov.attendance_rate_window == 1.0  # 3 present / 3 counted


def test_attendance_below_min_events_insufficient():
    payload = {
        "source_id": "mvp-attendance-over-time",
        "events": [
            {"student_ref": "s-9", "observed_at": "2026-05-01", "presence_status": "present"},
            {"student_ref": "s-9", "observed_at": "2026-05-08", "presence_status": "present"},
            {"student_ref": "s-9", "observed_at": "2026-05-15", "presence_status": "absent",
             "excused": False},
        ],
    }
    ds = _build_attendance(payload)
    cov = ds.data_quality_report.attendance_coverage[0]
    assert cov.attendance_rate_window is None
    assert "attendance_coverage_insufficient" in cov.reason_codes
    assert "attendance_coverage_insufficient" in ds.data_quality_report.reason_codes


def test_attendance_pii_fails_closed():
    payload = {
        "source_id": "mvp-attendance-over-time",
        "events": [
            {"student_ref": "s-9", "observed_at": "2026-05-01", "presence_status": "present",
             "MSSV": "123"}
        ],
    }
    with pytest.raises(PiiFieldError):
        _build_attendance(payload)


# --- Committed attendance artifacts: no drift (determinism) -----------------


def test_committed_linked_attendance_manifest_matches_payload():
    committed = json.loads(
        (_ATTENDANCE_DIR / "mvp_attendance_source_manifest.json").read_text(encoding="utf-8")
    )
    payload = json.loads(_ATTENDANCE_FIXTURE.read_text(encoding="utf-8"))
    assert committed["snapshot_sha256"] == hashlib.sha256(_ATTENDANCE_FIXTURE.read_bytes()).hexdigest()
    assert committed["record_count"] == len(payload["events"]) == 7_360
    assert committed["n_students"] == len({e["student_ref"] for e in payload["events"]}) == 460
    assert committed["provenance_approved"] is True
    assert committed["grain"] == "session"
    assert committed["linked_semester_source_id"] == "v59-empty-program-students"


def test_committed_linked_attendance_quality_report_matches_manifest():
    manifest = json.loads(
        (_ATTENDANCE_DIR / "mvp_attendance_source_manifest.json").read_text(encoding="utf-8")
    )
    committed = json.loads(
        (_ATTENDANCE_DIR / "mvp_attendance_data_quality_report.json").read_text(encoding="utf-8")
    )
    assert committed["report_version"] == "h15b-linked-1"
    assert committed["row_count"] == manifest["record_count"] == 7_360
    assert committed["n_students"] == manifest["n_students"] == 460
    assert committed["min_events_per_student"] == 16
    assert committed["reject_count"] == 0
