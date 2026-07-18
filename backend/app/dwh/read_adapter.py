"""H08 — read adapter: approved `dwh` snapshot → NormalizedStudentRecord / ScoringFeatures.

Fail-closed on missing/unapproved provenance. Does not project `is_dropout_outcome`
into ScoringFeatures. Default Mode B: no semester↔attendance cross-join.
Decision #27: when ``linked_namespace_approval`` is active, primary semester
records may attach attendance events from ``mvp-attendance-over-time`` by
exact ``student_ref`` (no fuzzy match).
Missing ``advisor_ref`` ⇒ ``mapping_repair=True`` (routing stop for H03).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.contracts.coverage import (
    Coverage,
    CoverageStatus,
    ReasonCode,
    attendance_unapproved_defaults,
)
from app.contracts.normalized import (
    NormalizedAttendanceEvent,
    NormalizedStudentRecord,
    NormalizedTermGrade,
)
from app.contracts.scoring import ScoringFeatures
from app.dwh.models import (
    AdvisorAssignment,
    AttendanceEvent,
    SourceManifest,
    StudentDimension,
    TermGrade,
)
from app.ml.domain.models import ATTENDANCE_MIN_EVENTS, TERM_MIN_FOR_TREND
from app.ml.source_gate.gate import SOURCE_ALLOWLIST

DEFAULT_MODEL_VERSION = "h08-features-0.1-passthrough"
DEFAULT_THRESHOLD_VERSION = "thr-epu-0.1-uncalibrated"

#: Attendance source paired with V59-empty under decision #27.
LINKED_ATTENDANCE_SOURCE_ID = "mvp-attendance-over-time"
LINKED_SEMESTER_SOURCE_ID = "v59-empty-program-students"
LINKED_APPROVAL_PREFIX = "approval:mvp-linked-v59-att:v1:"


def linked_namespace_active(handle: Optional[str] = None) -> bool:
    """True when Settings (or explicit handle) enables MVP linked join."""
    raw = (handle if handle is not None else get_settings().linked_namespace_approval) or ""
    text = raw.strip()
    return bool(text.startswith(LINKED_APPROVAL_PREFIX) and len(text) > len(LINKED_APPROVAL_PREFIX))


class ReadAdapterError(Exception):
    """Fail-closed read — caller must treat as insufficient_data / no rows."""

    def __init__(self, reason_codes: list[str], detail: str = ""):
        self.reason_codes = reason_codes
        self.detail = detail
        super().__init__(detail or ",".join(reason_codes))


def dataset_version(manifest: SourceManifest) -> str:
    short = manifest.snapshot_sha256[:8]
    return f"{manifest.source_id}:{short}:{manifest.schema_version}"


def require_approved_manifest(session: Session, source_id: str) -> SourceManifest:
    manifest = session.get(SourceManifest, source_id)
    if manifest is None:
        raise ReadAdapterError(["source_unapproved"], f"no source_manifest for {source_id}")
    if not manifest.provenance_approved:
        raise ReadAdapterError(["source_unapproved"], f"provenance not approved for {source_id}")
    if source_id not in SOURCE_ALLOWLIST:
        raise ReadAdapterError(["source_unapproved"], f"source_id not allowlisted: {source_id}")
    return manifest


def _term_coverage(
    grades: List[TermGrade],
) -> tuple[int, int, Optional[str], list[ReasonCode]]:
    terms = sorted({g.term_code for g in grades if g.final_grade is not None})
    n_courses = sum(1 for g in grades if g.final_grade is not None)
    last = terms[-1] if terms else None
    reasons: list[ReasonCode] = []
    if n_courses == 0:
        reasons.append("grade_coverage_insufficient")
    elif len(terms) < TERM_MIN_FOR_TREND:
        reasons.append("single_term")
    return len(terms), n_courses, last, reasons


def _attendance_coverage(
    events: List[AttendanceEvent],
) -> tuple[int, Optional[datetime], Optional[float], list[ReasonCode]]:
    valid = [e for e in events if e.presence_status is not None]
    counted = [e for e in valid if e.excused is not True]
    last = max((e.observed_at for e in events), default=None)
    reasons: list[ReasonCode] = []
    rate: Optional[float] = None
    if len(valid) >= ATTENDANCE_MIN_EVENTS and counted:
        n_present = sum(1 for e in counted if e.presence_status == "present")
        rate = round(n_present / len(counted), 6)
    elif events:
        reasons.append("attendance_coverage_insufficient")
    else:
        reasons.append("attendance_coverage_insufficient")
    return len(valid), last, rate, reasons


def _coverage_for_role(
    role: str,
    *,
    n_valid_terms: int,
    n_courses: int,
    last_term_code: Optional[str],
    term_reasons: list[ReasonCode],
    n_attendance_events: int,
    last_attendance_at: Optional[datetime],
    attendance_reasons: list[ReasonCode],
) -> Coverage:
    if role == "attendance":
        reasons: list[ReasonCode] = list(attendance_reasons)
        if n_courses == 0:
            reasons.append("grade_coverage_insufficient")
        # Dedup
        deduped: list[ReasonCode] = []
        for code in reasons:
            if code not in deduped:
                deduped.append(code)
        if n_attendance_events >= ATTENDANCE_MIN_EVENTS and "attendance_coverage_insufficient" not in deduped:
            status: CoverageStatus = "partial" if n_valid_terms == 0 else "ok"
        elif n_attendance_events > 0:
            status = "partial"
        else:
            status = "insufficient"
        if status == "insufficient" and not deduped:
            deduped.append("attendance_coverage_insufficient")
        return Coverage(
            n_valid_terms=n_valid_terms,
            n_courses=n_courses,
            n_attendance_events=n_attendance_events,
            last_term_code=last_term_code,
            last_attendance_at=last_attendance_at,
            status=status,
            reason_codes=deduped,
        )

    # Semester / primary: do not join attendance source — fail-closed attendance branch.
    base = attendance_unapproved_defaults(
        n_valid_terms=n_valid_terms,
        n_courses=n_courses,
        last_term_code=last_term_code,
    )
    extra = [r for r in term_reasons if r not in base.reason_codes]
    return Coverage(
        n_valid_terms=base.n_valid_terms,
        n_courses=base.n_courses,
        n_attendance_events=0,
        last_term_code=base.last_term_code,
        last_attendance_at=None,
        status=base.status,
        reason_codes=list(base.reason_codes) + extra,
    )


def _coverage_linked_primary(
    *,
    n_valid_terms: int,
    n_courses: int,
    last_term_code: Optional[str],
    term_reasons: list[ReasonCode],
    n_attendance_events: int,
    last_attendance_at: Optional[datetime],
    attendance_reasons: list[ReasonCode],
) -> Coverage:
    """Coverage for semester primary after decision #27 attendance join."""
    reasons: list[ReasonCode] = list(term_reasons)
    for code in attendance_reasons:
        if code not in reasons:
            reasons.append(code)

    grade_ready = n_valid_terms >= TERM_MIN_FOR_TREND
    att_ready = n_attendance_events >= ATTENDANCE_MIN_EVENTS
    if grade_ready and att_ready:
        status: CoverageStatus = "ok"
    elif n_valid_terms == 0 and n_attendance_events == 0:
        status = "insufficient"
        if "grade_coverage_insufficient" not in reasons:
            reasons.append("grade_coverage_insufficient")
        if "attendance_coverage_insufficient" not in reasons:
            reasons.append("attendance_coverage_insufficient")
    else:
        status = "partial"
        if 0 < n_valid_terms < TERM_MIN_FOR_TREND and "single_term" not in reasons:
            reasons.append("single_term")
        if 0 < n_attendance_events < ATTENDANCE_MIN_EVENTS and (
            "attendance_coverage_insufficient" not in reasons
        ):
            reasons.append("attendance_coverage_insufficient")

    # Dedup preserve order
    seen: set[str] = set()
    deduped: list[ReasonCode] = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            deduped.append(r)

    return Coverage(
        n_valid_terms=n_valid_terms,
        n_courses=n_courses,
        n_attendance_events=n_attendance_events,
        last_term_code=last_term_code,
        last_attendance_at=last_attendance_at,
        status=status,
        reason_codes=deduped,
    )


def list_normalized_students(session: Session, source_id: str) -> List[NormalizedStudentRecord]:
    """Load all students for one approved snapshot. Empty list if no students."""
    manifest = require_approved_manifest(session, source_id)
    role = SOURCE_ALLOWLIST[source_id]
    version = dataset_version(manifest)
    join_attendance = (
        role == "primary"
        and source_id == LINKED_SEMESTER_SOURCE_ID
        and linked_namespace_active()
    )

    students = session.scalars(
        select(StudentDimension)
        .where(StudentDimension.source_id == source_id)
        .order_by(StudentDimension.student_ref)
    ).all()

    grades_by_ref: dict[str, list[TermGrade]] = {}
    for g in session.scalars(
        select(TermGrade).where(TermGrade.source_id == source_id)
    ).all():
        grades_by_ref.setdefault(g.student_ref, []).append(g)

    events_by_ref: dict[str, list[AttendanceEvent]] = {}
    event_source = LINKED_ATTENDANCE_SOURCE_ID if join_attendance else source_id
    if join_attendance:
        # Exact student_ref match only — require attendance manifest approved.
        try:
            require_approved_manifest(session, LINKED_ATTENDANCE_SOURCE_ID)
        except ReadAdapterError:
            join_attendance = False
            event_source = source_id
    if join_attendance or role == "attendance":
        for e in session.scalars(
            select(AttendanceEvent).where(AttendanceEvent.source_id == event_source)
        ).all():
            events_by_ref.setdefault(e.student_ref, []).append(e)

    advisors: dict[str, Optional[str]] = {}
    for a in session.scalars(
        select(AdvisorAssignment).where(AdvisorAssignment.source_id == source_id)
    ).all():
        advisors[a.student_ref] = a.advisor_ref

    records: List[NormalizedStudentRecord] = []
    for student in students:
        grades = sorted(
            grades_by_ref.get(student.student_ref, []),
            key=lambda r: (r.term_code, r.course_ref),
        )
        events = sorted(
            events_by_ref.get(student.student_ref, []),
            key=lambda r: (r.observed_at.isoformat(), r.course_ref),
        )
        n_terms, n_courses, last_term, term_reasons = _term_coverage(grades)
        n_att, last_att, _rate, att_reasons = _attendance_coverage(events)

        if join_attendance and role == "primary":
            coverage = _coverage_linked_primary(
                n_valid_terms=n_terms,
                n_courses=n_courses,
                last_term_code=last_term,
                term_reasons=term_reasons,
                n_attendance_events=n_att,
                last_attendance_at=last_att,
                attendance_reasons=att_reasons,
            )
        else:
            coverage = _coverage_for_role(
                role,
                n_valid_terms=n_terms,
                n_courses=n_courses,
                last_term_code=last_term,
                term_reasons=term_reasons,
                n_attendance_events=n_att if role == "attendance" else 0,
                last_attendance_at=last_att if role == "attendance" else None,
                attendance_reasons=att_reasons,
            )
            if role == "primary":
                events = []  # Mode B: never attach foreign attendance rows

        advisor_ref = advisors.get(student.student_ref)
        mapping_repair = role == "primary" and not advisor_ref
        records.append(
            NormalizedStudentRecord(
                student_ref=student.student_ref,
                source_id=source_id,
                dataset_version=version,
                schema_version=manifest.schema_version,
                snapshot_sha256=manifest.snapshot_sha256,
                provenance_approved=manifest.provenance_approved,
                cohort=student.cohort,
                department=student.department,
                program=student.program,
                major=student.major,
                class_code=student.class_code,
                term_grades=[
                    NormalizedTermGrade(
                        term_code=g.term_code,
                        course_ref=g.course_ref,
                        credits=float(g.credits) if g.credits is not None else None,
                        final_grade=float(g.final_grade) if g.final_grade is not None else None,
                        grade_status=g.grade_status,
                    )
                    for g in grades
                ],
                attendance_events=[
                    NormalizedAttendanceEvent(
                        observed_at=e.observed_at,
                        course_ref=e.course_ref or "",
                        presence_status=e.presence_status,
                        excused=e.excused,
                    )
                    for e in events
                ],
                advisor_ref=advisor_ref,
                mapping_repair=mapping_repair,
                coverage=coverage,
            )
        )
    return records


def get_normalized_student(
    session: Session,
    source_id: str,
    student_ref: str,
) -> Optional[NormalizedStudentRecord]:
    """Lookup one student in an approved snapshot; None if absent."""
    ref = (student_ref or "").strip()
    if not ref:
        return None
    for record in list_normalized_students(session, source_id):
        if record.student_ref == ref:
            return record
    return None


def to_scoring_features(
    record: NormalizedStudentRecord,
    *,
    model_version: str = DEFAULT_MODEL_VERSION,
    threshold_config_version: str = DEFAULT_THRESHOLD_VERSION,
    calculated_at: Optional[datetime] = None,
    latest_term_gpa: Optional[float] = None,
    grade_trend_slope: Optional[float] = None,
    grade_volatility: Optional[float] = None,
    failed_credits: Optional[float] = None,
    attendance_rate_window: Optional[float] = None,
    attendance_trend_slope: Optional[float] = None,
) -> ScoringFeatures:
    """Project a normalized record to ScoringFeatures (no outcome / advisor / PII).

    Slope/rate fields default to null — M02 fills estimator outputs. When the
    record is from the attendance source and rate is computable, H08 may pass
    ``attendance_rate_window`` explicitly.
    """
    if not record.provenance_approved:
        raise ReadAdapterError(["source_unapproved"], "refusing unapproved record")

    rate = attendance_rate_window
    if rate is None and SOURCE_ALLOWLIST.get(record.source_id) == "attendance":
        # Recompute rate from events on the same source only.
        valid = [e for e in record.attendance_events if e.presence_status is not None]
        counted = [e for e in valid if e.excused is not True]
        if len(valid) >= ATTENDANCE_MIN_EVENTS and counted:
            n_present = sum(1 for e in counted if e.presence_status == "present")
            rate = round(n_present / len(counted), 6)

    return ScoringFeatures(
        dataset_version=record.dataset_version,
        model_version=model_version,
        threshold_config_version=threshold_config_version,
        calculated_at=calculated_at or datetime.now(timezone.utc),
        student_ref=record.student_ref,
        latest_term_gpa=latest_term_gpa,
        grade_trend_slope=grade_trend_slope,
        grade_volatility=grade_volatility,
        failed_credits=failed_credits,
        attendance_rate_window=rate,
        attendance_trend_slope=attendance_trend_slope,
        coverage=record.coverage,
    )
