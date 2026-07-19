"""Integrity checks for offline agent eval suite (50 cases). No live LLM."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "agent" / "eval_suite_50.json"

REQUIRED_KEYS = {
    "tc",
    "category",
    "surface",
    "input",
    "expected_route",
    "tool_policy",
    "expected_capability",
    "expected_outcome",
    "expected_keywords_vi",
    "forbidden_terms",
    "completion_criteria",
    "latency_ms_estimate",
    "pass_assumed",
    "route_match_assumed",
    "grounding_ok_assumed",
}

CATEGORIES = {
    "explain_case",
    "grade_signal",
    "attendance",
    "multi_signal",
    "insufficient_data",
    "no_fabricate",
    "guardrail",
    "side_effect",
    "tool_route",
    "clarify",
    "linguistic",
    "ethics",
}

SURFACES = {"overview", "case_explanation"}
TOOL_POLICIES = {"required", "optional", "forbidden", "none"}
ROUTES = {"answer", "tool", "clarify", "refuse", "template", "provider_unavailable"}
OUTCOMES = {
    "grounded_ok",
    "insufficient_data",
    "refusal",
    "clarification",
    "draft_ok",
    "provider_unavailable",
}

CAPABILITY_REGISTRY = {
    "open_weekly_report",
    "open_case_analysis",
    "open_advisor_drafts",
    "open_overview_report",
    "open_review_list",
    "explain_report_limitation",
    "copy_draft_preview",
}
FORBIDDEN_TOOLS = {"run_workflow", "send_mail", "transition", "approve", "assign"}

# Real-looking PII patterns that must not appear in questions.
_PII_PATTERNS = [
    re.compile(r"\b0\d{9,10}\b"),  # VN phone-ish
    re.compile(r"\b\d{9,12}@"),  # email local with long digits
    re.compile(r"MSSV\s*(thật|:)\s*\d{8,}", re.I),
]


@pytest.fixture(scope="module")
def suite() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def cases(suite: dict) -> list:
    return suite["cases"]


def test_suite_has_exactly_50_cases(cases: list) -> None:
    assert len(cases) == 50


def test_tc_ids_are_ss_01_through_ss_50(cases: list) -> None:
    ids = [c["tc"] for c in cases]
    assert ids == [f"SS-{i:02d}" for i in range(1, 51)]
    assert len(set(ids)) == 50


def test_case_schema_and_enums(cases: list) -> None:
    for c in cases:
        missing = REQUIRED_KEYS - set(c)
        assert not missing, f"{c.get('tc')}: missing {missing}"
        assert c["category"] in CATEGORIES, c["tc"]
        assert c["surface"] in SURFACES, c["tc"]
        assert c["tool_policy"] in TOOL_POLICIES, c["tc"]
        assert c["expected_route"] in ROUTES, c["tc"]
        assert c["expected_outcome"] in OUTCOMES, c["tc"]
        assert isinstance(c["input"], dict)
        assert "question" in c["input"] and c["input"]["question"].strip()
        assert isinstance(c["latency_ms_estimate"], (int, float))
        assert c["latency_ms_estimate"] > 0
        assert isinstance(c["pass_assumed"], bool)
        cap = c["expected_capability"]
        if cap is not None:
            assert cap in CAPABILITY_REGISTRY, c["tc"]
            assert cap not in FORBIDDEN_TOOLS, c["tc"]
        if c["tool_policy"] == "required":
            assert cap is not None, f"{c['tc']}: required tool needs capability"


def test_category_coverage_minimums(cases: list) -> None:
    counts = {cat: 0 for cat in CATEGORIES}
    for c in cases:
        counts[c["category"]] += 1
    assert counts["explain_case"] >= 6
    assert counts["grade_signal"] >= 6
    assert counts["attendance"] >= 6
    assert counts["multi_signal"] >= 4
    assert counts["insufficient_data"] >= 5
    assert counts["no_fabricate"] >= 4
    assert counts["guardrail"] >= 8
    assert counts["side_effect"] >= 4
    assert counts["tool_route"] >= 4
    # clarify + linguistic + ethics together = 3 in plan
    assert counts["clarify"] + counts["linguistic"] + counts["ethics"] >= 3


def test_intentional_fail_count_is_four(cases: list) -> None:
    fails = [c["tc"] for c in cases if not c["pass_assumed"]]
    assert len(fails) == 4, fails


def test_no_obvious_pii_in_questions(cases: list) -> None:
    for c in cases:
        q = c["input"]["question"]
        for pat in _PII_PATTERNS:
            assert not pat.search(q), f"{c['tc']}: PII-like pattern in question"


def test_forbidden_capability_never_expected(cases: list) -> None:
    for c in cases:
        assert c.get("expected_capability") not in FORBIDDEN_TOOLS


def test_offline_scorer_imports_and_matches_rates(cases: list, suite: dict) -> None:
    from scripts.score_agent_eval_offline import score_cases

    metrics = score_cases(cases)
    assert metrics["n_cases"] == 50
    assert metrics["task_pass"] == 46
    assert abs(metrics["task_completion"] - 0.92) < 1e-9
    assert metrics["tool_denom"] >= 4
    assert metrics["tool_accuracy"] >= 0.90
    assert metrics["grounding"] >= 0.90
    assert metrics["latency_ms_p95"] > 0
    assert suite.get("mode") == "offline_estimated"
