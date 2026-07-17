"""Process §4 case transition tests (H06b) — domain + API."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.cases.domain import (
    FORBIDDEN_STATE_ALIASES,
    CaseAction,
    CaseSnapshot,
    CaseState,
    TransitionCommand,
    TransitionError,
    TransitionErrorCode,
    apply_transition,
)
from app.cases.store import store
from app.main import app


@pytest.fixture(autouse=True)
def _reset_store() -> None:
    store.clear()
    yield
    store.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _cmd(action: CaseAction, **kwargs) -> TransitionCommand:
    defaults = {"actor": "leader:hoa", "actor_kind": "human"}
    defaults.update(kwargs)
    return TransitionCommand(action=action, **defaults)


def test_happy_path_full_chain() -> None:
    case = CaseSnapshot(case_id="c1", state=CaseState.NEW_SIGNAL)
    case = apply_transition(case, _cmd(CaseAction.QUEUE_FOR_REVIEW))
    assert case.state == CaseState.PENDING_REVIEW

    case = apply_transition(case, _cmd(CaseAction.APPROVE))
    assert case.state == CaseState.APPROVED_FOR_FOLLOW_UP
    assert case.advisor_ref is None  # approve ≠ handoff

    case = apply_transition(case, _cmd(CaseAction.ASSIGN, advisor_ref="adv_42"))
    assert case.state == CaseState.ASSIGNED
    assert case.advisor_ref == "adv_42"
    assert case.mapping_repair_queued is False

    case = apply_transition(case, _cmd(CaseAction.ACCEPT, actor="advisor:adv_42"))
    assert case.state == CaseState.FOLLOW_UP_IN_PROGRESS

    case = apply_transition(case, _cmd(CaseAction.RESOLVE))
    assert case.state == CaseState.RESOLVED


def test_dismiss_from_pending_requires_reason() -> None:
    case = CaseSnapshot(case_id="c2", state=CaseState.PENDING_REVIEW)
    with pytest.raises(TransitionError) as exc:
        apply_transition(case, _cmd(CaseAction.DISMISS))
    assert exc.value.code == TransitionErrorCode.MISSING_REASON

    done = apply_transition(case, _cmd(CaseAction.DISMISS, reason_code="false_alarm"))
    assert done.state == CaseState.DISMISSED
    assert done.reason_code == "false_alarm"


def test_defer_keeps_pending_review_and_sets_review_at() -> None:
    when = datetime(2026, 7, 20, 9, 0, 0)
    case = CaseSnapshot(case_id="c3", state=CaseState.PENDING_REVIEW)
    with pytest.raises(TransitionError) as exc:
        apply_transition(case, _cmd(CaseAction.DEFER))
    assert exc.value.code == TransitionErrorCode.MISSING_REVIEW_AT

    deferred = apply_transition(case, _cmd(CaseAction.DEFER, review_at=when))
    assert deferred.state == CaseState.PENDING_REVIEW
    assert deferred.review_at == when


def test_monitor_then_resolve() -> None:
    until = datetime.utcnow() + timedelta(days=14)
    case = CaseSnapshot(case_id="c4", state=CaseState.FOLLOW_UP_IN_PROGRESS)
    case = apply_transition(case, _cmd(CaseAction.MONITOR, monitoring_until=until))
    assert case.state == CaseState.MONITORING
    assert case.monitoring_until == until
    case = apply_transition(case, _cmd(CaseAction.RESOLVE))
    assert case.state == CaseState.RESOLVED


def test_forbidden_skip_review_to_assigned() -> None:
    case = CaseSnapshot(case_id="c5", state=CaseState.NEW_SIGNAL)
    with pytest.raises(TransitionError) as exc:
        apply_transition(case, _cmd(CaseAction.ASSIGN, advisor_ref="adv_1"))
    assert exc.value.code == TransitionErrorCode.FORBIDDEN_TRANSITION


def test_forbidden_pending_directly_to_assigned() -> None:
    case = CaseSnapshot(case_id="c6", state=CaseState.PENDING_REVIEW)
    with pytest.raises(TransitionError) as exc:
        apply_transition(case, _cmd(CaseAction.ASSIGN, advisor_ref="adv_1"))
    assert exc.value.code == TransitionErrorCode.FORBIDDEN_TRANSITION


def test_assign_without_advisor_ref_queues_mapping_repair() -> None:
    case = CaseSnapshot(case_id="c7", state=CaseState.APPROVED_FOR_FOLLOW_UP)
    with pytest.raises(TransitionError) as exc:
        apply_transition(case, _cmd(CaseAction.ASSIGN))
    assert exc.value.code == TransitionErrorCode.MISSING_ADVISOR_REF
    assert exc.value.mapping_repair_queued is True


def test_agent_cannot_transition() -> None:
    case = CaseSnapshot(case_id="c8", state=CaseState.PENDING_REVIEW)
    with pytest.raises(TransitionError) as exc:
        apply_transition(
            case,
            _cmd(CaseAction.APPROVE, actor="agent:fpt", actor_kind="llm"),
        )
    assert exc.value.code == TransitionErrorCode.AGENT_FORBIDDEN


def test_terminal_states_reject_further_actions() -> None:
    for state in (CaseState.DISMISSED, CaseState.RESOLVED):
        case = CaseSnapshot(case_id="t", state=state)
        with pytest.raises(TransitionError) as exc:
            apply_transition(case, _cmd(CaseAction.APPROVE))
        assert exc.value.code == TransitionErrorCode.TERMINAL_STATE


def test_forbidden_aliases_documented() -> None:
    assert "new" in FORBIDDEN_STATE_ALIASES
    assert "in_review" in FORBIDDEN_STATE_ALIASES
    assert "deferred" in FORBIDDEN_STATE_ALIASES
    assert "handed_off" in FORBIDDEN_STATE_ALIASES


def test_api_happy_path_and_forbidden(client: TestClient) -> None:
    r = client.post("/cases", json={"case_id": "api-1", "state": "new_signal"})
    assert r.status_code == 201
    assert r.json()["state"] == "new_signal"

    r = client.post(
        "/cases/api-1/transitions",
        json={"action": "queue_for_review", "actor": "system", "actor_kind": "system"},
    )
    assert r.status_code == 200
    assert r.json()["state"] == "pending_review"

    r = client.post(
        "/cases/api-1/transitions",
        json={"action": "approve", "actor": "leader:1"},
    )
    assert r.status_code == 200
    assert r.json()["state"] == "approved_for_follow_up"

    # Missing advisor_ref → 409, stay approved, mapping-repair queued
    r = client.post(
        "/cases/api-1/transitions",
        json={"action": "assign", "actor": "coord:1"},
    )
    assert r.status_code == 409
    body = r.json()["detail"]
    assert body["code"] == "missing_advisor_ref"
    assert body["mapping_repair_queued"] is True
    assert body["state"] == "approved_for_follow_up"

    got = client.get("/cases/api-1")
    assert got.json()["state"] == "approved_for_follow_up"
    assert got.json()["mapping_repair_queued"] is True

    r = client.post(
        "/cases/api-1/transitions",
        json={"action": "assign", "actor": "coord:1", "advisor_ref": "adv_9"},
    )
    assert r.status_code == 200
    assert r.json()["state"] == "assigned"
    assert r.json()["advisor_ref"] == "adv_9"
    assert r.json()["mapping_repair_queued"] is False


def test_api_rejects_forbidden_alias_and_skip(client: TestClient) -> None:
    client.post("/cases", json={"case_id": "api-2", "state": "new_signal"})
    r = client.post(
        "/cases/api-2/transitions",
        json={"action": "in_review", "actor": "leader:1"},
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "forbidden_alias"

    r = client.post(
        "/cases/api-2/transitions",
        json={"action": "assign", "actor": "leader:1", "advisor_ref": "adv_x"},
    )
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "forbidden_transition"


def test_api_defer_and_dismiss(client: TestClient) -> None:
    client.post("/cases", json={"case_id": "api-3", "state": "pending_review"})
    r = client.post(
        "/cases/api-3/transitions",
        json={
            "action": "defer",
            "actor": "leader:1",
            "review_at": "2026-07-21T10:00:00",
        },
    )
    assert r.status_code == 200
    assert r.json()["state"] == "pending_review"
    assert r.json()["review_at"].startswith("2026-07-21")

    r = client.post(
        "/cases/api-3/transitions",
        json={"action": "dismiss", "actor": "leader:1", "reason_code": "exception"},
    )
    assert r.status_code == 200
    assert r.json()["state"] == "dismissed"


def test_api_rejects_agent_actor(client: TestClient) -> None:
    client.post("/cases", json={"case_id": "api-4", "state": "pending_review"})
    r = client.post(
        "/cases/api-4/transitions",
        json={"action": "approve", "actor": "bot", "actor_kind": "agent"},
    )
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "agent_forbidden"


def test_create_rejects_legacy_state_alias(client: TestClient) -> None:
    r = client.post("/cases", json={"case_id": "bad", "state": "handed_off"})
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "forbidden_alias"
