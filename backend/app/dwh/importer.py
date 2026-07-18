"""H20 transactional importer — approved M06 domain packages → `dwh` tables.

CLI/service only (not a FastAPI public endpoint). Atomic, idempotent, fail-closed.
Attendance stubs `student_dimension` under the attendance `source_id` (no
cross-join to semester students). Spec: 07-mvp-persistence-schema.md §4–5.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, Optional

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.dwh.import_gate import (
    ApprovalArtifact,
    ImportGateResult,
    evaluate_domain_package,
    evaluate_snapshot_bytes,
)
from app.dwh.migrate import upgrade_head
from app.dwh.models import (
    AcademicStatus,
    AdvisorAssignment,
    AttendanceEvent,
    DataQualityReport,
    SourceManifest,
    StudentDimension,
    TermGrade,
)
from app.dwh.semester_adapt import adapt_v59_records
from app.ml.domain import build_attendance_dataset, build_semester_dataset
from app.ml.domain.models import DomainSourceManifest
from app.ml.domain.transform import PiiFieldError

ATTENDANCE_SOURCE_ID = "mvp-attendance-over-time"
SEMESTER_SOURCE_ID = "v59-empty-program-students"
SEMESTER_SOURCE_ENV = "SILENT_SHIELD_SEMESTER_SOURCE_PATH"

# Committed H15 fixture (relative to backend/)
_DEFAULT_ATTENDANCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "attendance"
    / "mvp_attendance_over_time.json"
)

# M05b / H15 approval constants (decision #18) — no PII.
ATTENDANCE_APPROVAL = ApprovalArtifact(
    source_id=ATTENDANCE_SOURCE_ID,
    snapshot_sha256="f65573ad1ec0e11f4093a57d3cf6e947a78ca994aa8d2feeaeabb6a25e2a2106",
    record_count=15,
    provenance_approved=True,
    schema_version="epu-1",
    extracted_at=datetime(2026, 7, 18, tzinfo=timezone.utc),
    owner="Hoàng / Admin kỹ thuật · Silent Shield MVP demo",
    usage_rights="MVP Silent Shield pipeline only; no redistribution; no PII in git",
)

SEMESTER_APPROVAL = ApprovalArtifact(
    source_id=SEMESTER_SOURCE_ID,
    snapshot_sha256="34a53298df3dafd4d248496e75fbc10d95f997b76d0a7e6566e04ea97c367c66",
    record_count=460,
    provenance_approved=True,
    schema_version="epu-1",
    extracted_at=datetime(2026, 7, 18, 0, 5, tzinfo=timezone.utc),
    owner="Hoàng / Admin kỹ thuật · Silent Shield MVP demo",
    usage_rights="MVP Silent Shield pipeline only (M06→H20→scoring); no raw redistribution",
)


@dataclass
class ImportResult:
    status: Literal["imported", "idempotent_skip", "rejected", "skipped"]
    source_id: str
    reason_codes: list[str] = field(default_factory=list)
    row_counts: dict[str, int] = field(default_factory=dict)
    snapshot_sha256: Optional[str] = None
    detail: Optional[str] = None


def _session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine(database_url, pool_pre_ping=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _domain_manifest(approval: ApprovalArtifact) -> DomainSourceManifest:
    return DomainSourceManifest(
        source_id=approval.source_id,
        snapshot_sha256=approval.normalized_sha256,
        provenance_approved=approval.provenance_approved,
        schema_version=approval.schema_version,
        record_count=approval.record_count,
        extracted_at=approval.extracted_at,
    )


def _check_idempotent(session: Session, approval: ApprovalArtifact) -> Optional[ImportResult]:
    existing = session.get(SourceManifest, approval.source_id)
    if existing is None:
        return None
    if existing.snapshot_sha256 == approval.normalized_sha256:
        return ImportResult(
            status="idempotent_skip",
            source_id=approval.source_id,
            snapshot_sha256=existing.snapshot_sha256,
            row_counts=_count_tables(session, approval.source_id),
            detail="same source_id+hash already loaded",
        )
    return ImportResult(
        status="rejected",
        source_id=approval.source_id,
        reason_codes=["snapshot_conflict"],
        snapshot_sha256=existing.snapshot_sha256,
        detail="source_id exists with different snapshot_sha256; refuse silent overwrite",
    )


def _count_tables(session: Session, source_id: str) -> dict[str, int]:
    tables = {
        "source_manifest": SourceManifest,
        "student_dimension": StudentDimension,
        "term_grade": TermGrade,
        "attendance_event": AttendanceEvent,
        "academic_status": AcademicStatus,
        "advisor_assignment": AdvisorAssignment,
        "data_quality_report": DataQualityReport,
    }
    out: dict[str, int] = {}
    for name, model in tables.items():
        out[name] = session.scalar(
            select(func.count()).select_from(model).where(model.source_id == source_id)
        ) or 0
    return out


def _write_manifest(session: Session, approval: ApprovalArtifact) -> None:
    session.add(
        SourceManifest(
            source_id=approval.source_id,
            snapshot_sha256=approval.normalized_sha256,
            provenance_approved=approval.provenance_approved,
            schema_version=approval.schema_version,
            record_count=approval.record_count,
            extracted_at=approval.extracted_at,
        )
    )


def _write_dqr(session: Session, report: Any) -> None:
    dump = report.model_dump(mode="json")
    session.add(
        DataQualityReport(
            source_id=report.source_id,
            report_version=report.report_version,
            generated_at=report.generated_at,
            row_count=report.row_count,
            reject_count=report.reject_count,
            missingness_summary=json.dumps(dump.get("missingness") or {}, ensure_ascii=False),
            term_coverage_summary=json.dumps(
                dump.get("term_coverage") or dump.get("attendance_coverage") or [],
                ensure_ascii=False,
            ),
            freshness_summary=json.dumps(dump.get("freshness") or {}, ensure_ascii=False),
            reason_codes=json.dumps(dump.get("reason_codes") or [], ensure_ascii=False),
        )
    )


def _reject(source_id: str, gate: ImportGateResult, detail: str = "") -> ImportResult:
    return ImportResult(
        status="rejected",
        source_id=source_id,
        reason_codes=list(gate.reason_codes),
        snapshot_sha256=gate.computed_sha256,
        detail=detail or "import gate rejected",
    )


def import_attendance(
    database_url: str,
    *,
    data_path: Optional[Path] = None,
    approval: ApprovalArtifact = ATTENDANCE_APPROVAL,
    ensure_schema: bool = True,
) -> ImportResult:
    """Import H15 attendance fixture into `dwh` (stub students + events + DQR)."""
    path = Path(data_path) if data_path else _DEFAULT_ATTENDANCE_PATH
    if ensure_schema:
        upgrade_head(database_url)

    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        return ImportResult(
            status="rejected",
            source_id=approval.source_id,
            reason_codes=["unreadable_source"],
            detail=str(exc),
        )

    payload = json.loads(raw_bytes.decode("utf-8"))
    events = payload.get("events") if isinstance(payload, dict) else None
    observed = len(events) if isinstance(events, list) else 0
    snap_gate = evaluate_snapshot_bytes(raw_bytes, approval, observed_record_count=observed)
    if not snap_gate.admitted:
        return _reject(approval.source_id, snap_gate)

    try:
        dataset = build_attendance_dataset(
            payload,
            manifest=_domain_manifest(approval),
            report_version="m06-attendance-1",
            generated_at=approval.extracted_at,
        )
    except PiiFieldError as exc:
        return ImportResult(
            status="rejected",
            source_id=approval.source_id,
            reason_codes=["pii_field_present"],
            detail=str(exc),
        )

    domain = {
        "source_manifest": dataset.source_manifest.model_dump(mode="json"),
        "attendance_event": [r.model_dump(mode="json") for r in dataset.attendance_event],
        "data_quality_report": dataset.data_quality_report.model_dump(mode="json"),
    }
    domain_gate = evaluate_domain_package(
        domain, source_id=approval.source_id, role="attendance"
    )
    if not domain_gate.admitted:
        return _reject(approval.source_id, domain_gate)

    factory = _session_factory(database_url)
    with factory() as session:
        conflict = _check_idempotent(session, approval)
        if conflict is not None:
            return conflict
        # End autobegin from the idempotency read before the write unit.
        session.rollback()

        try:
            # Flush in FK order: manifest → stub students → events → DQR.
            _write_manifest(session, approval)
            session.flush()
            stub_refs = sorted({e.student_ref for e in dataset.attendance_event})
            for ref in stub_refs:
                session.add(
                    StudentDimension(
                        source_id=approval.source_id,
                        student_ref=ref,
                        cohort=None,
                        department=None,
                        program=None,
                        major=None,
                        class_code=None,
                    )
                )
            session.flush()
            for row in dataset.attendance_event:
                session.add(
                    AttendanceEvent(
                        source_id=row.source_id,
                        student_ref=row.student_ref,
                        observed_at=row.observed_at,
                        course_ref=row.course_ref or "",
                        presence_status=row.presence_status,
                        excused=row.excused,
                    )
                )
            session.flush()
            _write_dqr(session, dataset.data_quality_report)
            session.commit()
        except Exception:
            session.rollback()
            raise

        return ImportResult(
            status="imported",
            source_id=approval.source_id,
            snapshot_sha256=approval.normalized_sha256,
            row_counts=_count_tables(session, approval.source_id),
        )


def import_semester(
    database_url: str,
    *,
    source_path: Optional[Path] = None,
    approval: Optional[ApprovalArtifact] = None,
    ensure_schema: bool = True,
) -> ImportResult:
    """Import M05b semester snapshot via env path → adapt → M06 → `dwh`."""
    path_str = (
        str(source_path)
        if source_path is not None
        else os.environ.get(SEMESTER_SOURCE_ENV, "").strip()
    )
    if not path_str:
        return ImportResult(
            status="skipped",
            source_id=SEMESTER_SOURCE_ID,
            reason_codes=["semester_source_path_missing"],
            detail=f"set {SEMESTER_SOURCE_ENV} to the approved external V59 JSON",
        )

    path = Path(path_str)
    use_approval = approval or SEMESTER_APPROVAL
    if ensure_schema:
        upgrade_head(database_url)

    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        return ImportResult(
            status="rejected",
            source_id=use_approval.source_id,
            reason_codes=["unreadable_source"],
            detail=str(exc),
        )

    try:
        raw_payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return ImportResult(
            status="rejected",
            source_id=use_approval.source_id,
            reason_codes=["unreadable_source"],
            detail=str(exc),
        )

    if not isinstance(raw_payload, list):
        return ImportResult(
            status="rejected",
            source_id=use_approval.source_id,
            reason_codes=["schema_invalid"],
            detail="semester source must be a JSON array of student records",
        )

    # When caller supplies a test approval, observe count from payload; live M05b
    # uses the fixed approval.record_count (460).
    observed = len(raw_payload)
    snap_gate = evaluate_snapshot_bytes(
        raw_bytes, use_approval, observed_record_count=observed
    )
    if not snap_gate.admitted:
        return _reject(use_approval.source_id, snap_gate)

    records = adapt_v59_records(raw_payload)
    try:
        dataset = build_semester_dataset(
            records,
            manifest=_domain_manifest(use_approval),
            report_version="m06-semester-1",
            generated_at=use_approval.extracted_at,
        )
    except PiiFieldError as exc:
        return ImportResult(
            status="rejected",
            source_id=use_approval.source_id,
            reason_codes=["pii_field_present"],
            detail=str(exc),
        )

    domain = {
        "source_manifest": dataset.source_manifest.model_dump(mode="json"),
        "student_dimension": [r.model_dump(mode="json") for r in dataset.student_dimension],
        "term_grade": [r.model_dump(mode="json") for r in dataset.term_grade],
        "academic_status": [r.model_dump(mode="json") for r in dataset.academic_status],
        "advisor_assignment": [r.model_dump(mode="json") for r in dataset.advisor_assignment],
        "data_quality_report": dataset.data_quality_report.model_dump(mode="json"),
    }
    domain_gate = evaluate_domain_package(
        domain, source_id=use_approval.source_id, role="primary"
    )
    if not domain_gate.admitted:
        return _reject(use_approval.source_id, domain_gate)

    factory = _session_factory(database_url)
    with factory() as session:
        conflict = _check_idempotent(session, use_approval)
        if conflict is not None:
            return conflict
        session.rollback()

        try:
            # Flush in FK order: manifest → students → dependent domain tables → DQR.
            _write_manifest(session, use_approval)
            session.flush()
            for row in dataset.student_dimension:
                session.add(
                    StudentDimension(
                        source_id=row.source_id,
                        student_ref=row.student_ref,
                        cohort=row.cohort,
                        department=row.department,
                        program=row.program,
                        major=row.major,
                        class_code=row.class_code,
                    )
                )
            session.flush()
            for row in dataset.term_grade:
                session.add(
                    TermGrade(
                        source_id=row.source_id,
                        student_ref=row.student_ref,
                        term_code=row.term_code,
                        course_ref=row.course_ref,
                        credits=Decimal(str(row.credits)) if row.credits is not None else None,
                        final_grade=(
                            Decimal(str(row.final_grade))
                            if row.final_grade is not None
                            else None
                        ),
                        grade_status=row.grade_status,
                    )
                )
            for row in dataset.academic_status:
                session.add(
                    AcademicStatus(
                        source_id=row.source_id,
                        student_ref=row.student_ref,
                        status_code=row.status_code,
                        status_observed_at=row.status_observed_at,
                        is_dropout_outcome=row.is_dropout_outcome,
                    )
                )
            for row in dataset.advisor_assignment:
                session.add(
                    AdvisorAssignment(
                        source_id=row.source_id,
                        student_ref=row.student_ref,
                        advisor_ref=row.advisor_ref,
                        scope_source=row.scope_source,
                    )
                )
            session.flush()
            _write_dqr(session, dataset.data_quality_report)
            session.commit()
        except Exception:
            session.rollback()
            raise

        return ImportResult(
            status="imported",
            source_id=use_approval.source_id,
            snapshot_sha256=use_approval.normalized_sha256,
            row_counts=_count_tables(session, use_approval.source_id),
        )


def readiness_report(database_url: str) -> dict[str, Any]:
    """Non-PII readiness summary for operators / handoff evidence."""
    factory = _session_factory(database_url)
    with factory() as session:
        manifests = session.scalars(select(SourceManifest)).all()
        sources: list[dict[str, Any]] = []
        for m in manifests:
            sources.append(
                {
                    "source_id": m.source_id,
                    "snapshot_sha256": m.snapshot_sha256,
                    "record_count": m.record_count,
                    "provenance_approved": m.provenance_approved,
                    "schema_version": m.schema_version,
                    "extracted_at": m.extracted_at.isoformat(),
                    "table_counts": _count_tables(session, m.source_id),
                }
            )
        present = {m.source_id for m in manifests}
        gaps: list[str] = []
        if ATTENDANCE_SOURCE_ID not in present:
            gaps.append("attendance_not_imported")
        if SEMESTER_SOURCE_ID not in present:
            if not os.environ.get(SEMESTER_SOURCE_ENV, "").strip():
                gaps.append("semester_source_path_missing")
            else:
                gaps.append("semester_not_imported")
        return {
            "ready": not gaps,
            "sources": sorted(sources, key=lambda s: s["source_id"]),
            "gaps": gaps,
            "notes": [
                "No student_ref/PII in this report",
                "Attendance and semester snapshots are never cross-joined",
            ],
        }

