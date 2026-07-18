"""H39b — RBAC matrix on API routes (Principal override; no live Postgres required)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth.principal import get_principal
from app.cases.store import store
from app.main import app
from tests.auth_helpers import DEFAULT_BAN_QUAN_LY, DEFAULT_GVCN, principal


@pytest.fixture(autouse=True)
def _reset():
    store.clear()
    yield
    store.clear()
    app.dependency_overrides.pop(get_principal, None)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _as(p) -> None:
    app.dependency_overrides[get_principal] = lambda: p


def test_gvcn_forbidden_on_thresholds(client: TestClient) -> None:
    _as(DEFAULT_GVCN)
    r = client.get("/config/thresholds")
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "role_not_permitted"


def test_ban_quan_ly_allowed_on_thresholds(client: TestClient) -> None:
    _as(DEFAULT_BAN_QUAN_LY)
    r = client.get("/config/thresholds")
    assert r.status_code == 200


def test_gvcn_forbidden_on_advisor_drafts(client: TestClient) -> None:
    _as(DEFAULT_GVCN)
    r = client.get("/advisor-handoff-drafts")
    assert r.status_code == 403


def test_gvcn_cannot_approve(client: TestClient) -> None:
    store.create("rbac-g", state="assigned", advisor_ref="a-240eb01d2805", student_ref="s1")
    _as(DEFAULT_GVCN)
    r = client.post("/cases/rbac-g/transitions", json={"action": "approve"})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "role_not_permitted"


def test_gvcn_can_accept(client: TestClient) -> None:
    store.create("rbac-a", state="assigned", advisor_ref="a-240eb01d2805", student_ref="s1")
    _as(DEFAULT_GVCN)
    r = client.post("/cases/rbac-a/transitions", json={"action": "accept"})
    assert r.status_code == 200
    assert r.json()["state"] == "follow_up_in_progress"


def test_gvcn_cannot_see_other_advisor_case(client: TestClient) -> None:
    store.create("rbac-x", state="assigned", advisor_ref="other-adv", student_ref="s1")
    _as(DEFAULT_GVCN)
    r = client.get("/cases/rbac-x")
    assert r.status_code == 404


def test_gvcn_cannot_see_pre_handoff(client: TestClient) -> None:
    store.create("rbac-new", state="new_signal", advisor_ref="a-240eb01d2805", student_ref="s1")
    _as(DEFAULT_GVCN)
    r = client.get("/cases/rbac-new")
    assert r.status_code == 404


def test_cross_org_denied(client: TestClient) -> None:
    store.create("rbac-org", state="assigned", advisor_ref="a-240eb01d2805", student_ref="s1")
    _as(
        principal(
            actor_id="acct:other",
            active_role="ban_quan_ly",
            org_scope="org-other",
            roles=("ban_quan_ly",),
        )
    )
    r = client.get("/cases/rbac-org")
    assert r.status_code == 404


def test_null_active_role_blocked(client: TestClient) -> None:
    _as(
        principal(
            actor_id="acct:demo",
            active_role=None,
            org_scope="org-demo",
            advisor_scope="a-240eb01d2805",
            roles=("ban_quan_ly", "gvcn"),
        )
    )
    r = client.get("/config/thresholds")
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "active_role_required"
