"""H23 — server-derived AgentContext + AgentCommand contract.

Evidence: M02 projection → H02 ReviewCase → AgentContextResponse; state/intent
matrix; forbidden-key scan; exact M02 factor codes/version; fail-closed gates
for H24 (provider_call_allowed == False ⇒ zero model calls).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.agent.context_service import (
    TrustedScope,
    build_agent_context,
    provider_call_allowed,
)
from app.agent.schemas import AgentCommand, AgentExplanationRequest
from app.cases.domain import CaseSnapshot, CaseState
from app.cases.store import CaseStore
from app.contracts.coverage import Coverage
from app.contracts.integration import FORBIDDEN_PUBLIC_FIELDS, assert_no_forbidden_keys
from app.contracts.normalized import NormalizedStudentRecord, NormalizedTermGrade
from app.dwh.read_adapter import ReadAdapterError
from app.ml.scoring import MODEL_VERSION

NOW = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)
SHA = "a" * 64
SOURCE_ID = "v59-empty-program-students"
SCOPE = TrustedScope(source_id=SOURCE_ID)


@pytest.fixture()
def case_store() -> CaseStore:
    s = CaseStore()
    yield s
    s.clear()


def _coverage(**kwargs) -> Coverage:
    base = dict(
        n_valid_terms=2,
        n_courses=4,
        n_attendance_events=0,
        last_term_code="20251",
        last_attendance_at=None,
        status="partial",
        reason_codes=["attendance_source_unapproved"],
    )
    base.update(kwargs)
    return Coverage(**base)


def _declining_grades() -> List[NormalizedTermGrade]:
    return [
        NormalizedTermGrade(term_code="20241", course_ref="c1", credits=3.0, final_grade=9.0),
        NormalizedTermGrade(term_code="20241", course_ref="c2", credits=3.0, final_grade=8.5),
        NormalizedTermGrade(term_code="20251", course_ref="c1", credits=3.0, final_grade=4.0),
        NormalizedTermGrade(term_code="20251", course_ref="c2", credits=3.0, final_grade=3.5),
    ]


def _record(
    student_ref: str,
    *,
    grades: Optional[List[NormalizedTermGrade]] = None,
    coverage: Optional[Coverage] = None,
    advisor_ref: Optional[str] = "adv-internal-secret",
    mapping_repair: bool = False,
) -> NormalizedStudentRecord:
    return NormalizedStudentRecord(
        student_ref=student_ref,
        source_id=SOURCE_ID,
        dataset_version="v59-empty-program-students:abcd1234:epu-1",
        schema_version="epu-1",
        snapshot_sha256=SHA,
        provenance_approved=True,
        term_grades=grades if grades is not None else _declining_grades(),
        attendance_events=[],
        advisor_ref=advisor_ref,
        mapping_repair=mapping_repair,
        coverage=coverage or _coverage(),
    )


def _patch_loader(
    monkeypatch: pytest.MonkeyPatch,
    record: Optional[NormalizedStudentRecord],
    *,
    error: Optional[BaseException] = None,
) -> None:
    def _get(_session, _source_id: str, student_ref: str):
        if error is not None:
            raise error
        if record is None:
            return None
        return record if record.student_ref == student_ref else None

    monkeypatch.setattr("app.agent.context_service.get_normalized_student", _get)
    monkeypatch.setattr("app.cases.routing.get_normalized_student", _get)


def _seed_state(case_store: CaseStore, case_id: str, student_ref: str, state: str) -> None:
    case_store.put(
        CaseSnapshot(
            case_id=case_id,
            state=CaseState(state),
            advisor_ref=None,
            student_ref=student_ref,
            source_id=SOURCE_ID,
        )
    )


# --- AgentCommand -----------------------------------------------------------


def test_agent_command_happy() -> None:
    cmd = AgentCommand(
        intent="explain_case",
        question="Vì sao case này cần được rà soát?",
        locale="vi",
    )
    assert cmd.intent == "explain_case"
    assert cmd.locale == "vi"
    assert 1 <= len(cmd.question) <= 500


def test_agent_command_trims_question() -> None:
    cmd = AgentCommand(intent="explain_case", question="  xin chào  ")
    assert cmd.question == "xin chào"


def test_agent_command_rejects_extra_context_field() -> None:
    with pytest.raises(ValidationError):
        AgentCommand.model_validate(
            {
                "intent": "explain_case",
                "question": "ok",
                "locale": "vi",
                "context": {"status": "ready"},
            }
        )


def test_agent_command_rejects_invalid_intent() -> None:
    with pytest.raises(ValidationError):
        AgentCommand(intent="diagnose", question="ok", locale="vi")  # type: ignore[arg-type]


def test_agent_command_rejects_non_vi_locale() -> None:
    with pytest.raises(ValidationError):
        AgentCommand(intent="explain_case", question="ok", locale="en")  # type: ignore[arg-type]


def test_agent_command_rejects_blank_or_overlong_question() -> None:
    with pytest.raises(ValidationError):
        AgentCommand(intent="explain_case", question="   ", locale="vi")
    with pytest.raises(ValidationError):
        AgentCommand(intent="explain_case", question="x" * 501, locale="vi")


def test_agent_explanation_request_still_accepts_library_context() -> None:
    """Library path keeps AgentExplanationRequest; HTTP uses AgentCommand."""
    from app.contracts.integration import AgentContextResponse

    ctx = AgentContextResponse.model_validate(
        {
            "status": "unavailable",
            "case": None,
            "problem": {"code": "upstream_unavailable", "reason_codes": []},
            "allowed_intents": [],
        }
    )
    req = AgentExplanationRequest(context=ctx, question="?", intent="explain_case")
    assert req.context.status == "unavailable"


# --- build_agent_context happy / M02 codes ---------------------------------


def test_ready_partial_coverage_exact_m02_codes(
    monkeypatch: pytest.MonkeyPatch, case_store: CaseStore
) -> None:
    student = "stu_h23_ok"
    case_id = f"rc-{student}"
    _seed_state(case_store, case_id, student, "pending_review")
    _patch_loader(monkeypatch, _record(student))

    ctx = build_agent_context(
        case_id, SCOPE, session=MagicMock(), case_store=case_store, now=NOW
    )
    payload = ctx.model_dump(mode="json")
    assert_no_forbidden_keys(payload)
    for key in FORBIDDEN_PUBLIC_FIELDS:
        assert key not in payload
        if ctx.case is not None:
            assert key not in ctx.case.model_dump(mode="json")

    assert ctx.status == "ready"
    assert ctx.case is not None
    assert ctx.case.model_version == MODEL_VERSION
    assert MODEL_VERSION == "m02-baseline-0.1"
    codes = {f.code for f in ctx.case.contributing_factors}
    assert "grade_trend_declining" in codes
    assert "grade_trend_negative" not in codes
    assert ctx.allowed_intents == ["explain_case"]
    assert provider_call_allowed(ctx, "explain_case") is True
    assert provider_call_allowed(ctx, "neutral_draft") is False


def test_neutral_draft_only_after_approval_and_valid_advisor(
    monkeypatch: pytest.MonkeyPatch, case_store: CaseStore
) -> None:
    student = "stu_h23_draft"
    case_id = f"rc-{student}"
    _seed_state(case_store, case_id, student, "approved_for_follow_up")
    _patch_loader(monkeypatch, _record(student, advisor_ref="adv-ok"))

    ctx = build_agent_context(
        case_id, SCOPE, session=MagicMock(), case_store=case_store, now=NOW
    )
    assert ctx.status == "ready"
    assert ctx.allowed_intents == ["explain_case", "neutral_draft"]
    assert "advisor_ref" not in ctx.model_dump(mode="json")
    assert provider_call_allowed(ctx, "neutral_draft") is True


def test_neutral_draft_refused_when_mapping_repair(
    monkeypatch: pytest.MonkeyPatch, case_store: CaseStore
) -> None:
    student = "stu_h23_repair"
    case_id = f"rc-{student}"
    _seed_state(case_store, case_id, student, "assigned")
    _patch_loader(
        monkeypatch,
        _record(student, advisor_ref=None, mapping_repair=True),
    )

    ctx = build_agent_context(
        case_id, SCOPE, session=MagicMock(), case_store=case_store, now=NOW
    )
    assert ctx.status == "ready"
    assert ctx.allowed_intents == ["explain_case"]
    assert provider_call_allowed(ctx, "neutral_draft") is False


# --- State / freshness matrix (fail-closed for provider) --------------------


@pytest.mark.parametrize(
    "state",
    [
        "new_signal",
        "pending_review",
        "follow_up_in_progress",
        "monitoring",
    ],
)
def test_explain_case_allowed_active_states(
    monkeypatch: pytest.MonkeyPatch, case_store: CaseStore, state: str
) -> None:
    student = f"stu_{state}"
    case_id = f"rc-{student}"
    _seed_state(case_store, case_id, student, state)
    _patch_loader(monkeypatch, _record(student))
    ctx = build_agent_context(
        case_id, SCOPE, session=MagicMock(), case_store=case_store, now=NOW
    )
    assert ctx.status == "ready"
    assert "explain_case" in ctx.allowed_intents
    assert "neutral_draft" not in ctx.allowed_intents
    assert provider_call_allowed(ctx, "explain_case") is True


@pytest.mark.parametrize("state", ["dismissed", "resolved"])
def test_terminal_states_no_intents(
    monkeypatch: pytest.MonkeyPatch, case_store: CaseStore, state: str
) -> None:
    student = f"stu_{state}"
    case_id = f"rc-{student}"
    _seed_state(case_store, case_id, student, state)
    _patch_loader(monkeypatch, _record(student))
    ctx = build_agent_context(
        case_id, SCOPE, session=MagicMock(), case_store=case_store, now=NOW
    )
    assert ctx.status == "ready"
    assert ctx.allowed_intents == []
    assert provider_call_allowed(ctx, "explain_case") is False
    assert provider_call_allowed(ctx, "neutral_draft") is False


def test_insufficient_coverage_fail_closed(
    monkeypatch: pytest.MonkeyPatch, case_store: CaseStore
) -> None:
    student = "stu_insuf"
    case_id = f"rc-{student}"
    cov = _coverage(
        n_valid_terms=0,
        n_courses=0,
        last_term_code=None,
        status="insufficient",
        reason_codes=["grade_coverage_insufficient", "attendance_source_unapproved"],
    )
    _patch_loader(monkeypatch, _record(student, grades=[], coverage=cov))
    ctx = build_agent_context(
        case_id, SCOPE, session=MagicMock(), case_store=case_store, now=NOW
    )
    assert ctx.status == "insufficient_data"
    assert ctx.allowed_intents == []
    assert provider_call_allowed(ctx, "explain_case") is False
    payload = ctx.model_dump(mode="json")
    assert_no_forbidden_keys(payload)
    if ctx.case is not None:
        assert ctx.case.model_version == MODEL_VERSION
        assert ctx.case.review_priority_band is None


def test_stale_snapshot_fail_closed(
    monkeypatch: pytest.MonkeyPatch, case_store: CaseStore
) -> None:
    student = "stu_stale"
    case_id = f"rc-{student}"
    _seed_state(case_store, case_id, student, "pending_review")
    _patch_loader(monkeypatch, _record(student))
    old = NOW - timedelta(days=30)

    def _proj(record, store, **kwargs):
        from app.cases import review_projection as rp

        kwargs["calculated_at"] = old
        return rp.project_review_case(record, store, **kwargs)

    monkeypatch.setattr("app.agent.context_service.project_review_case", _proj)
    ctx = build_agent_context(
        case_id, SCOPE, session=MagicMock(), case_store=case_store, now=NOW
    )
    assert ctx.status == "insufficient_data"
    assert ctx.problem is not None
    assert ctx.problem.code == "stale_snapshot"
    assert "stale_snapshot" in ctx.problem.reason_codes
    assert ctx.allowed_intents == []
    assert provider_call_allowed(ctx, "explain_case") is False
    assert_no_forbidden_keys(ctx.model_dump(mode="json"))


def test_empty_below_threshold_fail_closed(
    monkeypatch: pytest.MonkeyPatch, case_store: CaseStore
) -> None:
    student = "stu_low"
    grades = [
        NormalizedTermGrade(term_code="20241", course_ref="c1", credits=3.0, final_grade=8.0),
        NormalizedTermGrade(term_code="20251", course_ref="c1", credits=3.0, final_grade=8.1),
    ]
    _patch_loader(monkeypatch, _record(student, grades=grades))
    ctx = build_agent_context(
        f"rc-{student}", SCOPE, session=MagicMock(), case_store=case_store, now=NOW
    )
    assert ctx.status == "empty"
    assert ctx.case is None
    assert ctx.allowed_intents == []
    assert provider_call_allowed(ctx, "explain_case") is False


def test_invalid_case_id_empty() -> None:
    ctx = build_agent_context(
        "not-a-case", SCOPE, session=MagicMock(), case_store=CaseStore(), now=NOW
    )
    assert ctx.status == "empty"
    assert ctx.allowed_intents == []
    assert provider_call_allowed(ctx, "explain_case") is False


def test_student_not_found_empty(
    monkeypatch: pytest.MonkeyPatch, case_store: CaseStore
) -> None:
    _patch_loader(monkeypatch, None)
    ctx = build_agent_context(
        "rc-missing", SCOPE, session=MagicMock(), case_store=case_store, now=NOW
    )
    assert ctx.status == "empty"
    assert ctx.allowed_intents == []


def test_upstream_error_unavailable(
    monkeypatch: pytest.MonkeyPatch, case_store: CaseStore
) -> None:
    _patch_loader(
        monkeypatch,
        None,
        error=ReadAdapterError(["source_unapproved"], "nope"),
    )
    ctx = build_agent_context(
        "rc-anyone", SCOPE, session=MagicMock(), case_store=case_store, now=NOW
    )
    assert ctx.status == "unavailable"
    assert ctx.problem is not None
    assert ctx.problem.code == "upstream_unavailable"
    assert ctx.allowed_intents == []
    assert provider_call_allowed(ctx, "explain_case") is False


def test_query_exception_unavailable(
    monkeypatch: pytest.MonkeyPatch, case_store: CaseStore
) -> None:
    _patch_loader(monkeypatch, None, error=RuntimeError("db down"))
    ctx = build_agent_context(
        "rc-anyone", SCOPE, session=MagicMock(), case_store=case_store, now=NOW
    )
    assert ctx.status == "unavailable"
    assert ctx.allowed_intents == []


def test_missing_trusted_scope_unavailable(case_store: CaseStore) -> None:
    ctx = build_agent_context(
        "rc-stu",
        TrustedScope(source_id="  "),
        session=MagicMock(),
        case_store=case_store,
        now=NOW,
    )
    assert ctx.status == "unavailable"
    assert ctx.allowed_intents == []


def test_neutral_draft_before_approval_not_provider_ready(
    monkeypatch: pytest.MonkeyPatch, case_store: CaseStore
) -> None:
    """pending_review + valid advisor still must not allow neutral_draft."""
    student = "stu_early"
    case_id = f"rc-{student}"
    _seed_state(case_store, case_id, student, "pending_review")
    _patch_loader(monkeypatch, _record(student, advisor_ref="adv-ok"))
    ctx = build_agent_context(
        case_id, SCOPE, session=MagicMock(), case_store=case_store, now=NOW
    )
    assert ctx.allowed_intents == ["explain_case"]
    assert provider_call_allowed(ctx, "neutral_draft") is False
