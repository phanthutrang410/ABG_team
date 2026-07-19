"""GET /advisor/roster — scoped 4×115 overlay + cross-advisor deny."""

from __future__ import annotations

import os
import uuid
from urllib.parse import urlparse, urlunparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.auth.principal import Principal, get_principal
from app.cases.store import InMemoryCaseStore
from app.config import get_settings
from app.database import get_db
from app.dwh.importer import import_semester
from app.dwh.migrate import upgrade_head
from app.dwh.partition_demo import ADVISOR_REFS, CHUNK_SIZE, partition_advisor_assignments
from app.main import app
from tests.auth_helpers import principal


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
def roster_db_url() -> str:
    base_url = os.environ.get("TEST_DATABASE_URL") or get_settings().database_url
    if not _postgres_available(base_url):
        pytest.fail("Postgres required for roster tests")

    test_name = f"ss_roster_{uuid.uuid4().hex[:10]}"
    admin = create_engine(_admin_url(base_url), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{test_name}"'))
    admin.dispose()

    parsed = urlparse(base_url)
    test_url = urlunparse(parsed._replace(path=f"/{test_name}"))
    upgrade_head(test_url)
    import_semester(test_url, ensure_schema=False)
    engine = create_engine(test_url, pool_pre_ping=True)
    with Session(engine) as session:
        result = partition_advisor_assignments(session)
        assert result.status == "partitioned"
        session.commit()
    engine.dispose()
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


@pytest.fixture
def roster_client(roster_db_url: str, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", roster_db_url)
    get_settings.cache_clear()

    engine = create_engine(roster_db_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def _override_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    mem = InMemoryCaseStore()
    monkeypatch.setattr("app.cases.advisor_roster_router.store", mem)

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    yield client, mem
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_principal, None)
    engine.dispose()


def _as(client_pair, p: Principal):
    client, _ = client_pair
    app.dependency_overrides[get_principal] = lambda: p
    return client


def test_gvcn_roster_exactly_115_and_disjoint(roster_client) -> None:
    client_pair = roster_client
    seen: set[str] = set()
    for ref in ADVISOR_REFS:
        p = principal(
            actor_id=f"acct:{ref}",
            active_role="gvcn",
            advisor_scope=ref,
            roles=("gvcn",),
        )
        client = _as(client_pair, p)
        res = client.get("/advisor/roster")
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["state"] == "ok"
        assert len(body["classes"]) == 1
        cls = body["classes"][0]
        assert cls["student_count"] == CHUNK_SIZE
        assert len(cls["students"]) == CHUNK_SIZE
        refs = {s["student_ref"] for s in cls["students"]}
        assert refs.isdisjoint(seen)
        seen |= refs
    assert len(seen) == CHUNK_SIZE * len(ADVISOR_REFS)


def test_gvcn_cross_scope_empty_for_unknown_scope(roster_client) -> None:
    client = _as(
        roster_client,
        principal(
            active_role="gvcn",
            advisor_scope="a-not-a-real-scope",
            roles=("gvcn",),
        ),
    )
    res = client.get("/advisor/roster")
    assert res.status_code == 200
    assert res.json()["state"] == "empty"
    assert res.json()["classes"] == []


def test_ban_quan_ly_sees_all_four_classes(roster_client) -> None:
    client = _as(
        roster_client,
        principal(active_role="ban_quan_ly", advisor_scope=None, roles=("ban_quan_ly",)),
    )
    res = client.get("/advisor/roster")
    assert res.status_code == 200
    body = res.json()
    assert body["state"] == "ok"
    assert len(body["classes"]) == 4
    total = sum(c["student_count"] for c in body["classes"])
    assert total == CHUNK_SIZE * 4
