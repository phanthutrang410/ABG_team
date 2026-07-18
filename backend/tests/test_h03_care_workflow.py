"""H03 — care workflow API wired to H08 advisor_ref / mapping_repair."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.cases.store import store
from app.config import get_settings
from app.database import get_db
from app.dwh.import_gate import ApprovalArtifact
from app.dwh.importer import SEMESTER_SOURCE_ID, import_semester
from app.dwh.migrate import upgrade_head
from app.dwh.read_adapter import get_normalized_student, list_normalized_students
from app.main import app

TRUSTED_ACTOR = "leader:demo"
TRUSTED_KIND = "human"
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


@pytest.fixture(autouse=True)
def _reset_store() -> None:
    store.clear()
    yield
    store.clear()


@pytest.fixture(autouse=True)
def _default_local_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("CASES_TRUSTED_ACTOR", TRUSTED_ACTOR)
    monkeypatch.setenv("CASES_TRUSTED_ACTOR_KIND", TRUSTED_KIND)
    monkeypatch.delenv("CASES_SEED_CREATE", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def h03_database_url() -> str:
    base_url = os.environ.get("TEST_DATABASE_URL") or get_settings().database_url
    if not _postgres_available(base_url):
        pytest.fail("Postgres required for H03 tests. Start `docker compose up -d db`.")
    test_name = f"ss_h03_{uuid.uuid4().hex[:10]}"
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
def client(h03_database_url: str):
    engine = create_engine(h03_database_url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def _override_db():
        session: Session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def _transition_body(action: str, **extra) -> dict:
    body = {"action": action, "actor": TRUSTED_ACTOR, "actor_kind": TRUSTED_KIND}
    body.update(extra)
    return body


def _import_semester_payload(
    database_url: str, tmp_path: Path, payload: list[dict]
) -> None:
    path = tmp_path / "sem.json"
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    path.write_bytes(raw)
    approval = ApprovalArtifact(
        source_id=SEMESTER_SOURCE_ID,
        snapshot_sha256=hashlib.sha256(raw).hexdigest(),
        record_count=len(payload),
        provenance_approved=True,
        schema_version="epu-1",
        extracted_at=_EXTRACTED,
        owner="test",
        usage_rights="mvp",
    )
    result = import_semester(
        database_url, source_path=path, approval=approval, ensure_schema=False
    )
    assert result.status == "imported", result


def _v59_student(*, mssv: str, advisor_name: str | None) -> dict:
    info = {
        "MSSV": mssv,
        "Trạng thái": "Đang học",
        "Khoa": "CNTT",
        "Ngành": "KTPM",
        "Lớp": "A1",
        "Khóa": "2022",
        "Họ và tên": "Anon",
    }
    if advisor_name:
        info["Cố vấn học tập"] = advisor_name
    return {
        "token": "t",
        "student_info": info,
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


def test_approve_dismiss_defer_smoke(client: TestClient) -> None:
    assert client.post("/cases", json={"case_id": "care-1", "state": "new_signal"}).status_code == 201
    assert (
        client.post(
            "/cases/care-1/transitions",
            json=_transition_body("queue_for_review"),
        ).status_code
        == 200
    )
    r = client.post("/cases/care-1/transitions", json=_transition_body("approve"))
    assert r.status_code == 200
    assert r.json()["state"] == "approved_for_follow_up"

    # Separate case for dismiss / defer
    client.post("/cases", json={"case_id": "care-d", "state": "pending_review"})
    r = client.post(
        "/cases/care-d/transitions",
        json=_transition_body("defer", review_at="2026-07-21T10:00:00"),
    )
    assert r.status_code == 200
    assert r.json()["state"] == "pending_review"
    assert r.json()["review_at"].startswith("2026-07-21")

    r = client.post(
        "/cases/care-d/transitions",
        json=_transition_body("dismiss", reason_code="false_alarm"),
    )
    assert r.status_code == 200
    assert r.json()["state"] == "dismissed"


def test_assign_mapping_repair_when_h08_missing_advisor(
    client: TestClient, h03_database_url: str, tmp_path: Path
) -> None:
    _import_semester_payload(
        h03_database_url,
        tmp_path,
        [_v59_student(mssv="NOADV001", advisor_name=None)],
    )
    engine = create_engine(h03_database_url)
    with sessionmaker(bind=engine)() as session:
        records = list_normalized_students(session, SEMESTER_SOURCE_ID)
        assert len(records) == 1
        assert records[0].mapping_repair is True
        student_ref = records[0].student_ref
    engine.dispose()

    client.post(
        "/cases",
        json={
            "case_id": "h03-repair",
            "state": "approved_for_follow_up",
            "student_ref": student_ref,
            "source_id": SEMESTER_SOURCE_ID,
        },
    )
    r = client.post(
        "/cases/h03-repair/transitions",
        json=_transition_body("assign", advisor_ref="client-fake"),
    )
    assert r.status_code == 409
    body = r.json()["detail"]
    assert body["code"] == "missing_advisor_ref"
    assert body["state"] == "approved_for_follow_up"
    assert body["mapping_repair_queued"] is True
    assert "advisor_ref" not in body


def test_assign_handoff_when_h08_has_advisor(
    client: TestClient, h03_database_url: str, tmp_path: Path
) -> None:
    _import_semester_payload(
        h03_database_url,
        tmp_path,
        [_v59_student(mssv="WITHADV001", advisor_name="Nguyen Van A")],
    )
    engine = create_engine(h03_database_url)
    with sessionmaker(bind=engine)() as session:
        record = list_normalized_students(session, SEMESTER_SOURCE_ID)[0]
        assert record.mapping_repair is False
        assert record.advisor_ref
        student_ref = record.student_ref
        expected_advisor = record.advisor_ref
        looked = get_normalized_student(session, SEMESTER_SOURCE_ID, student_ref)
        assert looked is not None
        assert looked.advisor_ref == expected_advisor
    engine.dispose()

    client.post(
        "/cases",
        json={
            "case_id": "h03-ok",
            "state": "approved_for_follow_up",
            "student_ref": student_ref,
            "source_id": SEMESTER_SOURCE_ID,
        },
    )
    r = client.post("/cases/h03-ok/transitions", json=_transition_body("assign"))
    assert r.status_code == 200
    payload = r.json()
    assert payload["state"] == "assigned"
    assert payload["mapping_repair_queued"] is False
    assert "advisor_ref" not in payload
    assert "student_ref" not in payload
    assert "source_id" not in payload

    internal = store.get("h03-ok")
    assert internal is not None
    assert internal.advisor_ref == expected_advisor
