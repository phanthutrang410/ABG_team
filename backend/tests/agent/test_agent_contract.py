"""Contract tests for the explanation agent (T03).

Scope: validate the AgentExplanation output contract, its JSON fixtures, the
adversarial suite, and the privacy allowlist (no forbidden public field in any
agent-facing fixture). Input contexts come from Hoàng's validated H11a
fixtures under ``tests/fixtures/integration/`` — referenced, not duplicated.

Live LLM behaviour is out of scope (T01/T02 run this suite with a mocked
model; live eval only when the task allows — AGENTS.md §4).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.agent.schemas import (
    AgentExplanation,
    AgentExplanationRequest,
    ExplanationStatus,
    RefusalReason,
)
from app.contracts.integration import (
    AgentContextResponse,
    assert_no_forbidden_keys,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
AGENT_FIXTURES = FIXTURES / "agent"

EXPLANATION_FIXTURES = [
    "agent_explanation.ok.json",
    "agent_explanation.insufficient_data.json",
    "agent_explanation.refusal_diagnose.json",
    "agent_explanation.draft_message.json",
    "agent_explanation.unavailable.json",
]


def _load(name: str) -> dict:
    return json.loads((AGENT_FIXTURES / name).read_text(encoding="utf-8"))


def _adversarial() -> dict:
    return _load("adversarial_cases.json")


# --- output contract & fixtures -------------------------------------------


@pytest.mark.parametrize("name", EXPLANATION_FIXTURES)
def test_explanation_fixture_validates(name: str) -> None:
    """Every explanation fixture must parse against the output contract."""
    obj = AgentExplanation.model_validate(_load(name))
    assert obj.answer_vi
    assert obj.disclaimer_vi


@pytest.mark.parametrize("name", EXPLANATION_FIXTURES)
def test_explanation_fixture_has_no_forbidden_field(name: str) -> None:
    """Privacy allowlist (H11a §2.1): no forbidden key anywhere in output."""
    assert_no_forbidden_keys(_load(name))


def test_refused_fixture_has_reason() -> None:
    obj = AgentExplanation.model_validate(_load("agent_explanation.refusal_diagnose.json"))
    assert obj.status is ExplanationStatus.REFUSED
    assert obj.refusal_reason is RefusalReason.DIAGNOSE_HEALTH


def test_draft_message_requires_human_approval() -> None:
    obj = AgentExplanation.model_validate(_load("agent_explanation.draft_message.json"))
    assert obj.draft_message is not None
    assert obj.draft_message.requires_human_approval is True


def test_unavailable_fixture_carries_nothing() -> None:
    """Ethics §5: nothing may be invented when no data was accessible."""
    obj = AgentExplanation.model_validate(_load("agent_explanation.unavailable.json"))
    assert obj.status is ExplanationStatus.UNAVAILABLE
    assert obj.grounded_facts == []
    assert obj.model_factors_used == []
    assert obj.draft_message is None


# --- invariants enforced by the model validator ----------------------------


def test_refused_status_requires_reason() -> None:
    with pytest.raises(ValidationError):
        AgentExplanation(status="refused", answer_vi="x")


def test_reason_forbidden_when_not_refused() -> None:
    with pytest.raises(ValidationError):
        AgentExplanation(
            status="ok",
            answer_vi="x",
            model_version="ew-term-0.1-uncalibrated",
            refusal_reason="diagnose_mental_health",
        )


def test_draft_only_allowed_on_ok() -> None:
    with pytest.raises(ValidationError):
        AgentExplanation(
            status="insufficient_data",
            answer_vi="x",
            draft_message={"body_vi": "y", "requires_human_approval": True},
        )


def test_draft_approval_flag_cannot_be_false() -> None:
    """No auto-send, ever (Ethics §4): a pre-approved draft is invalid."""
    with pytest.raises(ValidationError):
        AgentExplanation(
            status="ok",
            answer_vi="x",
            model_version="ew-term-0.1-uncalibrated",
            draft_message={"body_vi": "y", "requires_human_approval": False},
        )


def test_ok_requires_model_version() -> None:
    """Explainability NFR: grounded answers carry provenance."""
    with pytest.raises(ValidationError):
        AgentExplanation(status="ok", answer_vi="x")


def test_unavailable_must_not_carry_facts() -> None:
    with pytest.raises(ValidationError):
        AgentExplanation(
            status="unavailable",
            answer_vi="x",
            grounded_facts=[
                {"statement_vi": "y", "source": "coverage", "ref": None}
            ],
        )


# --- request side: reuse Hoàng's H11a envelopes verbatim -------------------


def test_request_wraps_h11a_context() -> None:
    """The agent input is Hoàng's AgentContextResponse — no widening."""
    ready = json.loads(
        (FIXTURES / "integration" / "agent_context_ready.json").read_text(encoding="utf-8")
    )
    req = AgentExplanationRequest(
        context=AgentContextResponse.model_validate(ready),
        question="Vì sao case này cần được rà soát?",
    )
    assert req.intent == "explain_case"
    assert req.locale == "vi"
    # The public case must not expose a raw score even at runtime shape level.
    assert not hasattr(req.context.case, "model_score")


def test_request_rejects_unknown_intent() -> None:
    ready = json.loads(
        (FIXTURES / "integration" / "agent_context_ready.json").read_text(encoding="utf-8")
    )
    with pytest.raises(ValidationError):
        AgentExplanationRequest(
            context=AgentContextResponse.model_validate(ready),
            question="x",
            intent="transition_case",  # H06b forbids agent-driven transitions
        )


# --- adversarial suite ------------------------------------------------------


def test_adversarial_suite_wellformed() -> None:
    """≥5 cases (DoD), unique ids, valid statuses/reasons, valid intents."""
    data = _adversarial()
    cases = data["cases"]
    assert len(cases) >= 5, "T03 DoD requires at least 5 adversarial cases"

    valid_status = {s.value for s in ExplanationStatus}
    valid_reason = {r.value for r in RefusalReason}
    valid_context = set(data["context_fixtures"])
    seen_ids: set[str] = set()
    for c in cases:
        assert c["id"] not in seen_ids, f"duplicate case id {c['id']}"
        seen_ids.add(c["id"])
        assert c["context"] in valid_context, f"{c['id']} unknown context ref"
        assert c["intent"] in ("explain_case", "neutral_draft")
        assert c["expected_status"] in valid_status
        reason = c["expected_refusal_reason"]
        if c["expected_status"] == "refused":
            assert reason in valid_reason, f"{c['id']} refused but reason invalid"
        else:
            assert reason is None, f"{c['id']} not refused but has a reason"


def test_adversarial_covers_every_refusal_reason() -> None:
    """Every guardrail category has at least one adversarial probe."""
    covered = {c["expected_refusal_reason"] for c in _adversarial()["cases"]}
    covered.discard(None)
    missing = {r.value for r in RefusalReason} - covered
    assert not missing, f"no adversarial case for refusal reasons: {sorted(missing)}"


def test_adversarial_covers_non_refusal_outcomes() -> None:
    """Suite must also probe over-refusal (ok) and fail-closed paths."""
    statuses = {c["expected_status"] for c in _adversarial()["cases"]}
    assert {"ok", "insufficient_data", "unavailable"} <= statuses


def test_adversarial_context_fixtures_exist_and_validate() -> None:
    """Referenced H11a fixtures exist and parse as AgentContextResponse."""
    for key, rel in _adversarial()["context_fixtures"].items():
        path = FIXTURES / rel
        assert path.is_file(), f"context fixture missing for {key}: {rel}"
        AgentContextResponse.model_validate(
            json.loads(path.read_text(encoding="utf-8"))
        )


def test_adversarial_file_has_no_forbidden_field() -> None:
    assert_no_forbidden_keys(_adversarial())
