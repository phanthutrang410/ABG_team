"""H39a — auth migration, seed, login/session/cookie matrix (Postgres required)."""

from __future__ import annotations

import os
import uuid
from urllib.parse import urlparse, urlunparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.auth.cli import seed_accounts
from app.auth.models import AccessAuditEventRow
from app.auth.principal import SESSION_COOKIE, get_principal, record_access_event
from app.auth.passwords import hash_password
from app.config import get_settings
from app.database import get_db
from app.dwh.migrate import HEAD_REVISION, current_revision, upgrade_head
from app.main import app

APP_TABLES = {
    "auth_account",
    "auth_account_role",
    "auth_session",
    "access_audit_event",
}
SEED_PASSWORD = "test-seed-password-h39"


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
def auth_database_url() -> str:
    base_url = os.environ.get("TEST_DATABASE_URL") or get_settings().database_url
    if not _postgres_available(base_url):
        pytest.fail(
            "Postgres required for H39 auth tests. "
            "Start `docker compose up -d db` then re-run."
        )

    test_name = f"ss_h39_{uuid.uuid4().hex[:10]}"
    admin = create_engine(_admin_url(base_url), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{test_name}"'))
    admin.dispose()

    parsed = urlparse(base_url)
    test_url = urlunparse(parsed._replace(path=f"/{test_name}"))
    upgrade_head(test_url)
    assert current_revision(test_url) == HEAD_REVISION
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
def auth_client(auth_database_url: str, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", auth_database_url)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("AUTH_SEED_PASSWORD", SEED_PASSWORD)
    get_settings.cache_clear()

    engine = create_engine(auth_database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # Clear auth rows between tests (keep schema).
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM app.access_audit_event"))
        conn.execute(text("DELETE FROM app.auth_session"))
        conn.execute(text("DELETE FROM app.auth_account_role"))
        conn.execute(text("DELETE FROM app.auth_account"))

    db = SessionLocal()
    seed_accounts(db, SEED_PASSWORD)
    db.close()

    def _override_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides.pop(get_principal, None)
    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_db, None)
    get_settings.cache_clear()
    engine.dispose()


def test_app_schema_tables_exist(auth_database_url: str) -> None:
    engine = create_engine(auth_database_url)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'app'"
                )
            ).fetchall()
        names = {r[0] for r in rows}
        assert APP_TABLES <= names
    finally:
        engine.dispose()


def test_role_check_rejects_legacy_roles(auth_database_url: str) -> None:
    engine = create_engine(auth_database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        # Need a parent account first
        db.execute(
            text(
                "INSERT INTO app.auth_account "
                "(actor_id, username, display_name, password_hash, org_scope, is_active) "
                "VALUES ('acct:x', 'xuser', 'X', :ph, 'org-demo', true)"
            ),
            {"ph": hash_password("unused")},
        )
        db.commit()
        for bad in ("leader", "advisor", "admin", "superuser"):
            with pytest.raises(Exception):
                db.execute(
                    text(
                        "INSERT INTO app.auth_account_role (actor_id, role) "
                        "VALUES ('acct:x', :role)"
                    ),
                    {"role": bad},
                )
                db.commit()
            db.rollback()
    finally:
        db.close()
        engine.dispose()


def test_login_success_single_role(auth_client: TestClient) -> None:
    r = auth_client.post("/auth/login", json={"username": "quanly", "password": SEED_PASSWORD})
    assert r.status_code == 200
    body = r.json()
    assert body["account_id"] == "acct:quanly"
    assert body["roles"] == ["ban_quan_ly"]
    assert body["active_role"] == "ban_quan_ly"
    assert "password" not in body
    assert "org_scope" not in body
    assert SESSION_COOKIE in r.cookies


def test_login_wrong_password(auth_client: TestClient) -> None:
    r = auth_client.post("/auth/login", json={"username": "quanly", "password": "wrong"})
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "invalid_credentials"


def test_login_multi_role_leaves_active_null(auth_client: TestClient) -> None:
    r = auth_client.post("/auth/login", json={"username": "demo", "password": SEED_PASSWORD})
    assert r.status_code == 200
    body = r.json()
    assert set(body["roles"]) == {"ban_quan_ly", "gvcn"}
    assert body["active_role"] is None


def test_active_role_switch_and_me(auth_client: TestClient) -> None:
    auth_client.post("/auth/login", json={"username": "demo", "password": SEED_PASSWORD})
    r = auth_client.post("/auth/active-role", json={"role": "gvcn"})
    assert r.status_code == 200
    assert r.json()["active_role"] == "gvcn"
    me = auth_client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["active_role"] == "gvcn"
    assert "advisor_scope" not in me.json()


def test_active_role_rejects_unknown(auth_client: TestClient) -> None:
    auth_client.post("/auth/login", json={"username": "demo", "password": SEED_PASSWORD})
    r = auth_client.post("/auth/active-role", json={"role": "admin"})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "unknown_role"


def test_logout_revokes_session(auth_client: TestClient) -> None:
    auth_client.post("/auth/login", json={"username": "quanly", "password": SEED_PASSWORD})
    assert auth_client.get("/auth/me").status_code == 200
    out = auth_client.post("/auth/logout")
    assert out.status_code == 204
    assert auth_client.get("/auth/me").status_code == 401


def test_disabled_account_rejected(auth_client: TestClient, auth_database_url: str) -> None:
    engine = create_engine(auth_database_url)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE app.auth_account SET is_active = false WHERE username = 'quanly'")
        )
    engine.dispose()
    r = auth_client.post("/auth/login", json={"username": "quanly", "password": SEED_PASSWORD})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "account_disabled"


def test_audit_persists_across_commit(auth_client: TestClient, auth_database_url: str) -> None:
    engine = create_engine(auth_database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        record_access_event(
            actor_id="acct:quanly",
            role="ban_quan_ly",
            action="review_cases.list",
            resource_handle="review-cases",
            decision="allowed",
            db=db,
        )
        rows = db.query(AccessAuditEventRow).all()
        assert len(rows) == 1
        assert rows[0].action == "review_cases.list"
        blob = str(rows[0].__dict__).lower()
        assert "password" not in blob
        assert "prompt" not in blob
    finally:
        db.close()
        engine.dispose()
