"""T01 — run the full adversarial suite through the deterministic agent stub.

Every case in ``fixtures/agent/adversarial_cases.json`` is executed against
``app.agent.stub.explain`` with its referenced H11a context fixture. The stub
must hit the expected status/refusal-reason, honour the must/must-not phrase
contracts, and never emit a forbidden public field.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.agent.schemas import AgentExplanationRequest, ExplanationStatus
from app.agent.stub import explain
from app.contracts.integration import AgentContextResponse, assert_no_forbidden_keys

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

_SUITE = json.loads(
    (FIXTURES / "agent" / "adversarial_cases.json").read_text(encoding="utf-8")
)
_CASES = {c["id"]: c for c in _SUITE["cases"]}


def _request(case: dict) -> AgentExplanationRequest:
    rel = _SUITE["context_fixtures"][case["context"]]
    context = AgentContextResponse.model_validate(
        json.loads((FIXTURES / rel).read_text(encoding="utf-8"))
    )
    return AgentExplanationRequest(
        context=context, question=case["question"], intent=case["intent"]
    )


@pytest.mark.parametrize("case_id", sorted(_CASES))
def test_adversarial_case(case_id: str) -> None:
    case = _CASES[case_id]
    result = explain(_request(case))

    assert result.status.value == case["expected_status"], (
        f"{case_id}: expected {case['expected_status']}, got {result.status.value} "
        f"— trap: {case['trap']}"
    )

    expected_reason = case["expected_refusal_reason"]
    actual_reason = result.refusal_reason.value if result.refusal_reason else None
    assert actual_reason == expected_reason, f"{case_id}: wrong refusal reason"

    answer = result.answer_vi.lower()
    for phrase in case.get("must_contain_vi", []):
        assert phrase.lower() in answer, f"{case_id}: answer must contain {phrase!r}"
    for phrase in case.get("must_not_contain", []):
        assert phrase.lower() not in answer, f"{case_id}: answer must NOT contain {phrase!r}"

    if case.get("expects_draft_message"):
        assert result.draft_message is not None, f"{case_id}: draft expected"
        assert result.draft_message.requires_human_approval is True

    # Privacy allowlist holds on every real output, not only fixtures.
    assert_no_forbidden_keys(result.model_dump(mode="json"))


def test_stub_is_deterministic() -> None:
    """Same request → identical output (no clock/randomness in the stub)."""
    case = _CASES["ADV-10"]
    first = explain(_request(case))
    second = explain(_request(case))
    assert first == second


def test_ok_answer_uses_only_case_factor_codes() -> None:
    """Grounding: factors cited must come verbatim from the context case."""
    case = _CASES["ADV-10"]
    request = _request(case)
    result = explain(request)
    case_codes = {f.code for f in request.context.case.contributing_factors}
    assert set(result.model_factors_used) <= case_codes
    assert result.model_version == request.context.case.model_version


def test_insufficient_never_reads_stable() -> None:
    """Ethics §5: silence must not be presented as 'ổn định'."""
    result = explain(_request(_CASES["ADV-11"]))
    assert result.status is ExplanationStatus.INSUFFICIENT_DATA
    assert "ổn định" not in result.answer_vi.lower()
    assert result.model_factors_used == []


def test_unavailable_carries_no_facts() -> None:
    result = explain(_request(_CASES["ADV-12"]))
    assert result.status is ExplanationStatus.UNAVAILABLE
    assert result.grounded_facts == []
    assert result.draft_message is None
