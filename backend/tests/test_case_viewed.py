"""H36a — POST /cases/{id}/viewed: GVCN 'đã xem' receipt (idempotent, scoped).

Viewing (reading the secured handoff) is distinct from acceptance (the
``assigned → follow_up_in_progress`` transition). These tests pin the RBAC and
idempotency invariants the FE advisor deep-link flow depends on.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth.principal import get_principal
from app.cases.domain import CaseSnapshot, CaseState
from app.cases.store import store
from app.main import app
from tests.auth_helpers import principal

GVCN_SCOPE = "a-240eb01d2805"


@pytest.fixture(autouse=True)
def _reset_store() -> None:
    store.clear()
    yield
    store.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _seed_assigned(case_id: str = "v-1", advisor_ref: str = GVCN_SCOPE) -> None:
    store.put(
        CaseSnapshot(
            case_id=case_id,
            state=CaseState.ASSIGNED,
            advisor_ref=advisor_ref,
        )
    )


def _as(principal_obj) -> None:
    app.dependency_overrides[get_principal] = lambda: principal_obj


def test_gvcn_marks_viewed_and_is_idempotent(client: TestClient) -> None:
    _seed_assigned()
    _as(principal(active_role="gvcn", advisor_scope=GVCN_SCOPE))

    first = client.post("/cases/v-1/viewed")
    assert first.status_code == 200
    body = first.json()
    assert body["state"] == "assigned"  # viewing is NOT a state change
    assert body["viewed_at"] is not None
    stamped = body["viewed_at"]

    second = client.post("/cases/v-1/viewed")
    assert second.status_code == 200
    assert second.json()["viewed_at"] == stamped  # idempotent — receipt set once


def test_viewed_at_surfaces_on_get_case(client: TestClient) -> None:
    _seed_assigned()
    _as(principal(active_role="gvcn", advisor_scope=GVCN_SCOPE))

    client.post("/cases/v-1/viewed")
    got = client.get("/cases/v-1")
    assert got.status_code == 200
    assert got.json()["viewed_at"] is not None


def test_ban_quan_ly_cannot_mark_viewed(client: TestClient) -> None:
    _seed_assigned()
    _as(principal(active_role="ban_quan_ly"))

    res = client.post("/cases/v-1/viewed")
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "role_not_permitted"

    # Receipt must remain unset — a management view never logs advisor 'đã xem'.
    assert store.get("v-1").viewed_at is None


def test_gvcn_out_of_scope_gets_404(client: TestClient) -> None:
    _seed_assigned(advisor_ref="a-someone-else")
    _as(principal(active_role="gvcn", advisor_scope=GVCN_SCOPE))

    res = client.post("/cases/v-1/viewed")
    assert res.status_code == 404
    assert store.get("v-1").viewed_at is None


def test_viewed_unknown_case_is_404(client: TestClient) -> None:
    _as(principal(active_role="gvcn", advisor_scope=GVCN_SCOPE))
    assert client.post("/cases/does-not-exist/viewed").status_code == 404
