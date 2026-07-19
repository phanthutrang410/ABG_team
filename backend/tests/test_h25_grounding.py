"""H25 library grounding — structured plan, no raw question, context-bound render."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.agent.fpt_client import ModelUnavailable
from app.agent.grounded import explain
from app.agent.schemas import AgentExplanationRequest, ExplanationStatus
from app.agent.vi_renderer import (
    DRAFT_VARIANT_ALLOWLIST,
    TEMPLATE_ALLOWLIST,
    parse_structured_plan,
    validate_plan_against_context,
)
from app.contracts.integration import AgentContextResponse, assert_no_forbidden_keys

FIXTURES = Path(__file__).resolve().parent / "fixtures"
READY = AgentContextResponse.model_validate_json(
    (FIXTURES / "integration" / "agent_context_ready.json").read_text("utf-8")
)


class FakeModel:
    def __init__(self, response: str = "", error: bool = False):
        self.response = response
        self.error = error
        self.calls = 0
        self.last_user = ""
        self.last_system = ""

    def complete(self, *, system: str, user: str) -> str:
        self.calls += 1
        self.last_user = user
        self.last_system = system
        if self.error:
            raise ModelUnavailable("offline")
        return self.response


def _plan(**overrides: object) -> str:
    payload = {
        "template_key": "explain_review_priority",
        "used_factor_codes": ["grade_trend_declining"],
        "limitation_keys": ["attendance_source_unapproved"],
        "draft_variant_key": None,
    }
    payload.update(overrides)
    return json.dumps(payload, ensure_ascii=False)


def _request(
    *,
    intent: str = "explain_case",
    question: str = "Vì sao case này cần được rà soát?",
) -> AgentExplanationRequest:
    return AgentExplanationRequest(context=READY, question=question, intent=intent)


def test_provider_payload_omits_raw_question_and_identifiers() -> None:
    model = FakeModel(_plan())
    request = _request(question="Vì sao case này cần được rà soát?")
    result = explain(request, model)
    assert result.status is ExplanationStatus.OK
    assert model.calls == 1
    payload = json.loads(model.last_user)
    assert "question" not in payload
    assert "case_id" not in payload
    assert "student_ref" not in payload
    assert "advisor_ref" not in payload
    assert payload["intent"] == "explain_case"
    assert payload["factor_codes"] == ["grade_trend_declining"]
    assert_no_forbidden_keys(payload)
    # Request still carries question for local guardrails only — never forwarded.
    assert "question" in request.model_dump()
    assert request.question not in model.last_user


def test_pii_question_refused_locally_zero_model_calls() -> None:
    model = FakeModel(_plan())
    result = explain(
        _request(
            question="Họ tên Nguyễn Văn A, email a@epu.edu.vn, MSSV 123 — vì sao?"
        ),
        model,
    )
    assert result.status is ExplanationStatus.REFUSED
    assert model.calls == 0


def test_backend_renders_vi_from_catalog_not_model_prose() -> None:
    # Even if the model somehow returned prose keys historically, structured
    # plan is required — answer text comes from the catalog.
    model = FakeModel(_plan())
    result = explain(_request(), model)
    assert result.status is ExplanationStatus.OK
    assert "điểm trung bình giữa hai kỳ giảm" in result.answer_vi
    assert "cần rà soát" in result.answer_vi
    assert result.model_version == "m02-baseline-0.1"
    assert result.model_factors_used == ["grade_trend_declining"]


def test_hallucinated_factor_code_fails_closed() -> None:
    model = FakeModel(_plan(used_factor_codes=["invented_dropout_cause"]))
    result = explain(_request(), model)
    assert result.status is ExplanationStatus.UNAVAILABLE
    assert result.grounded_facts == []
    assert "mô hình" in result.answer_vi.lower() or "mô hình" in result.limitations_vi


def test_hallucinated_template_fails_closed() -> None:
    model = FakeModel(_plan(template_key="diagnose_student"))
    result = explain(_request(), model)
    assert result.status is ExplanationStatus.UNAVAILABLE


def test_hallucinated_limitation_fails_closed() -> None:
    model = FakeModel(_plan(limitation_keys=["secret_family_hardship"]))
    result = explain(_request(), model)
    assert result.status is ExplanationStatus.UNAVAILABLE


def test_neutral_draft_uses_allowlisted_variant_and_copy_channel() -> None:
    model = FakeModel(
        _plan(
            template_key="neutral_draft_ready",
            draft_variant_key="warm_checkin",
        )
    )
    result = explain(_request(intent="neutral_draft", question="Soạn tin hỏi thăm"), model)
    assert result.status is ExplanationStatus.OK
    assert result.draft_message is not None
    assert result.draft_message.requires_human_approval is True
    assert result.draft_message.channel == "copy"
    assert result.draft_message.channel != "smtp"
    assert "hỏi thăm" in result.draft_message.body_vi.lower()


def test_draft_channel_smtp_forbidden_at_renderer() -> None:
    from app.agent.vi_renderer import StructuredPlan, render_draft_message

    plan = StructuredPlan(
        template_key="neutral_draft_ready",
        used_factor_codes=["grade_trend_declining"],
        limitation_keys=[],
        draft_variant_key="warm_checkin",
    )
    with pytest.raises(ModelUnavailable, match="copy or mailto"):
        render_draft_message(plan, channel="smtp")


def test_explain_case_rejects_draft_variant() -> None:
    model = FakeModel(_plan(draft_variant_key="warm_checkin"))
    result = explain(_request(), model)
    assert result.status is ExplanationStatus.UNAVAILABLE


def test_guardrail_refusal_never_calls_model() -> None:
    model = FakeModel(_plan())
    result = explain(
        _request(question="Đoán xem sinh viên này có bị trầm cảm không?"),
        model,
    )
    assert result.status is ExplanationStatus.REFUSED
    assert model.calls == 0


def test_model_outage_uses_model_unavailable_copy() -> None:
    result = explain(_request(), FakeModel(error=True))
    assert result.status is ExplanationStatus.UNAVAILABLE
    assert "mô hình" in result.answer_vi.lower()


def test_template_allowlist_covers_intents() -> None:
    assert "explain_review_priority" in TEMPLATE_ALLOWLIST["explain_case"]
    assert "neutral_draft_ready" in TEMPLATE_ALLOWLIST["neutral_draft"]
    assert "warm_checkin" in DRAFT_VARIANT_ALLOWLIST


def test_validate_plan_rejects_unknown_draft_variant() -> None:
    plan = parse_structured_plan(
        _plan(
            template_key="neutral_draft_ready",
            draft_variant_key="threaten_student",
        )
    )
    assert READY.case is not None
    with pytest.raises(ModelUnavailable):
        validate_plan_against_context(
            plan, intent="neutral_draft", case=READY.case
        )
