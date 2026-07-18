"""H34 — light wiring: GET /weekly-reports/latest, /weekly-briefings/latest, shown/ack."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.weekly import state as weekly_state


@pytest.fixture(autouse=True)
def _reset_state():
    weekly_state.clear()
    yield
    weekly_state.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_latest_weekly_report_seeds_empty_fixture_when_missing(client: TestClient) -> None:
    response = client.get("/weekly-reports/latest", params={"branch": "semester"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "empty"
    assert body["branch"] == "semester"
    assert "student_ref" not in body


def test_latest_weekly_report_rejects_unknown_branch(client: TestClient) -> None:
    response = client.get("/weekly-reports/latest", params={"branch": "combined"})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "unknown_branch"


def test_latest_weekly_report_default_branch_is_semester(client: TestClient) -> None:
    response = client.get("/weekly-reports/latest")
    assert response.status_code == 200
    assert response.json()["branch"] == "semester"


def test_latest_briefing_role_scoped_for_leader_vs_advisor(client: TestClient) -> None:
    leader_resp = client.get(
        "/weekly-briefings/latest",
        headers={"X-SS-Actor-Id": "leader:1", "X-SS-Role": "leader", "X-SS-Org-Scope": "org-a"},
    )
    advisor_resp = client.get(
        "/weekly-briefings/latest",
        headers={
            "X-SS-Actor-Id": "advisor:1",
            "X-SS-Role": "advisor",
            "X-SS-Org-Scope": "org-a",
            "X-SS-Advisor-Scope": "adv-1",
        },
    )
    assert leader_resp.status_code == 200
    assert advisor_resp.status_code == 200
    assert leader_resp.json()["role"] == "leader"
    assert advisor_resp.json()["role"] == "advisor"
    assert leader_resp.json()["message_vi"] != advisor_resp.json()["message_vi"]


def test_briefing_shown_and_ack_idempotent(client: TestClient) -> None:
    briefing = client.get("/weekly-briefings/latest").json()
    briefing_id = briefing["briefing_id"]

    shown1 = client.post(f"/weekly-briefings/{briefing_id}/shown")
    shown2 = client.post(f"/weekly-briefings/{briefing_id}/shown")
    assert shown1.status_code == 200
    assert shown1.json()["shown_at"] == shown2.json()["shown_at"]

    ack1 = client.post(f"/weekly-briefings/{briefing_id}/ack")
    ack2 = client.post(f"/weekly-briefings/{briefing_id}/ack")
    assert ack1.json()["ack_at"] == ack2.json()["ack_at"]


def test_weekly_report_openapi_has_no_forbidden_public_fields(client: TestClient) -> None:
    from app.contracts.integration import assert_no_forbidden_keys

    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    assert "/weekly-reports/latest" in paths
    assert "/weekly-briefings/latest" in paths

    schemas = schema.get("components", {}).get("schemas", {})
    for name in ("WeeklyReport", "Briefing", "BriefingReceipt", "ActionCard"):
        assert name in schemas
        assert_no_forbidden_keys(schemas[name])
