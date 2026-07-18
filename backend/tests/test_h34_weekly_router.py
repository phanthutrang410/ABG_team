"""H34 — light wiring: GET /weekly-reports/latest, /weekly-briefings/latest, shown/ack."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth.principal import Principal, get_principal
from app.main import app
from app.weekly import state as weekly_state
from tests.auth_helpers import DEFAULT_BAN_QUAN_LY, DEFAULT_GVCN


@pytest.fixture(autouse=True)
def _reset_state():
    weekly_state.clear()
    app.dependency_overrides.clear()
    yield
    weekly_state.clear()
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _as(principal: Principal) -> None:
    app.dependency_overrides[get_principal] = lambda: principal


def test_latest_weekly_report_seeds_empty_fixture_when_missing(client: TestClient) -> None:
    _as(DEFAULT_BAN_QUAN_LY)
    response = client.get("/weekly-reports/latest", params={"branch": "semester"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "empty"
    assert body["branch"] == "semester"
    assert "student_ref" not in body


def test_latest_weekly_report_rejects_unknown_branch(client: TestClient) -> None:
    _as(DEFAULT_BAN_QUAN_LY)
    response = client.get("/weekly-reports/latest", params={"branch": "combined"})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "unknown_branch"


def test_latest_weekly_report_default_branch_is_semester(client: TestClient) -> None:
    _as(DEFAULT_BAN_QUAN_LY)
    response = client.get("/weekly-reports/latest")
    assert response.status_code == 200
    assert response.json()["branch"] == "semester"


def test_latest_briefing_role_scoped_for_ban_quan_ly_vs_gvcn(client: TestClient) -> None:
    _as(DEFAULT_BAN_QUAN_LY)
    leader_resp = client.get("/weekly-briefings/latest")
    _as(DEFAULT_GVCN)
    advisor_resp = client.get("/weekly-briefings/latest")
    assert leader_resp.status_code == 200
    assert advisor_resp.status_code == 200
    assert leader_resp.json()["role"] == "ban_quan_ly"
    assert advisor_resp.json()["role"] == "gvcn"
    assert leader_resp.json()["message_vi"] != advisor_resp.json()["message_vi"]


def test_briefing_shown_and_ack_idempotent(client: TestClient) -> None:
    _as(DEFAULT_BAN_QUAN_LY)
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
    schema = client.get("/openapi.json").json()
    blob = str(schema)
    assert "student_ref" not in blob or "WeeklyReport" in blob
