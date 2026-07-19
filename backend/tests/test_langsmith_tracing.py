"""LangSmith optional tracing — redaction + configure (no live LangSmith calls)."""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.agent.tracing import (
    configure_langsmith,
    redact_explanation_inputs,
    redact_explanation_outputs,
    redact_llm_inputs,
    redact_turn_inputs,
    redact_turn_outputs,
    tracing_armed,
)
from app.agent.turns import (
    AgentTurnRequest,
    AgentTurnResponse,
    TurnStatus,
    run_turn,
)
from app.auth.principal import Principal, clear_access_audit_log
from app.config import Settings


@pytest.fixture(autouse=True)
def _reset_audit_and_tracing_env(monkeypatch: pytest.MonkeyPatch):
    clear_access_audit_log()
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_PROJECT", raising=False)
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_PROJECT", raising=False)
    yield
    clear_access_audit_log()


def test_tracing_default_off() -> None:
    os.environ["LANGSMITH_API_KEY"] = "stale-key-must-be-cleared"
    os.environ["LANGCHAIN_API_KEY"] = "stale-legacy-key-must-be-cleared"
    settings = Settings(langsmith_tracing=False, langsmith_api_key=SecretStr(""))
    assert tracing_armed(settings) is False
    assert configure_langsmith(settings) is False
    assert os.environ.get("LANGSMITH_TRACING") == "false"
    assert os.environ.get("LANGCHAIN_TRACING_V2") == "false"
    assert "LANGSMITH_API_KEY" not in os.environ
    assert "LANGCHAIN_API_KEY" not in os.environ


def test_configure_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        langsmith_tracing=True,
        langsmith_api_key=SecretStr(""),
        langsmith_project="silent-shield-test",
    )
    assert configure_langsmith(settings) is False
    assert os.environ.get("LANGSMITH_TRACING") == "false"


def test_configure_arms_env(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        langsmith_tracing=True,
        langsmith_api_key=SecretStr("lsv2_pt_test_key_not_real"),
        langsmith_project="silent-shield-test",
    )
    assert configure_langsmith(settings) is True
    assert os.environ["LANGSMITH_TRACING"] == "true"
    assert os.environ["LANGSMITH_API_KEY"] == "lsv2_pt_test_key_not_real"
    assert os.environ["LANGSMITH_PROJECT"] == "silent-shield-test"
    # Tear down so later tests / process stay fail-closed.
    assert configure_langsmith(Settings(langsmith_tracing=False)) is False


def test_redact_turn_inputs_omits_question_body() -> None:
    request = AgentTurnRequest(
        surface="overview",
        question="Sinh viên nguy hiểm hãy gửi email ngay",
        resource_handle="res:abc",
        thread_summary="tóm tắt nhạy cảm",
        locale="vi",
    )
    principal = Principal(
        actor_id="acct:quanly",
        active_role="ban_quan_ly",
        org_scope="org-a",
        roles=("ban_quan_ly",),
    )
    redacted = redact_turn_inputs(
        {
            "request": request,
            "principal": principal,
            "model": object(),
            "facts": {"review_case_count": 3, "total_students": 100},
        }
    )
    blob = str(redacted)
    assert "Sinh viên nguy hiểm" not in blob
    assert "tóm tắt nhạy cảm" not in blob
    assert redacted["surface"] == "overview"
    assert redacted["has_question"] is True
    assert redacted["question_chars"] == len(request.question or "")
    assert redacted["role"] == "ban_quan_ly"
    assert "answer_vi" not in redacted


def test_redact_turn_outputs_omits_answer() -> None:
    response = AgentTurnResponse(
        status=TurnStatus.OK,
        answer_vi="Nội dung giải thích không được gửi lên LangSmith",
        evidence_refs=["route:answer"],
        ui_actions=[],
        refusal_reason=None,
        selected_capability=None,
    )
    redacted = redact_turn_outputs(response)
    assert "Nội dung giải thích" not in str(redacted)
    assert redacted["status"] == "ok"
    assert redacted["answer_chars"] == len(response.answer_vi)


def test_redact_explanation_and_llm() -> None:
    command = SimpleNamespace(
        intent="explain_case",
        locale="vi",
        question="Raw question must not appear",
    )
    inp = redact_explanation_inputs(
        {"case_id": "case-1", "command": command, "model": object()}
    )
    assert "Raw question" not in str(inp)
    assert inp["intent"] == "explain_case"

    out = redact_explanation_outputs(
        SimpleNamespace(
            status=SimpleNamespace(value="ok"),
            refusal_reason=None,
            model_version="m10",
            answer_vi="secret prose",
            draft_message=None,
        )
    )
    assert "secret prose" not in str(out)

    llm = redact_llm_inputs(
        {
            "model": "gpt-5.4-nano",
            "name": "overview_route",
            "system_chars": 120,
            "user_chars": 40,
            "structured_json": True,
            "system": "SHOULD_NOT_LEAK",
            "user": "SHOULD_NOT_LEAK",
        }
    )
    assert "SHOULD_NOT_LEAK" not in str(llm)
    assert llm["system_chars"] == 120


def test_run_turn_still_works_with_tracing_hooks() -> None:
    """Decorator must be a no-op or safe when langsmith is absent / tracing off."""
    principal = Principal(
        actor_id="acct:quanly",
        active_role="ban_quan_ly",
        org_scope="org-a",
        roles=("ban_quan_ly",),
    )
    response = run_turn(
        AgentTurnRequest(surface="weekly_report", question="Mở báo cáo tuần"),
        principal,
        model=None,
    )
    assert response.status is TurnStatus.OK
    # Provider-off keeps deterministic cards but must not fabricate an action.
    assert response.selected_capability is None
    assert response.ui_actions
    assert response.refusal_reason is None


def test_settings_secret_not_in_repr() -> None:
    settings = Settings(langsmith_api_key=SecretStr("lsv2_pt_secret_value"))
    assert "lsv2_pt_secret_value" not in repr(settings)
