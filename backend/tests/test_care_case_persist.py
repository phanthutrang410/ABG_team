"""D460-08 — durable care CaseStore persists across sessions."""

from __future__ import annotations

import os
import uuid
from urllib.parse import urlparse, urlunparse

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from app.cases.domain import (
    CaseAction,
    CaseState,
    TransitionCommand,
    TransitionError,
    TransitionErrorCode,
)
from app.cases.models import CareCaseEvent
from app.cases.store import PostgresCaseStore
from app.config import get_settings
from app.dwh.migrate import upgrade_head

TRUSTED = "leader:persist-test"


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
def care_pg_url() -> str:
    base_url = os.environ.get("TEST_DATABASE_URL") or get_settings().database_url
    if not _postgres_available(base_url):
        pytest.fail(
            "Postgres required for care CaseStore persist tests. "
            "Start `docker compose up -d db` then re-run "
            "`python -m pytest -q tests/test_care_case_persist.py`."
        )
    test_name = f"ss_care_{uuid.uuid4().hex[:10]}"
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


@pytest.fixture()
def care_store(care_pg_url: str) -> PostgresCaseStore:
    engine = create_engine(care_pg_url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    store = PostgresCaseStore(session_factory=factory)
    yield store
    store.clear()
    engine.dispose()


def _cmd(action: CaseAction, **kwargs) -> TransitionCommand:
    defaults = {"actor": TRUSTED, "actor_kind": "human"}
    defaults.update(kwargs)
    return TransitionCommand(action=action, **defaults)


def test_create_survives_new_session(care_pg_url: str) -> None:
    engine = create_engine(care_pg_url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    first = PostgresCaseStore(session_factory=factory)
    created = first.create(
        "rc-persist-1",
        state="new_signal",
        student_ref="sv_persist_1",
        source_id="src-demo",
    )
    assert created.state == CaseState.NEW_SIGNAL
    assert created.student_ref == "sv_persist_1"

    # New store instance + new session factory binding — still readable.
    engine2 = create_engine(care_pg_url, pool_pre_ping=True)
    factory2 = sessionmaker(bind=engine2, autoflush=False, autocommit=False)
    second = PostgresCaseStore(session_factory=factory2)
    loaded = second.get("rc-persist-1")
    assert loaded is not None
    assert loaded.case_id == "rc-persist-1"
    assert loaded.state == CaseState.NEW_SIGNAL
    assert loaded.student_ref == "sv_persist_1"
    assert loaded.source_id == "src-demo"

    second.clear()
    engine.dispose()
    engine2.dispose()


def test_transition_writes_case_event(care_store: PostgresCaseStore, care_pg_url: str) -> None:
    care_store.create("rc-evt-1", state="new_signal", student_ref="sv_evt")
    updated = care_store.transition(
        "rc-evt-1", _cmd(CaseAction.QUEUE_FOR_REVIEW)
    )
    assert updated.state == CaseState.PENDING_REVIEW

    engine = create_engine(care_pg_url, pool_pre_ping=True)
    session = sessionmaker(bind=engine)()
    try:
        events = session.scalars(
            select(CareCaseEvent)
            .where(CareCaseEvent.case_id == "rc-evt-1")
            .order_by(CareCaseEvent.id)
        ).all()
        kinds = [e.kind for e in events]
        assert "created" in kinds
        assert "transition:queue_for_review" in kinds
        transition = next(e for e in events if e.kind.startswith("transition:"))
        assert transition.actor == TRUSTED
        assert transition.from_state == "new_signal"
        assert transition.to_state == "pending_review"
        assert transition.action == "queue_for_review"
    finally:
        session.close()
        engine.dispose()


def test_mapping_repair_persists_flag_and_event(
    care_store: PostgresCaseStore, care_pg_url: str
) -> None:
    care_store.create("rc-map-1", state="new_signal")
    care_store.transition("rc-map-1", _cmd(CaseAction.QUEUE_FOR_REVIEW))
    care_store.transition("rc-map-1", _cmd(CaseAction.APPROVE))

    with pytest.raises(TransitionError) as excinfo:
        care_store.transition("rc-map-1", _cmd(CaseAction.ASSIGN, advisor_ref=None))
    err = excinfo.value
    assert err.code == TransitionErrorCode.MISSING_ADVISOR_REF
    assert err.mapping_repair_queued is True
    assert err.case is not None
    assert err.case.mapping_repair_queued is True
    assert err.case.state == CaseState.APPROVED_FOR_FOLLOW_UP

    reloaded = care_store.get("rc-map-1")
    assert reloaded is not None
    assert reloaded.mapping_repair_queued is True
    assert reloaded.state == CaseState.APPROVED_FOR_FOLLOW_UP

    engine = create_engine(care_pg_url, pool_pre_ping=True)
    session = sessionmaker(bind=engine)()
    try:
        events = session.scalars(
            select(CareCaseEvent).where(CareCaseEvent.case_id == "rc-map-1")
        ).all()
        assert any(e.kind == "mapping_repair" for e in events)
    finally:
        session.close()
        engine.dispose()
