"""H39 — RBAC scope + Principal role matrix (no DB required for scope unit tests)."""

from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth import Principal, can_access_case, require_roles
from app.auth.principal import (
    clear_access_audit_log,
    get_access_audit_log,
    get_principal,
    record_access_event,
)
from app.auth.scope import gvcn_may_see_case_state
from app.main import app as main_app

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
def _leader_only(principal: Principal = Depends(require_roles("ban_quan_ly"))) -> dict:
    return {"actor_id": principal.actor_id}


@pytest.fixture(autouse=True)
def _reset():
    clear_access_audit_log()
    main_app.dependency_overrides.clear()
    _test_app.dependency_overrides.clear()
    yield
    clear_access_audit_log()
    main_app.dependency_overrides.clear()
    _test_app.dependency_overrides.clear()


def test_ban_quan_ly_allow_own_org() -> None:
    principal = Principal(
        actor_id="acct:1",
        active_role="ban_quan_ly",
        org_scope="org-a",
        roles=("ban_quan_ly",),
    )
    assert can_access_case(principal, case_advisor_ref="adv-x", case_org="org-a") is True


def test_require_roles_allows_ban_quan_ly() -> None:
    p = Principal(
        actor_id="acct:1",
        active_role="ban_quan_ly",
        org_scope="org-a",
        roles=("ban_quan_ly",),
    )
    _test_app.dependency_overrides[get_principal] = lambda: p
    client = TestClient(_test_app)
    r = client.get("/leader-only")
    assert r.status_code == 200


def test_gvcn_allow_assigned_case() -> None:
    principal = Principal(
        actor_id="acct:7",
        active_role="gvcn",
        org_scope="org-a",
        advisor_scope="adv-7",
        roles=("gvcn",),
    )
    assert can_access_case(principal, case_advisor_ref="adv-7", case_org="org-a") is True


def test_gvcn_deny_cross_advisor_scope() -> None:
    principal = Principal(
        actor_id="acct:7",
        active_role="gvcn",
        org_scope="org-a",
        advisor_scope="adv-7",
        roles=("gvcn",),
    )
    assert can_access_case(principal, case_advisor_ref="adv-99", case_org="org-a") is False


def test_gvcn_deny_cross_org() -> None:
    principal = Principal(
        actor_id="acct:7",
        active_role="gvcn",
        org_scope="org-a",
        advisor_scope="adv-7",
        roles=("gvcn",),
    )
    assert can_access_case(principal, case_advisor_ref="adv-7", case_org="org-b") is False


def test_ban_quan_ly_deny_cross_org() -> None:
    principal = Principal(
        actor_id="acct:1",
        active_role="ban_quan_ly",
        org_scope="org-a",
        roles=("ban_quan_ly",),
    )
    assert can_access_case(principal, case_advisor_ref="adv-x", case_org="org-b") is False


def test_gvcn_missing_scope_never_authorized() -> None:
    principal = Principal(
        actor_id="acct:7",
        active_role="gvcn",
        org_scope="org-a",
        advisor_scope=None,
        roles=("gvcn",),
    )
    assert can_access_case(principal, case_advisor_ref=None, case_org="org-a") is False


def test_gvcn_route_rejects_ban_quan_ly_only_dependency() -> None:
    p = Principal(
        actor_id="acct:7",
        active_role="gvcn",
        org_scope="org-a",
        advisor_scope="adv-7",
        roles=("gvcn",),
    )
    _test_app.dependency_overrides[get_principal] = lambda: p
    client = TestClient(_test_app)
    r = client.get("/leader-only")
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "role_not_permitted"


def test_missing_session_rejected() -> None:
    client = TestClient(_test_app)
    r = client.get("/whoami")
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "missing_identity"


def test_legacy_admin_role_unknown_via_require_roles() -> None:
    p = Principal(
        actor_id="acct:x",
        active_role="admin",
        org_scope="org-a",
        roles=("admin",),
    )
    _test_app.dependency_overrides[get_principal] = lambda: p
    client = TestClient(_test_app)
    r = client.get("/leader-only")
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "unknown_role"


def test_null_active_role_denied_by_require_roles() -> None:
    p = Principal(
        actor_id="acct:demo",
        active_role=None,
        org_scope="org-demo",
        advisor_scope="a-240eb01d2805",
        roles=("ban_quan_ly", "gvcn"),
    )
    _test_app.dependency_overrides[get_principal] = lambda: p
    client = TestClient(_test_app)
    r = client.get("/leader-only")
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "active_role_required"


def test_gvcn_visible_states() -> None:
    assert gvcn_may_see_case_state("assigned") is True
    assert gvcn_may_see_case_state("new_signal") is False
    assert gvcn_may_see_case_state("pending_review") is False


def test_access_audit_event_records_actor_role_action_resource() -> None:
    record_access_event(
        actor_id="acct:1",
        role="ban_quan_ly",
        action="view_case",
        resource_handle="case-123",
        decision="allowed",
    )
    log = get_access_audit_log()
    assert len(log) == 1
    event = log[0]
    assert event.actor_id == "acct:1"
    assert event.role == "ban_quan_ly"
    assert event.action == "view_case"
    assert event.resource_handle == "case-123"
    assert event.decision == "allowed"
    assert event.at is not None
