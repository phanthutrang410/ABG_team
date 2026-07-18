"""H36 — production identity/RBAC/scope + access-audit foundation.

Covers: leader allow, advisor allow (assigned), advisor deny (cross-scope),
forged/missing headers in production env, and a role-switch matrix. Also
exercises the FastAPI dependency wiring end-to-end via a throwaway router so
header parsing/validation is tested, not just the dataclass logic.
"""

from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth import Principal, can_access_case, get_principal, require_roles
from app.auth.principal import clear_access_audit_log, get_access_audit_log, record_access_event
from app.config import Settings, get_settings

# --- HTTP wiring: minimal app exercising the real dependency chain ---

_test_app = FastAPI()


@_test_app.get("/whoami")
def _whoami(principal: Principal = Depends(get_principal)) -> dict:
    return {
        "actor_id": principal.actor_id,
        "active_role": principal.active_role,
        "org_scope": principal.org_scope,
        "advisor_scope": principal.advisor_scope,
    }


@_test_app.get("/leader-only")
def _leader_only(principal: Principal = Depends(require_roles("leader", "admin"))) -> dict:
    return {"actor_id": principal.actor_id}


def _override_env(monkeypatch: pytest.MonkeyPatch, app_env: str) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("APP_ENV", app_env)
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset(monkeypatch: pytest.MonkeyPatch):
    clear_access_audit_log()
    _override_env(monkeypatch, "local")
    yield
    get_settings.cache_clear()
    clear_access_audit_log()


@pytest.fixture
def client() -> TestClient:
    return TestClient(_test_app)


# --- local/demo default identity (existing demo routes keep working) ---


def test_local_env_defaults_when_headers_absent(client: TestClient) -> None:
    r = client.get("/whoami")
    assert r.status_code == 200
    body = r.json()
    assert body["actor_id"] == "leader:demo"
    assert body["active_role"] == "leader"
    assert body["org_scope"] == "org-demo"
    assert body["advisor_scope"] is None


# --- leader allow ---


def test_leader_allow_own_org(client: TestClient) -> None:
    r = client.get(
        "/whoami",
        headers={
            "X-SS-Actor-Id": "leader:1",
            "X-SS-Role": "leader",
            "X-SS-Org-Scope": "org-a",
        },
    )
    assert r.status_code == 200
    principal = Principal(
        actor_id="leader:1", active_role="leader", org_scope="org-a", advisor_scope=None
    )
    assert can_access_case(principal, case_advisor_ref="adv-x", case_org="org-a") is True


def test_leader_only_route_allows_leader(client: TestClient) -> None:
    r = client.get(
        "/leader-only",
        headers={
            "X-SS-Actor-Id": "leader:1",
            "X-SS-Role": "leader",
            "X-SS-Org-Scope": "org-a",
        },
    )
    assert r.status_code == 200


# --- advisor allow assigned ---


def test_advisor_allow_assigned_case(client: TestClient) -> None:
    r = client.get(
        "/whoami",
        headers={
            "X-SS-Actor-Id": "advisor:7",
            "X-SS-Role": "advisor",
            "X-SS-Org-Scope": "org-a",
            "X-SS-Advisor-Scope": "adv-7",
        },
    )
    assert r.status_code == 200
    principal = Principal(
        actor_id="advisor:7",
        active_role="advisor",
        org_scope="org-a",
        advisor_scope="adv-7",
    )
    assert can_access_case(principal, case_advisor_ref="adv-7", case_org="org-a") is True


# --- advisor deny cross-scope ---


def test_advisor_deny_cross_advisor_scope() -> None:
    principal = Principal(
        actor_id="advisor:7",
        active_role="advisor",
        org_scope="org-a",
        advisor_scope="adv-7",
    )
    assert can_access_case(principal, case_advisor_ref="adv-99", case_org="org-a") is False


def test_advisor_deny_cross_org() -> None:
    principal = Principal(
        actor_id="advisor:7",
        active_role="advisor",
        org_scope="org-a",
        advisor_scope="adv-7",
    )
    assert can_access_case(principal, case_advisor_ref="adv-7", case_org="org-b") is False


def test_leader_deny_cross_org() -> None:
    principal = Principal(
        actor_id="leader:1", active_role="leader", org_scope="org-a", advisor_scope=None
    )
    assert can_access_case(principal, case_advisor_ref="adv-x", case_org="org-b") is False


def test_advisor_missing_scope_is_never_authorized() -> None:
    # Defensive: a principal built with role=advisor but no scope must never
    # be treated as matching a case whose advisor_ref happens to be falsy/None.
    principal = Principal(
        actor_id="advisor:7", active_role="advisor", org_scope="org-a", advisor_scope=None
    )
    assert can_access_case(principal, case_advisor_ref=None, case_org="org-a") is False


def test_advisor_route_rejects_leader_only_dependency(client: TestClient) -> None:
    r = client.get(
        "/leader-only",
        headers={
            "X-SS-Actor-Id": "advisor:7",
            "X-SS-Role": "advisor",
            "X-SS-Org-Scope": "org-a",
            "X-SS-Advisor-Scope": "adv-7",
        },
    )
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "role_not_permitted"


# --- forged/missing headers in production env ---


def test_production_env_rejects_missing_headers(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _override_env(monkeypatch, "production")
    r = client.get("/whoami")
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "missing_identity"


@pytest.mark.parametrize("app_env", ["production", "live", "demo"])
def test_non_local_envs_require_full_headers(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, app_env: str
) -> None:
    _override_env(monkeypatch, app_env)
    r = client.get("/whoami")
    assert r.status_code == 401


def test_production_env_rejects_forged_empty_actor(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _override_env(monkeypatch, "production")
    r = client.get(
        "/whoami",
        headers={
            "X-SS-Actor-Id": "",
            "X-SS-Role": "leader",
            "X-SS-Org-Scope": "org-a",
        },
    )
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "missing_identity"


def test_production_env_accepts_full_trusted_headers(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _override_env(monkeypatch, "production")
    r = client.get(
        "/whoami",
        headers={
            "X-SS-Actor-Id": "leader:42",
            "X-SS-Role": "leader",
            "X-SS-Org-Scope": "org-a",
        },
    )
    assert r.status_code == 200
    assert r.json()["actor_id"] == "leader:42"


def test_production_env_advisor_without_scope_rejected(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _override_env(monkeypatch, "production")
    r = client.get(
        "/whoami",
        headers={
            "X-SS-Actor-Id": "advisor:7",
            "X-SS-Role": "advisor",
            "X-SS-Org-Scope": "org-a",
        },
    )
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "missing_advisor_scope"


def test_partial_headers_in_local_env_still_fail_closed(
    client: TestClient,
) -> None:
    # Any header present at all switches off the local default and demands
    # a full, valid set — client cannot half-declare an identity.
    r = client.get("/whoami", headers={"X-SS-Role": "leader"})
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "missing_identity"


def test_unknown_role_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _override_env(monkeypatch, "production")
    r = client.get(
        "/whoami",
        headers={
            "X-SS-Actor-Id": "x:1",
            "X-SS-Role": "superuser",
            "X-SS-Org-Scope": "org-a",
        },
    )
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "unknown_role"


# --- role-switch matrix ---


@pytest.mark.parametrize(
    ("role", "advisor_scope", "expect_status"),
    [
        ("leader", None, 200),
        ("admin", None, 200),
        ("advisor", "adv-1", 200),
        ("advisor", None, 403),
    ],
)
def test_role_switch_matrix(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    role: str,
    advisor_scope: str | None,
    expect_status: int,
) -> None:
    _override_env(monkeypatch, "production")
    headers = {
        "X-SS-Actor-Id": f"{role}:1",
        "X-SS-Role": role,
        "X-SS-Org-Scope": "org-a",
    }
    if advisor_scope:
        headers["X-SS-Advisor-Scope"] = advisor_scope
    r = client.get("/whoami", headers=headers)
    assert r.status_code == expect_status
    if expect_status == 200:
        assert r.json()["active_role"] == role


def test_role_switch_same_actor_different_requests(client: TestClient) -> None:
    """Same actor_id can appear under different roles across requests; the
    server must resolve each request's principal independently from headers,
    never from prior request state."""
    leader_headers = {
        "X-SS-Actor-Id": "dual:1",
        "X-SS-Role": "leader",
        "X-SS-Org-Scope": "org-a",
    }
    advisor_headers = {
        "X-SS-Actor-Id": "dual:1",
        "X-SS-Role": "advisor",
        "X-SS-Org-Scope": "org-a",
        "X-SS-Advisor-Scope": "adv-1",
    }
    r1 = client.get("/whoami", headers=leader_headers)
    r2 = client.get("/whoami", headers=advisor_headers)
    assert r1.json()["active_role"] == "leader"
    assert r2.json()["active_role"] == "advisor"
    assert r2.json()["advisor_scope"] == "adv-1"


# --- access audit event (no PII) ---


def test_access_audit_event_records_actor_role_action_resource() -> None:
    record_access_event(
        actor_id="leader:1",
        role="leader",
        action="view_case",
        resource_handle="case-123",
    )
    log = get_access_audit_log()
    assert len(log) == 1
    event = log[0]
    assert event.actor_id == "leader:1"
    assert event.role == "leader"
    assert event.action == "view_case"
    assert event.resource_handle == "case-123"
    assert event.at is not None


def test_settings_helper_local_default_env_detection() -> None:
    from app.auth.principal import _is_local_default_env

    assert _is_local_default_env(Settings(app_env="local")) is True
    assert _is_local_default_env(Settings(app_env="test")) is True
    assert _is_local_default_env(Settings(app_env="production")) is False
    assert _is_local_default_env(Settings(app_env="demo")) is False
