"""H08b — linked semester↔attendance join (decision #27)."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.dwh.importer import (
    SEMESTER_SOURCE_ID,
    import_attendance,
    import_semester,
)
from app.dwh.migrate import upgrade_head
from app.dwh.read_adapter import (
    linked_namespace_active,
    list_normalized_students,
)
from app.ml.scoring import score_student


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
def linked_db_url() -> str:
    base_url = os.environ.get("TEST_DATABASE_URL") or get_settings().database_url
    if not _postgres_available(base_url):
        pytest.fail("Postgres required. Start `docker compose up -d db`.")
    test_name = f"ss_h08b_{uuid.uuid4().hex[:10]}"
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


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_linked_namespace_active_default():
    assert linked_namespace_active()
    assert linked_namespace_active("approval:mvp-linked-v59-att:v1:acfb7d80dc3a")
    assert not linked_namespace_active("")
    assert not linked_namespace_active("approval:pending-linked-namespace")


def test_semester_joins_attendance_when_approval_active(
    linked_db_url: str, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv(
        "LINKED_NAMESPACE_APPROVAL",
        "approval:mvp-linked-v59-att:v1:acfb7d80dc3a",
    )
    get_settings.cache_clear()
    assert linked_namespace_active()

    import_attendance(linked_db_url, ensure_schema=False)
    import_semester(linked_db_url, ensure_schema=False)

    with _session(linked_db_url) as session:
        records = list_normalized_students(session, SEMESTER_SOURCE_ID)
        assert len(records) == 460
        with_att = [r for r in records if r.coverage.n_attendance_events >= 12]
        assert len(with_att) >= 450
        assert all(
            "attendance_source_unapproved" not in r.coverage.reason_codes for r in with_att
        )
        sample = with_att[0]
        features = score_student(sample)
        assert features.latest_term_gpa is not None
        assert features.attendance_rate_window is not None
        assert features.attendance_trend_slope is not None


def test_mode_b_no_join_when_approval_cleared(
    linked_db_url: str, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("LINKED_NAMESPACE_APPROVAL", "")
    get_settings.cache_clear()
    assert not linked_namespace_active()

    import_attendance(linked_db_url, ensure_schema=False)
    import_semester(linked_db_url, ensure_schema=False)

    with _session(linked_db_url) as session:
        records = list_normalized_students(session, SEMESTER_SOURCE_ID)
        assert len(records) == 460
        assert all(r.coverage.n_attendance_events == 0 for r in records)
        assert all(
            "attendance_source_unapproved" in r.coverage.reason_codes for r in records
        )
        assert all(not r.attendance_events for r in records)


def test_generator_session_grain_and_determinism():
    import json
    from app.ml.mvp_attendance.generate import (
        SESSIONS_PER_STUDENT,
        build_attendance_payload,
    )

    repo = Path(__file__).resolve().parents[2]
    domain = json.loads(
        (repo / "data" / "approved" / "semester" / "domain_package.json").read_text(
            encoding="utf-8"
        )
    )
    a = build_attendance_payload(domain, seed=42)
    b = build_attendance_payload(domain, seed=42)
    assert a == b
    assert "synthetic" not in json.dumps(a).casefold()
    by_ref: dict[str, int] = {}
    for e in a["events"]:
        by_ref[e["student_ref"]] = by_ref.get(e["student_ref"], 0) + 1
        assert e.get("course_ref")
        assert e.get("observed_at")
    assert len(by_ref) == 460
    assert min(by_ref.values()) >= SESSIONS_PER_STUDENT
