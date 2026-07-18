"""H20b/c — transactional attendance + semester import (Postgres)."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.dwh.import_gate import ApprovalArtifact
from app.dwh.importer import (
    ATTENDANCE_APPROVAL,
    ATTENDANCE_SOURCE_ID,
    SEMESTER_APPROVAL,
    SEMESTER_SOURCE_ENV,
    SEMESTER_SOURCE_ID,
    import_attendance,
    import_semester,
    readiness_report,
)
from app.dwh.migrate import upgrade_head
from app.dwh.models import (
    AttendanceEvent,
    SourceManifest,
    StudentDimension,
    TermGrade,
)

_EXTRACTED = datetime(2026, 7, 18, tzinfo=timezone.utc)


def _postgres_available(url: str) -> bool:
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


def _admin_url(database_url: str) -> str:
    parsed = urlparse(database_url)
    return urlunparse(parsed._replace(path="/postgres"))


@pytest.fixture()
def import_database_url() -> str:
    base_url = os.environ.get("TEST_DATABASE_URL") or get_settings().database_url
    if not _postgres_available(base_url):
        pytest.fail(
            "Postgres required for H20 import tests. "
            "Start `docker compose up -d db` then re-run."
        )
    test_name = f"ss_h20_{uuid.uuid4().hex[:10]}"
    admin = create_engine(_admin_url(base_url), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{test_name}"'))
    admin.dispose()
    parsed = urlparse(base_url)
    test_url = urlunparse(parsed._replace(path=f"/{test_name}"))
    upgrade_head(test_url)
    yield test_url
    admin = create_engine(_admin_url(base_url), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :name AND pid <> pg_backend_pid()"
            ),
            {"name": test_name},
        )
        conn.execute(text(f'DROP DATABASE IF EXISTS "{test_name}"'))
    admin.dispose()


def _session(url: str):
    engine = create_engine(url)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def test_attendance_import_happy_and_idempotent(import_database_url: str) -> None:
    first = import_attendance(import_database_url, ensure_schema=False)
    assert first.status == "imported"
    assert first.row_counts["attendance_event"] == 15
    assert first.row_counts["student_dimension"] == 3  # stub refs
    assert first.row_counts["source_manifest"] == 1

    second = import_attendance(import_database_url, ensure_schema=False)
    assert second.status == "idempotent_skip"
    assert second.row_counts["attendance_event"] == 15

    with _session(import_database_url) as session:
        n_events = session.scalar(select(func.count()).select_from(AttendanceEvent))
        n_students = session.scalar(select(func.count()).select_from(StudentDimension))
        assert n_events == 15
        assert n_students == 3
        stubs = session.scalars(select(StudentDimension)).all()
        assert {s.source_id for s in stubs} == {ATTENDANCE_SOURCE_ID}


def test_attendance_gate_reject_leaves_zero_rows(import_database_url: str, tmp_path: Path) -> None:
    # Tamper hash approval vs fixture bytes
    bad = ApprovalArtifact(
        source_id=ATTENDANCE_SOURCE_ID,
        snapshot_sha256="0" * 64,
        record_count=15,
        provenance_approved=True,
        schema_version="epu-1",
        extracted_at=_EXTRACTED,
        owner="test",
        usage_rights="mvp",
    )
    result = import_attendance(
        import_database_url, approval=bad, ensure_schema=False
    )
    assert result.status == "rejected"
    assert "hash_mismatch" in result.reason_codes

    with _session(import_database_url) as session:
        assert session.scalar(select(func.count()).select_from(SourceManifest)) == 0
        assert session.scalar(select(func.count()).select_from(AttendanceEvent)) == 0
        assert session.scalar(select(func.count()).select_from(StudentDimension)) == 0


def test_attendance_unapproved_zero_write(import_database_url: str) -> None:
    bad = ATTENDANCE_APPROVAL.model_copy(update={"provenance_approved": False})
    result = import_attendance(
        import_database_url, approval=bad, ensure_schema=False
    )
    assert result.status == "rejected"
    assert "source_unapproved" in result.reason_codes
    with _session(import_database_url) as session:
        assert session.scalar(select(func.count()).select_from(SourceManifest)) == 0


def _mini_v59_payload() -> list[dict]:
    return [
        {
            "token": "tok-test-not-persisted",
            "total_courses": 2,
            "student_info": {
                "Họ và tên": "Nguyen Van A",
                "MSSV": "TEST0001",
                "Trạng thái": "Đang học",
                "Khoa": "CNTT",
                "Ngành": "KTPM",
                "Chuyên ngành": "KTPM",
                "Lớp": "KTPM01",
                "Khóa": "2022",
                "Cố vấn học tập": "Advisor One",
                "Số ĐT": "0900000000",
            },
            "grades": [
                {
                    "Học kỳ": "HK1 (2022-2023)",
                    "Mã lớp": "CLS001",
                    "Tên môn học": "Toan",
                    "TC": "3",
                    "Điểm tổng kết": "7.5",
                    "Xếp loại": "[B]",
                    "Ghi chú": "",
                },
                {
                    "Học kỳ": "HK2 (2022-2023)",
                    "Mã lớp": "CLS002",
                    "Tên môn học": "Ly",
                    "TC": "3",
                    "Điểm tổng kết": "6.0",
                    "Xếp loại": "[C]",
                    "Ghi chú": "",
                },
            ],
        }
    ]


def test_semester_import_from_tmp_raw(import_database_url: str, tmp_path: Path) -> None:
    payload = _mini_v59_payload()
    path = tmp_path / "semester.json"
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    path.write_bytes(raw)
    sha = hashlib.sha256(raw).hexdigest()
    approval = ApprovalArtifact(
        source_id=SEMESTER_SOURCE_ID,
        snapshot_sha256=sha,
        record_count=1,
        provenance_approved=True,
        schema_version="epu-1",
        extracted_at=_EXTRACTED,
        owner="test-owner",
        usage_rights="mvp-test",
    )
    result = import_semester(
        import_database_url, source_path=path, approval=approval, ensure_schema=False
    )
    assert result.status == "imported"
    assert result.row_counts["student_dimension"] == 1
    assert result.row_counts["term_grade"] == 2
    assert result.row_counts["academic_status"] == 1
    assert result.row_counts["advisor_assignment"] == 1

    # Domain tables must not store raw MSSV / name / phone / token
    with _session(import_database_url) as session:
        student = session.scalars(select(StudentDimension)).one()
        assert student.student_ref.startswith("s-")
        assert "TEST0001" not in student.student_ref
        grades = session.scalars(select(TermGrade)).all()
        assert len(grades) == 2
        assert {g.term_code for g in grades} == {"2022-2023-T1", "2022-2023-T2"}

    # Idempotent re-run
    again = import_semester(
        import_database_url, source_path=path, approval=approval, ensure_schema=False
    )
    assert again.status == "idempotent_skip"


def test_semester_default_domain_package(import_database_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Committed domain package imports without SILENT_SHIELD_SEMESTER_SOURCE_PATH."""
    monkeypatch.delenv(SEMESTER_SOURCE_ENV, raising=False)
    result = import_semester(import_database_url, ensure_schema=False)
    assert result.status == "imported"
    assert result.snapshot_sha256 == SEMESTER_APPROVAL.normalized_sha256
    assert result.row_counts["student_dimension"] == 460
    assert result.row_counts["term_grade"] == 3680
    assert result.row_counts["academic_status"] == 460
    assert result.row_counts["advisor_assignment"] == 460

    again = import_semester(import_database_url, ensure_schema=False)
    assert again.status == "idempotent_skip"

    with _session(import_database_url) as session:
        student = session.scalars(select(StudentDimension)).first()
        assert student is not None
        assert student.student_ref.startswith("s-")
        assert "MSSV" not in (student.student_ref or "")


def test_semester_raw_v59_optional_owner_path(import_database_url: str) -> None:
    """Optional raw V59 adapt path — skip when file missing; uses raw-hash approval."""
    raw_sha = "34a53298df3dafd4d248496e75fbc10d95f997b76d0a7e6566e04ea97c367c66"
    repo_root = Path(__file__).resolve().parents[2]
    candidates = []
    env = os.environ.get(SEMESTER_SOURCE_ENV, "").strip()
    if env:
        candidates.append(Path(env))
    candidates.append(
        repo_root
        / "reference-Learning-Analytics-AI"
        / "backend"
        / "db"
        / "v59-empty-program-students.json"
    )
    live = next((p for p in candidates if p.is_file()), None)
    if live is None:
        pytest.skip(f"BLOCKED → external raw V59 ({SEMESTER_SOURCE_ENV})")

    raw = live.read_bytes()
    if hashlib.sha256(raw).hexdigest() != raw_sha:
        pytest.skip("external raw semester hash does not match M05b provenance")
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, list) or len(payload) != 460:
        pytest.skip("external semester record_count does not match M05b")

    # Raw path must not use package-gate SEMESTER_APPROVAL (different SHA).
    approval = ApprovalArtifact(
        source_id=SEMESTER_SOURCE_ID,
        snapshot_sha256=raw_sha,
        record_count=460,
        provenance_approved=True,
        schema_version="epu-1",
        extracted_at=_EXTRACTED,
        owner="test-raw-owner",
        usage_rights="mvp-raw-optional",
    )
    result = import_semester(
        import_database_url, source_path=live, approval=approval, ensure_schema=False
    )
    assert result.status == "imported"
    assert result.row_counts["student_dimension"] == 460
    assert result.row_counts["term_grade"] > 0


def test_readiness_report_no_pii_keys(import_database_url: str) -> None:
    import_attendance(import_database_url, ensure_schema=False)
    report = readiness_report(import_database_url)
    blob = json.dumps(report, ensure_ascii=False).lower()
    for banned in ("mssv", "họ và tên", "ho va ten", "email", "0900000000", "@"):
        assert banned not in blob
    assert report["sources"][0]["source_id"] == ATTENDANCE_SOURCE_ID
    # Report talks about student_ref as a concept in notes; must not embed values.
    assert "s-1001" not in blob
    assert "s-1002" not in blob
