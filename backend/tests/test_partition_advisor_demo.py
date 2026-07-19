"""Tests for demo advisor partition overlay (4×115, manifest hash stable)."""

from __future__ import annotations

import os
import uuid
from urllib.parse import urlparse, urlunparse

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.dwh.importer import SEMESTER_SOURCE_ID, import_semester
from app.dwh.migrate import upgrade_head
from app.dwh.models import AdvisorAssignment, SourceManifest
from app.dwh.partition_demo import (
    ADVISOR_REFS,
    CHUNK_SIZE,
    EXPECTED_STUDENTS,
    SCOPE_SOURCE,
    assign_advisor_chunks,
    partition_advisor_assignments,
)


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


@pytest.fixture(scope="module")
def partition_db_url() -> str:
    base_url = os.environ.get("TEST_DATABASE_URL") or get_settings().database_url
    if not _postgres_available(base_url):
        pytest.fail("Postgres required for partition tests")

    test_name = f"ss_part_{uuid.uuid4().hex[:10]}"
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


def test_assign_advisor_chunks_deterministic() -> None:
    refs = [f"s-{i:03d}" for i in range(460)]
    first = assign_advisor_chunks(refs)
    second = assign_advisor_chunks(list(reversed(refs)))
    assert first == second
    assert len(first) == 460
    counts = {ref: 0 for ref in ADVISOR_REFS}
    for advisor in first.values():
        counts[advisor] += 1
    assert all(counts[ref] == CHUNK_SIZE for ref in ADVISOR_REFS)


def test_partition_overlay_four_by_115_preserves_manifest_hash(partition_db_url: str) -> None:
    imported = import_semester(partition_db_url, ensure_schema=False)
    assert imported.status in ("imported", "idempotent_skip")

    engine = create_engine(partition_db_url, pool_pre_ping=True)
    try:
        with Session(engine) as session:
            before = session.get(SourceManifest, SEMESTER_SOURCE_ID)
            assert before is not None
            sha_before = before.snapshot_sha256

            result = partition_advisor_assignments(session)
            session.commit()
            assert result.status == "partitioned"
            assert result.total_students == EXPECTED_STUDENTS
            assert result.manifest_sha256 == sha_before
            assert all(result.counts_by_advisor[ref] == CHUNK_SIZE for ref in ADVISOR_REFS)

            after = session.get(SourceManifest, SEMESTER_SOURCE_ID)
            assert after is not None
            assert after.snapshot_sha256 == sha_before

            rows = session.scalars(
                select(AdvisorAssignment).where(AdvisorAssignment.source_id == SEMESTER_SOURCE_ID)
            ).all()
            assert len(rows) == EXPECTED_STUDENTS
            assert all(r.scope_source == SCOPE_SOURCE for r in rows)
            assert set(r.advisor_ref for r in rows) == set(ADVISOR_REFS)

            # Idempotent re-run
            again = partition_advisor_assignments(session)
            session.commit()
            assert again.status == "partitioned"
            assert again.counts_by_advisor == result.counts_by_advisor
            assert session.get(SourceManifest, SEMESTER_SOURCE_ID).snapshot_sha256 == sha_before
    finally:
        engine.dispose()
