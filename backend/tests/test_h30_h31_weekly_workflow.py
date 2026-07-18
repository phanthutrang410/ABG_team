"""H30/H31 — snapshot ledger + weekly workflow tests."""

from __future__ import annotations

import json
import os
import uuid
from urllib.parse import urlparse, urlunparse

import pytest
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.dwh.migrate import HEAD_REVISION, upgrade_head
from app.dwh.models import ActiveDatasetSnapshot, DatasetSnapshot, WorkflowRun
from app.dwh.weekly_workflow import run_weekly_from_bytes


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
def weekly_database_url() -> str:
    base_url = os.environ.get("TEST_DATABASE_URL") or get_settings().database_url
    if not _postgres_available(base_url):
        pytest.fail("Postgres required for H30/H31 tests")

    test_name = f"ss_h30_{uuid.uuid4().hex[:10]}"
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


def test_h30_head_revision_and_tables(weekly_database_url: str) -> None:
    assert HEAD_REVISION == "20260718_h30_snapshot"
    engine = create_engine(weekly_database_url)
    try:
        tables = set(inspect(engine).get_table_names(schema="dwh")) - {"alembic_version"}
        for required in (
            "dataset_source",
            "dataset_snapshot",
            "active_dataset_snapshot",
            "workflow_run",
            "workflow_step_run",
        ):
            assert required in tables
        pk = inspect(engine).get_pk_constraint("dataset_snapshot", schema="dwh")
        assert pk["constrained_columns"] == ["snapshot_id"]
    finally:
        engine.dispose()


def test_h31_exact_byte_replay_idempotent(weekly_database_url: str) -> None:
    payload = json.dumps({"contract_version": "weekly-snapshot-v2", "n": 1}).encode()
    first = run_weekly_from_bytes(
        weekly_database_url,
        dataset_key="epu-care-signals-test",
        content_bytes=payload,
        approval_id="approval:test-replay",
        idempotency_key="k1",
    )
    assert first.status == "succeeded"
    assert first.snapshot_id

    second = run_weekly_from_bytes(
        weekly_database_url,
        dataset_key="epu-care-signals-test",
        content_bytes=payload,
        approval_id="approval:test-replay",
        idempotency_key="k1",
    )
    assert second.status == "duplicate"
    assert second.snapshot_id == first.snapshot_id


def test_h31_approval_fail_zero_promotion(weekly_database_url: str) -> None:
    payload = json.dumps({"contract_version": "weekly-snapshot-v2"}).encode()
    result = run_weekly_from_bytes(
        weekly_database_url,
        dataset_key="epu-care-fail",
        content_bytes=payload,
        approval_id="approval:x",
        provenance_approved=False,
        idempotency_key="fail-1",
    )
    assert result.status == "failed"
    assert "approval_missing" in result.reason_codes

    engine = create_engine(weekly_database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        active = session.get(ActiveDatasetSnapshot, "epu-care-fail")
        assert active is None
    finally:
        session.close()
        engine.dispose()


def test_h31_multi_version_same_dataset(weekly_database_url: str) -> None:
    a = json.dumps({"v": 1}).encode()
    b = json.dumps({"v": 2}).encode()
    r1 = run_weekly_from_bytes(
        weekly_database_url,
        dataset_key="epu-multi",
        content_bytes=a,
        approval_id="a1",
        idempotency_key="m1",
    )
    r2 = run_weekly_from_bytes(
        weekly_database_url,
        dataset_key="epu-multi",
        content_bytes=b,
        approval_id="a2",
        idempotency_key="m2",
    )
    assert r1.status == "succeeded" and r2.status == "succeeded"
    assert r1.snapshot_id != r2.snapshot_id

    engine = create_engine(weekly_database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        active = session.get(ActiveDatasetSnapshot, "epu-multi")
        assert active is not None
        assert active.snapshot_id == r2.snapshot_id
        snaps = session.scalars(
            select(DatasetSnapshot).where(DatasetSnapshot.dataset_key == "epu-multi")
        ).all()
        assert len(snaps) == 2
        runs = session.scalars(
            select(WorkflowRun).where(WorkflowRun.dataset_key == "epu-multi")
        ).all()
        assert len(runs) == 2
    finally:
        session.close()
        engine.dispose()
