"""H11a — FE/Agent integration contract fixtures + leakage guards."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.contracts.integration import (
    ALLOWED_DISPLAY_FIELDS,
    FORBIDDEN_PUBLIC_FIELDS,
    AgentContextResponse,
    CaseDetailResponse,
    CaseListResponse,
    assert_no_forbidden_keys,
)
from app.contracts.review_overview import ReviewOverviewSummary
from app.contracts.review_case import ReviewCase

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "integration"

LIST_FIXTURES = (
    "case_list_ok.json",
    "case_list_empty.json",
    "case_list_stale.json",
    "case_list_error.json",
)
DETAIL_FIXTURES = (
    "case_detail_ok.json",
    "case_detail_insufficient.json",
    "case_detail_stale.json",
)
AGENT_FIXTURES = (
    "agent_context_ready.json",
    "agent_context_refused.json",
    "agent_context_insufficient.json",
    "agent_context_unavailable.json",
)


def _load(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", LIST_FIXTURES)
def test_case_list_fixtures_validate(name: str) -> None:
    raw = _load(name)
    assert_no_forbidden_keys(raw)
    CaseListResponse.model_validate(raw)


def test_review_overview_summary_fixture_validates() -> None:
    raw = _load("review_overview_summary.ok.json")
    assert_no_forbidden_keys(raw)
    summary = ReviewOverviewSummary.model_validate(raw)
    assert summary.total_students == 460
    assert summary.review_case_count == 35
    assert summary.new_since_previous_snapshot is None


@pytest.mark.parametrize("name", DETAIL_FIXTURES)
def test_case_detail_fixtures_validate(name: str) -> None:
    raw = _load(name)
    assert_no_forbidden_keys(raw)
    CaseDetailResponse.model_validate(raw)


@pytest.mark.parametrize("name", AGENT_FIXTURES)
def test_agent_context_fixtures_validate(name: str) -> None:
    raw = _load(name)
    assert_no_forbidden_keys(raw)
    AgentContextResponse.model_validate(raw)


def test_insufficient_fixtures_null_band_empty_factors() -> None:
    """H06a-r / H11a-r: insufficient → no band; empty factors OK when not ok."""
    for name in (
        "case_detail_insufficient.json",
        "agent_context_insufficient.json",
    ):
        raw = _load(name)
        assert isinstance(raw, dict)
        case = raw["case"]
        assert isinstance(case, dict)
        assert case["review_priority_band"] is None
        assert case["contributing_factors"] == []
        assert case["coverage"]["status"] == "insufficient"
        assert case["data_state"] == "insufficient_data"


def test_allowed_display_fields_match_review_case() -> None:
    assert ALLOWED_DISPLAY_FIELDS == frozenset(ReviewCase.model_fields.keys())
    assert not (ALLOWED_DISPLAY_FIELDS & FORBIDDEN_PUBLIC_FIELDS)


def test_list_ok_rejects_empty_items() -> None:
    with pytest.raises(ValidationError):
        CaseListResponse.model_validate({"items": [], "state": "ok", "problem": None})


def test_list_error_requires_problem() -> None:
    with pytest.raises(ValidationError):
        CaseListResponse.model_validate({"items": [], "state": "error", "problem": None})


def test_detail_rejects_forbidden_extra_on_case() -> None:
    raw = _load("case_detail_ok.json")
    assert isinstance(raw, dict)
    case = raw["case"]
    assert isinstance(case, dict)
    case["model_score"] = 0.91
    with pytest.raises(ValidationError):
        CaseDetailResponse.model_validate(raw)


def test_assert_no_forbidden_keys_detects_nested_score() -> None:
    with pytest.raises(ValueError, match="model_score"):
        assert_no_forbidden_keys({"case": {"model_score": 0.5}})


def test_agent_ready_rejects_problem() -> None:
    raw = _load("agent_context_ready.json")
    assert isinstance(raw, dict)
    raw["problem"] = {
        "code": "refused",
        "reason_codes": [],
        "message_key": None,
    }
    with pytest.raises(ValidationError):
        AgentContextResponse.model_validate(raw)


def test_agent_refused_rejects_case_payload() -> None:
    raw = _load("agent_context_refused.json")
    assert isinstance(raw, dict)
    raw["case"] = _load("case_detail_ok.json")["case"]  # type: ignore[index]
    with pytest.raises(ValidationError):
        AgentContextResponse.model_validate(raw)
