"""M06 attendance transform — `mvp-attendance-over-time` → `attendance_event`.

Nguồn allowlisted H15 (decision #18), TÁCH biệt snapshot semester: không
cross-join `student_ref` giữa hai nguồn. Cửa sổ/mốc theo Data-ML §2.2:

* `attendance_rate_window` hợp lệ khi ≥4 mốc `observed_at` có `presence_status`
  khác null; `excused=true` **loại khỏi mẫu số** rate.
* `attendance_trend_slope` chỉ khi ≥2 mốc phân biệt sau khi rate gate đạt.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.ml.domain.models import (
    ATTENDANCE_MIN_EVENTS,
    ATTENDANCE_MIN_TREND_POINTS,
    AttendanceDataset,
    AttendanceEventRow,
    CoverageReasonCode,
    DataQualityReport,
    DomainSourceManifest,
    StudentAttendanceCoverage,
)
from app.ml.domain.transform import PiiFieldError, _forbidden_field_names, _iso


def build_attendance_dataset(
    payload: dict,
    *,
    manifest: DomainSourceManifest,
    report_version: str,
    generated_at: datetime,
) -> AttendanceDataset:
    """`{source_id, events:[...]}` → `attendance_event` + coverage + quality report.

    Fail-closed: field PII/token ⇒ ``PiiFieldError``. Event thiếu `student_ref` /
    `observed_at` không parse được ⇒ reject vào report. Deterministic: rows sắp
    theo `(student_ref, observed_at, course_ref)`.
    """
    forbidden = _forbidden_field_names(payload)
    if forbidden:
        raise PiiFieldError(f"forbidden PII/token fields in attendance input: {sorted(set(forbidden))}")

    source_id = manifest.source_id
    events = payload.get("events", []) or []

    rows: Dict[Tuple[str, str, str], AttendanceEventRow] = {}
    reject_reasons: Dict[str, int] = {}
    reject_count = 0

    for event in events:
        student_ref = event.get("student_ref")
        observed_at = _iso(event.get("observed_at"))
        if not isinstance(student_ref, str) or not student_ref or observed_at is None:
            reject_count += 1
            reject_reasons["missing_required_field"] = (
                reject_reasons.get("missing_required_field", 0) + 1
            )
            continue
        course_ref = event.get("course_ref") if isinstance(event.get("course_ref"), str) else ""
        excused = event.get("excused")
        key = (student_ref, observed_at.isoformat(), course_ref)
        if key in rows:
            reject_count += 1
            reject_reasons["duplicate_key"] = reject_reasons.get("duplicate_key", 0) + 1
            continue
        rows[key] = AttendanceEventRow(
            source_id=source_id,
            student_ref=student_ref,
            observed_at=observed_at,
            course_ref=course_ref,
            presence_status=event.get("presence_status")
            if isinstance(event.get("presence_status"), str) else None,
            excused=excused if isinstance(excused, bool) else None,
        )

    ordered_keys = sorted(rows)
    ordered_rows = [rows[k] for k in ordered_keys]

    # --- Coverage theo student (Data-ML §2.2) -----------------------------
    coverage: List[StudentAttendanceCoverage] = []
    source_reasons: set = set()
    last_overall: Optional[datetime] = None
    for student_ref in sorted({r.student_ref for r in ordered_rows}):
        student_rows = [r for r in ordered_rows if r.student_ref == student_ref]
        valid = [r for r in student_rows if r.presence_status is not None]
        counted = [r for r in valid if r.excused is not True]  # excused loại khỏi mẫu số
        n_present = sum(1 for r in counted if r.presence_status == "present")
        distinct_points = {r.observed_at for r in valid}
        last_at = max((r.observed_at for r in student_rows), default=None)
        if last_at is not None and (last_overall is None or last_at > last_overall):
            last_overall = last_at

        reasons: List[CoverageReasonCode] = []
        rate: Optional[float] = None
        trend_eligible = False
        if len(valid) >= ATTENDANCE_MIN_EVENTS and counted:
            rate = round(n_present / len(counted), 6)
            trend_eligible = len(distinct_points) >= ATTENDANCE_MIN_TREND_POINTS
        else:
            reasons.append("attendance_coverage_insufficient")
        source_reasons.update(reasons)
        coverage.append(
            StudentAttendanceCoverage(
                student_ref=student_ref,
                n_attendance_events=len(valid),
                n_counted_events=len(counted),
                n_excused=sum(1 for r in valid if r.excused is True),
                attendance_rate_window=rate,
                last_attendance_at=last_at,
                trend_eligible=trend_eligible,
                reason_codes=reasons,
            )
        )

    report = DataQualityReport(
        source_id=source_id,
        report_version=report_version,
        generated_at=generated_at,
        row_count=len(ordered_rows),
        reject_count=reject_count,
        reject_reasons=dict(sorted(reject_reasons.items())),
        missingness={
            "presence_status_null": sum(1 for r in ordered_rows if r.presence_status is None),
            "excused_null": sum(1 for r in ordered_rows if r.excused is None),
        },
        attendance_coverage=coverage,
        freshness={
            "last_attendance_at": last_overall.isoformat() if last_overall else None,
            "n_students": len({r.student_ref for r in ordered_rows}),
        },
        reason_codes=sorted(source_reasons),
    )

    return AttendanceDataset(
        source_manifest=manifest,
        attendance_event=ordered_rows,
        data_quality_report=report,
    )
