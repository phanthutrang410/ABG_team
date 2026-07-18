"""H08 — dwh → NormalizedStudentRecord / ScoringFeatures read adapter."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.contracts.scoring import ScoringFeatures
from app.dwh.import_gate import ApprovalArtifact
from app.dwh.importer import (
    ATTENDANCE_SOURCE_ID,
    SEMESTER_SOURCE_ID,
    import_attendance,
    import_semester,
)
from app.dwh.migrate import upgrade_head
from app.dwh.read_adapter import (
    ReadAdapterError,
    list_normalized_students,
    require_approved_manifest,
    to_scoring_features,
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
def h08_database_url() -> str:
    base_url = os.environ.get("TEST_DATABASE_URL") or get_settings().database_url
    if not _postgres_available(base_url):
        pytest.fail("Postgres required for H08 tests. Start `docker compose up -d db`.")
    test_name = f"ss_h08_{uuid.uuid4().hex[:10]}"
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
    return sessionmaker(bind=create_engine(url), autoflush=False, autocommit=False)()


def test_attendance_normalized_and_scoring_features(h08_database_url: str) -> None:
    import_attendance(h08_database_url, ensure_schema=False)
    with _session(h08_database_url) as session:
        records = list_normalized_students(session, ATTENDANCE_SOURCE_ID)
        assert len(records) == 460
        sample = next(r for r in records if r.coverage.n_attendance_events >= 12)
        assert sample.coverage.status in ("ok", "partial")
        features = to_scoring_features(sample)
        assert isinstance(features, ScoringFeatures)
        assert features.attendance_rate_window is not None
        assert 0.0 <= features.attendance_rate_window <= 1.0
        dumped = features.model_dump()
        assert "is_dropout_outcome" not in dumped
        assert "advisor_ref" not in dumped


def test_semester_mapping_repair_and_no_cross_join(
    h08_database_url: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Explicit Mode B — decision #27 join must not apply here.
    monkeypatch.setenv("LINKED_NAMESPACE_APPROVAL", "")
    get_settings.cache_clear()

    # Student without advisor → mapping_repair
    payload = [
        {
            "token": "t",
            "student_info": {
                "MSSV": "NOADV001",
                "Trạng thái": "Đang học",
                "Khoa": "CNTT",
                "Ngành": "KTPM",
                "Lớp": "A1",
                "Khóa": "2022",
                "Họ và tên": "Anon",
            },
            "grades": [
                {
                    "Học kỳ": "HK1 (2022-2023)",
                    "Mã lớp": "C1",
                    "TC": "3",
                    "Điểm tổng kết": "8.0",
                },
                {
                    "Học kỳ": "HK2 (2022-2023)",
                    "Mã lớp": "C2",
                    "TC": "3",
                    "Điểm tổng kết": "7.0",
                },
            ],
        }
    ]
    path = tmp_path / "sem.json"
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    path.write_bytes(raw)
    approval = ApprovalArtifact(
        source_id=SEMESTER_SOURCE_ID,
        snapshot_sha256=hashlib.sha256(raw).hexdigest(),
        record_count=1,
        provenance_approved=True,
        schema_version="epu-1",
        extracted_at=_EXTRACTED,
        owner="test",
        usage_rights="mvp",
    )
    import_semester(
        h08_database_url, source_path=path, approval=approval, ensure_schema=False
    )
    import_attendance(h08_database_url, ensure_schema=False)

    with _session(h08_database_url) as session:
        sem = list_normalized_students(session, SEMESTER_SOURCE_ID)
        assert len(sem) == 1
        assert sem[0].mapping_repair is True
        assert sem[0].advisor_ref is None
        # No cross-join: semester record must not absorb attendance events
        assert sem[0].attendance_events == []
        assert "attendance_source_unapproved" in sem[0].coverage.reason_codes
        features = to_scoring_features(sem[0])
        assert features.attendance_rate_window is None
        assert features.coverage.n_attendance_events == 0

        att = list_normalized_students(session, ATTENDANCE_SOURCE_ID)
        assert len(att) == 460
        # Attendance stubs have no term grades from semester
        assert all(r.term_grades == [] for r in att)


def test_unapproved_source_fail_closed(h08_database_url: str) -> None:
    with _session(h08_database_url) as session:
        with pytest.raises(ReadAdapterError) as exc:
            require_approved_manifest(session, SEMESTER_SOURCE_ID)
        assert "source_unapproved" in exc.value.reason_codes
