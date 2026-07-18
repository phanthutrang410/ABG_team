from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.agent.fpt_client import ModelUnavailable
from app.agent.grounded import explain
from app.agent.schemas import AgentExplanationRequest, ExplanationStatus
from app.contracts.integration import AgentContextResponse, assert_no_forbidden_keys

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SUITE = json.loads((FIXTURES / "agent" / "adversarial_cases.json").read_text("utf-8"))
CASES = {case["id"]: case for case in SUITE["cases"]}


class FakeModel:
    def __init__(self, response: str = "", error: bool = False):
        self.response = response
        self.error = error
        self.calls = 0
        self.last_user = ""

    def complete(self, *, system: str, user: str) -> str:
        self.calls += 1
        self.last_user = user
        if self.error:
            raise ModelUnavailable("offline")
        return self.response


def make_request(case_id: str) -> AgentExplanationRequest:
    item = CASES[case_id]
    rel = SUITE["context_fixtures"][item["context"]]
    context = AgentContextResponse.model_validate_json((FIXTURES / rel).read_text("utf-8"))
    return AgentExplanationRequest(
        context=context, question=item["question"], intent=item["intent"]
    )


@pytest.mark.parametrize(
    "case_id",
    [
        "ADV-01",
        "ADV-02",
        "ADV-03",
        "ADV-04",
        "ADV-05",
        "ADV-07",
        "ADV-08",
        "ADV-09",
        "ADV-11",
        "ADV-12",
    ],
)
def test_guardrails_and_non_ready_states_never_call_model(case_id: str) -> None:
    model = FakeModel()
    result = explain(make_request(case_id), model)
    assert result.status.value == CASES[case_id]["expected_status"]
    assert model.calls == 0


def test_ready_explanation_uses_model_text_but_contract_fields_from_case() -> None:
    model = FakeModel(
        json.dumps(
            {
                "answer_vi": "Case cần được con người rà soát theo các tín hiệu được cung cấp.",
                "draft_body_vi": None,
            },
            ensure_ascii=False,
        )
    )
    request = make_request("ADV-10")
    result = explain(request, model)
    assert result.status is ExplanationStatus.OK
    assert request.context.case is not None
    assert set(result.model_factors_used) == {
        factor.code for factor in request.context.case.contributing_factors
    }
    assert result.model_version == request.context.case.model_version
    assert "student_ref" not in model.last_user
    assert_no_forbidden_keys(result.model_dump(mode="json"))


def test_neutral_draft_is_always_human_approval_required() -> None:
    raw = json.dumps(
        {
            "answer_vi": "Đây là bản nháp để anh/chị xem lại.",
            "draft_body_vi": (
                "Chào em, thầy/cô muốn hỏi thăm và lắng nghe nếu em cần hỗ trợ."
            ),
        },
        ensure_ascii=False,
    )
    result = explain(make_request("ADV-06"), FakeModel(raw))
    assert result.draft_message is not None
    assert result.draft_message.requires_human_approval is True


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        '{"answer_vi":"Khả năng bỏ học 87%","draft_body_vi":null}',
        '{"answer_vi":"ok","extra":true,"draft_body_vi":null}',
    ],
)
def test_malformed_or_unsafe_model_output_fails_closed(raw: str) -> None:
    result = explain(make_request("ADV-10"), FakeModel(raw))
    assert result.status is ExplanationStatus.UNAVAILABLE
    assert result.grounded_facts == []


def test_model_outage_fails_closed() -> None:
    result = explain(make_request("ADV-10"), FakeModel(error=True))
    assert result.status is ExplanationStatus.UNAVAILABLE


def test_empty_draft_fails_closed() -> None:
    raw = json.dumps({"answer_vi": "Bản nháp.", "draft_body_vi": ""})
    result = explain(make_request("ADV-06"), FakeModel(raw))
    assert result.status is ExplanationStatus.UNAVAILABLE
