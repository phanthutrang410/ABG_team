"""Attendance week rollup — pure bucketing + Postgres integration (H20 pattern)."""

from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from urllib.parse import urlparse, urlunparse

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.dwh.attendance_week_rollup import (
    DEFAULT_ATTENDANCE_SOURCE_ID,
    aggregate_week_bucket,
    bucket_events_by_iso_week,
    iso_week_monday,
    rollup_attendance_weeks,
)
from app.dwh.importer import ATTENDANCE_SOURCE_ID, import_attendance
from app.dwh.migrate import upgrade_head
from app.dwh.models import AttendanceEvent, AttendanceWeek, SourceManifest


def _event(
    *,
    student_ref: str,
    observed_at: datetime,
    presence_status: str | None = "present",
    excused: bool | None = False,
    course_ref: str = "c-test",
) -> SimpleNamespace:
    return SimpleNamespace(
        student_ref=student_ref,
        observed_at=observed_at,
        presence_status=presence_status,
        excused=excused,
        course_ref=course_ref,
    )


# --- Pure unit ---------------------------------------------------------------


def test_iso_week_monday_bucketing() -> None:
    # 2026-07-15 is a Wednesday → Monday 2026-07-13
    wed = date(2026, 7, 15)
    assert wed.weekday() == 2
    assert iso_week_monday(wed) == date(2026, 7, 13)

    mon = datetime(2026, 7, 13, 8, 0, tzinfo=timezone.utc)
    sun = datetime(2026, 7, 19, 23, 0, tzinfo=timezone.utc)
    assert iso_week_monday(mon) == date(2026, 7, 13)
    assert iso_week_monday(sun) == date(2026, 7, 13)
    assert iso_week_monday(sun) + timedelta(days=6) == date(2026, 7, 19)


def test_excused_excluded_from_denominator() -> None:
    week_start = date(2026, 7, 13)
    events = [
        _event(
            student_ref="s-1",
            observed_at=datetime(2026, 7, 14, 8, 0, tzinfo=timezone.utc),
            presence_status="present",
            excused=False,
        ),
        _event(
            student_ref="s-1",
            observed_at=datetime(2026, 7, 15, 8, 0, tzinfo=timezone.utc),
            presence_status="absent",
            excused=False,
        ),
        _event(
            student_ref="s-1",
            observed_at=datetime(2026, 7, 16, 8, 0, tzinfo=timezone.utc),
            presence_status="absent",
            excused=True,
        ),
    ]
    agg = aggregate_week_bucket("s-1", week_start, events)
    assert agg.n_events == 3
    assert agg.n_excused_excluded == 1
    assert agg.n_in_denominator == 2
    assert agg.n_present == 1
    assert agg.n_absent == 1
    assert agg.attendance_rate == Decimal("0.5000")
    assert agg.week_end_date == date(2026, 7, 19)


def test_only_excused_week_rate_is_null() -> None:
    week_start = date(2026, 7, 13)
    events = [
        _event(
            student_ref="s-2",
            observed_at=datetime(2026, 7, 14, 9, 0, tzinfo=timezone.utc),
            presence_status="absent",
            excused=True,
        ),
        _event(
            student_ref="s-2",
            observed_at=datetime(2026, 7, 15, 9, 0, tzinfo=timezone.utc),
            presence_status="present",
            excused=True,
        ),
    ]
    agg = aggregate_week_bucket("s-2", week_start, events)
    assert agg.n_events == 2
    assert agg.n_excused_excluded == 2
    assert agg.n_in_denominator == 0
    assert agg.attendance_rate is None


def test_bucket_events_groups_by_student_and_monday() -> None:
    events = [
        _event(
            student_ref="s-a",
            observed_at=datetime(2026, 7, 14, 8, 0, tzinfo=timezone.utc),
        ),
        _event(
            student_ref="s-a",
            observed_at=datetime(2026, 7, 21, 8, 0, tzinfo=timezone.utc),
        ),
        _event(
            student_ref="s-b",
            observed_at=datetime(2026, 7, 15, 8, 0, tzinfo=timezone.utc),
        ),
    ]
    aggs = bucket_events_by_iso_week(events)
    keys = {(a.student_ref, a.week_start_date) for a in aggs}
    assert keys == {
        ("s-a", date(2026, 7, 13)),
        ("s-a", date(2026, 7, 20)),
        ("s-b", date(2026, 7, 13)),
    }


# --- DB integration ----------------------------------------------------------


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
def rollup_database_url() -> str:
    base_url = os.environ.get("TEST_DATABASE_URL") or get_settings().database_url
    if not _postgres_available(base_url):
        pytest.fail(
            "Postgres required for attendance week rollup tests. "
            "Start `docker compose up -d db` then re-run."
        )
    test_name = f"ss_rollup_{uuid.uuid4().hex[:10]}"
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


def test_rollup_after_import_grain_and_idempotent(rollup_database_url: str) -> None:
    imported = import_attendance(rollup_database_url, ensure_schema=False)
    assert imported.status == "imported"
    assert imported.source_id == ATTENDANCE_SOURCE_ID == DEFAULT_ATTENDANCE_SOURCE_ID

    with _session(rollup_database_url) as session:
        first = rollup_attendance_weeks(session, ATTENDANCE_SOURCE_ID)
        session.commit()
        assert first.status == "rolled_up"
        n_weeks = first.row_counts["attendance_week"]
        assert n_weeks > 0

        rows = session.scalars(select(AttendanceWeek)).all()
        assert len(rows) == n_weeks
        pks = {(r.source_id, r.student_ref, r.week_start_date) for r in rows}
        assert len(pks) == n_weeks
        assert {r.source_id for r in rows} == {ATTENDANCE_SOURCE_ID}
        for r in rows:
            assert r.week_start_date.weekday() == 0  # Monday
            assert r.week_end_date == r.week_start_date + timedelta(days=6)
            if r.n_in_denominator == 0:
                assert r.attendance_rate is None
            else:
                assert r.attendance_rate is not None

        second = rollup_attendance_weeks(session, ATTENDANCE_SOURCE_ID)
        session.commit()
        assert second.status == "rolled_up"
        assert second.row_counts["attendance_week"] == n_weeks
        assert session.scalar(select(func.count()).select_from(AttendanceWeek)) == n_weeks


def test_rollup_only_excused_week_rate_null(rollup_database_url: str) -> None:
    imported = import_attendance(rollup_database_url, ensure_schema=False)
    assert imported.status == "imported"

    # Far-future ISO week so it does not collide with fixture dates.
    week_monday = date(2099, 1, 5)  # Monday
    assert week_monday.weekday() == 0
    student_ref = "s-00518c9485a9"

    with _session(rollup_database_url) as session:
        session.add(
            AttendanceEvent(
                source_id=ATTENDANCE_SOURCE_ID,
                student_ref=student_ref,
                observed_at=datetime(2099, 1, 6, 10, 0, tzinfo=timezone.utc),
                course_ref="c-excused-only-1",
                presence_status="absent",
                excused=True,
            )
        )
        session.add(
            AttendanceEvent(
                source_id=ATTENDANCE_SOURCE_ID,
                student_ref=student_ref,
                observed_at=datetime(2099, 1, 7, 10, 0, tzinfo=timezone.utc),
                course_ref="c-excused-only-2",
                presence_status="present",
                excused=True,
            )
        )
        session.commit()

        result = rollup_attendance_weeks(session, ATTENDANCE_SOURCE_ID)
        session.commit()
        assert result.status == "rolled_up"

        row = session.get(
            AttendanceWeek,
            {
                "source_id": ATTENDANCE_SOURCE_ID,
                "student_ref": student_ref,
                "week_start_date": week_monday,
            },
        )
        assert row is not None
        assert row.n_events == 2
        assert row.n_excused_excluded == 2
        assert row.n_in_denominator == 0
        assert row.attendance_rate is None
        assert row.week_end_date == week_monday + timedelta(days=6)


def test_rollup_rejects_unapproved_manifest(rollup_database_url: str) -> None:
    with _session(rollup_database_url) as session:
        session.add(
            SourceManifest(
                source_id="not-allowlisted-source",
                snapshot_sha256="a" * 64,
                provenance_approved=True,
                schema_version="test",
                record_count=0,
                extracted_at=datetime(2026, 7, 18, tzinfo=timezone.utc),
            )
        )
        session.commit()
        result = rollup_attendance_weeks(session, "not-allowlisted-source")
        assert result.status == "rejected"
        assert "source_unapproved" in result.reason_codes
        assert result.row_counts.get("attendance_week", 0) == 0
