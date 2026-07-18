"""H19 — empty `dwh` migrate repeatability and schema shape tests."""

from __future__ import annotations

import os
import uuid
from urllib.parse import urlparse, urlunparse

import pytest
from sqlalchemy import create_engine, inspect, text

from app.config import get_settings
from app.dwh.migrate import HEAD_REVISION, current_revision, downgrade_base, upgrade_head
from app.dwh.models import DWH_TABLE_NAMES

EXPECTED_TABLES = set(DWH_TABLE_NAMES)
FORBIDDEN_TABLE_SUBSTRINGS = ("case", "prediction", "review_case", "model_score")


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
    """Point at the default `postgres` maintenance DB for CREATE/DROP DATABASE."""
    parsed = urlparse(database_url)
    return urlunparse(parsed._replace(path="/postgres"))


@pytest.fixture(scope="module")
def migrate_database_url() -> str:
    base_url = os.environ.get("TEST_DATABASE_URL") or get_settings().database_url
    if not _postgres_available(base_url):
        pytest.fail(
            "Postgres required for H19 migrate tests. "
            "Start `docker compose up -d db` then re-run "
            "`python -m pytest -q tests/test_dwh_migrate.py`."
        )

    # Isolated DB so upgrade/downgrade does not wipe a shared local silentshield.
    test_name = f"ss_h19_{uuid.uuid4().hex[:10]}"
    admin = create_engine(_admin_url(base_url), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{test_name}"'))
    admin.dispose()

    parsed = urlparse(base_url)
    test_url = urlunparse(parsed._replace(path=f"/{test_name}"))
    yield test_url

    # Teardown: terminate connections then drop.
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


def _dwh_tables(engine) -> set[str]:
    inspector = inspect(engine)
    return set(inspector.get_table_names(schema="dwh")) - {"alembic_version"}


def _assert_empty_domain_tables(engine) -> None:
    with engine.connect() as conn:
        for table in sorted(EXPECTED_TABLES):
            count = conn.execute(text(f'SELECT COUNT(*) FROM dwh."{table}"')).scalar_one()
            assert count == 0, f"expected empty {table}, got {count} rows"


def test_upgrade_head_creates_empty_tables(migrate_database_url: str) -> None:
    upgrade_head(migrate_database_url)
    engine = create_engine(migrate_database_url)
    try:
        tables = _dwh_tables(engine)
        assert tables == EXPECTED_TABLES
        for name in tables:
            lowered = name.lower()
            assert not any(bad in lowered for bad in FORBIDDEN_TABLE_SUBSTRINGS)
        _assert_empty_domain_tables(engine)
        assert current_revision(migrate_database_url) == HEAD_REVISION
    finally:
        engine.dispose()


def test_upgrade_head_is_repeatable(migrate_database_url: str) -> None:
    """Running migrate twice on an empty/already-migrated DB must not error or change shape."""
    upgrade_head(migrate_database_url)
    engine = create_engine(migrate_database_url)
    try:
        before = _dwh_tables(engine)
        cols_before = {
            t: {c["name"] for c in inspect(engine).get_columns(t, schema="dwh")}
            for t in sorted(before)
        }
    finally:
        engine.dispose()

    upgrade_head(migrate_database_url)  # second pass — Alembic no-op at head

    engine = create_engine(migrate_database_url)
    try:
        after = _dwh_tables(engine)
        cols_after = {
            t: {c["name"] for c in inspect(engine).get_columns(t, schema="dwh")}
            for t in sorted(after)
        }
        assert after == before == EXPECTED_TABLES
        assert cols_after == cols_before
        _assert_empty_domain_tables(engine)
        assert current_revision(migrate_database_url) == HEAD_REVISION
    finally:
        engine.dispose()


def test_downgrade_base_then_upgrade_again(migrate_database_url: str) -> None:
    upgrade_head(migrate_database_url)
    downgrade_base(migrate_database_url)
    engine = create_engine(migrate_database_url)
    try:
        remaining = _dwh_tables(engine)
        assert remaining == set()
    finally:
        engine.dispose()

    upgrade_head(migrate_database_url)
    engine = create_engine(migrate_database_url)
    try:
        assert _dwh_tables(engine) == EXPECTED_TABLES
        _assert_empty_domain_tables(engine)
    finally:
        engine.dispose()


def test_source_manifest_unique_and_pk_constraints(migrate_database_url: str) -> None:
    upgrade_head(migrate_database_url)
    engine = create_engine(migrate_database_url)
    try:
        inspector = inspect(engine)
        pk = inspector.get_pk_constraint("source_manifest", schema="dwh")
        assert pk["constrained_columns"] == ["source_id"]
        uniques = inspector.get_unique_constraints("source_manifest", schema="dwh")
        unique_cols = {tuple(u["column_names"]) for u in uniques}
        assert ("snapshot_sha256",) in unique_cols

        student_pk = inspector.get_pk_constraint("student_dimension", schema="dwh")
        assert set(student_pk["constrained_columns"]) == {"source_id", "student_ref"}

        term_pk = inspector.get_pk_constraint("term_grade", schema="dwh")
        assert set(term_pk["constrained_columns"]) == {
            "source_id",
            "student_ref",
            "term_code",
            "course_ref",
        }

        att_pk = inspector.get_pk_constraint("attendance_event", schema="dwh")
        assert set(att_pk["constrained_columns"]) == {
            "source_id",
            "student_ref",
            "observed_at",
            "course_ref",
        }
    finally:
        engine.dispose()
