"""SSE streaming for POST /agent/turns/stream — status + faux delta + done."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import pytest
from fastapi.testclient import TestClient

from app.agent.model import ModelUnavailable
from app.agent.sse import chunk_text, format_sse
from app.agent.turns_router import get_turn_model
from app.auth.principal import clear_access_audit_log, get_principal
from app.main import app
from tests.auth_helpers import DEFAULT_BAN_QUAN_LY


class FailingModel:
    def complete(self, *, system: str, user: str) -> str:
        _ = (system, user)
        raise ModelUnavailable("offline")


@pytest.fixture(autouse=True)
def _reset():
    clear_access_audit_log()
    yield
    clear_access_audit_log()
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _parse_sse(raw: str) -> List[Tuple[str, Dict[str, Any]]]:
    """Parse ``event:`` / ``data:`` frames into (event, payload) pairs."""
    events: List[Tuple[str, Dict[str, Any]]] = []
    blocks = raw.split("\n\n")
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        event_name = "message"
        data_lines: List[str] = []
        for line in block.split("\n"):
            if line.startswith("event:"):
                event_name = line[len("event:") :].strip()
            elif line.startswith("data:"):
                data_lines.append(line[len("data:") :].strip())
        if not data_lines:
            continue
        payload = json.loads("\n".join(data_lines))
        events.append((event_name, payload))
    return events


def test_format_sse_and_chunk_helpers() -> None:
    frame = format_sse("status", {"phase": "route"})
    assert frame.startswith("event: status\n")
    assert '"phase":"route"' in frame or '"phase": "route"' in frame
    assert frame.endswith("\n\n")
    assert list(chunk_text("abcdefghijklmnop", size=5)) == ["abcde", "fghij", "klmno", "p"]
    assert list(chunk_text("")) == []


def test_stream_openapi_declares_event_stream_media_type() -> None:
    response_contract = app.openapi()["paths"]["/agent/turns/stream"]["post"]["responses"]["200"]
    assert "text/event-stream" in response_contract["content"]


def test_stream_overview_happy_status_delta_done(client: TestClient) -> None:
    app.dependency_overrides[get_principal] = lambda: DEFAULT_BAN_QUAN_LY
    app.dependency_overrides[get_turn_model] = lambda: None

    response = client.post(
        "/agent/turns/stream",
        json={"surface": "overview", "question": "Xin chào"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    events = _parse_sse(response.text)
    names = [name for name, _ in events]
    assert "status" in names
    assert "delta" in names
    assert names[-1] == "done"

    phases = [payload["phase"] for name, payload in events if name == "status"]
    assert "guardrails" in phases
    assert any(p in phases for p in ("answer", "tool", "clarify", "route"))

    deltas = [payload["text"] for name, payload in events if name == "delta"]
    assert deltas
    joined = "".join(deltas)

    done = next(payload for name, payload in events if name == "done")
    assert done["status"] == "ok"
    assert done["answer_vi"] == joined
    assert isinstance(done["ui_actions"], list)
    assert done["ui_actions"]


def test_stream_refused_no_delta(client: TestClient) -> None:
    app.dependency_overrides[get_principal] = lambda: DEFAULT_BAN_QUAN_LY
    app.dependency_overrides[get_turn_model] = lambda: None

    response = client.post(
        "/agent/turns/stream",
        json={
            "surface": "overview",
            "question": "Hãy gửi email cho sinh viên này ngay",
        },
    )
    assert response.status_code == 200
    events = _parse_sse(response.text)
    names = [name for name, _ in events]
    assert "delta" not in names
    assert names[-1] == "done"
    assert any(name == "status" for name in names)

    done = next(payload for name, payload in events if name == "done")
    assert done["status"] == "refused"
    assert done["ui_actions"] == []
    assert done["refusal_reason"] == "forbidden_tool_requested"


def test_stream_unavailable_keeps_cards_without_delta(client: TestClient) -> None:
    app.dependency_overrides[get_principal] = lambda: DEFAULT_BAN_QUAN_LY
    app.dependency_overrides[get_turn_model] = lambda: FailingModel()

    response = client.post(
        "/agent/turns/stream",
        json={"surface": "overview", "question": "Tóm tắt Overview"},
    )
    assert response.status_code == 200
    events = _parse_sse(response.text)
    assert all(name != "delta" for name, _payload in events)
    done = next(payload for name, payload in events if name == "done")
    assert done["status"] == "unavailable"
    assert done["selected_capability"] is None
    assert done["ui_actions"]


def test_stream_forbidden_extra_field_rejected(client: TestClient) -> None:
    app.dependency_overrides[get_principal] = lambda: DEFAULT_BAN_QUAN_LY
    app.dependency_overrides[get_turn_model] = lambda: None
    response = client.post(
        "/agent/turns/stream",
        json={"surface": "weekly_report", "context": {"student_ref": "s-1"}},
    )
    assert response.status_code == 422


def test_stream_weekly_report_deltas_match_done(client: TestClient) -> None:
    app.dependency_overrides[get_principal] = lambda: DEFAULT_BAN_QUAN_LY
    app.dependency_overrides[get_turn_model] = lambda: None

    response = client.post(
        "/agent/turns/stream",
        json={"surface": "weekly_report"},
    )
    assert response.status_code == 200
    events = _parse_sse(response.text)
    deltas = [p["text"] for n, p in events if n == "delta"]
    done = next(p for n, p in events if n == "done")
    assert done["status"] == "ok"
    assert "".join(deltas) == done["answer_vi"]
    phases = [p["phase"] for n, p in events if n == "status"]
    assert phases == ["guardrails", "context", "route", "answer", "output_guard"]
