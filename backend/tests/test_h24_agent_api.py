"""H24 — POST /review-cases/{case_id}/explanation HTTP API evidence.

Happy / refused / insufficient / stale / unavailable; OpenAPI forbidden-field
scan; fail-closed branches assert fake_model.calls == 0. Demo identity only
(not production RBAC).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.agent.fpt_client import ModelUnavailable
from app.agent.runtime import get_text_model
from app.cases.domain import CaseSnapshot, CaseState
from app.cases.store import store
from app.config import Settings, get_settings
from app.contracts.coverage import Coverage
from app.contracts.integration import assert_no_forbidden_keys
from app.contracts.normalized import NormalizedStudentRecord, NormalizedTermGrade
from app.database import get_db
from app.dwh.read_adapter import ReadAdapterError
from app.main import app

NOW = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)
SHA = "a" * 64
SOURCE_ID = "v59-empty-program-students"

_FORBIDDEN_REQUEST_FIELDS = frozenset(
    {
        "context",
        "source_id",
        "actor",
        "actor_kind",
        "advisor_ref",
        "student_ref",
        "trusted_scope",
        "model_score",
    }
)


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


def _structured_plan(**overrides: object) -> str:
    payload = {
        "template_key": "explain_review_priority",
        "used_factor_codes": ["grade_trend_declining"],
        "limitation_keys": ["attendance_source_unapproved"],
        "draft_variant_key": None,
    }
    payload.update(overrides)
    return json.dumps(payload, ensure_ascii=False)


@pytest.fixture(autouse=True)
def _reset_store() -> None:
    store.clear()
    yield
    store.clear()


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
    app.dependency_overrides.clear()


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


def _seed_state(case_id: str, student_ref: str, state: str) -> None:
    store.put(
        CaseSnapshot(
            case_id=case_id,
            state=CaseState(state),
            advisor_ref=None,
            student_ref=student_ref,
            source_id=SOURCE_ID,
        )
    )


def _client_with_model(fake: FakeModel) -> TestClient:
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_text_model] = lambda: fake
    return TestClient(app)


def _body(
    *,
    intent: str = "explain_case",
    question: str = "Vì sao case này cần được rà soát?",
    locale: str = "vi",
) -> dict:
    return {"intent": intent, "question": question, "locale": locale}


# --- OpenAPI -----------------------------------------------------------------


def test_openapi_explanation_request_omits_forbidden_fields() -> None:
    client = TestClient(app)
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    assert "/review-cases/{case_id}/explanation" in paths
    post = paths["/review-cases/{case_id}/explanation"]["post"]
    body_schema_ref = post["requestBody"]["content"]["application/json"]["schema"]
    # Resolve $ref if present
    if "$ref" in body_schema_ref:
        ref = body_schema_ref["$ref"].split("/")[-1]
        props = schema["components"]["schemas"][ref].get("properties", {})
        required = schema["components"]["schemas"][ref].get("required", [])
        extra = schema["components"]["schemas"][ref].get("additionalProperties")
    else:
        props = body_schema_ref.get("properties", {})
        required = body_schema_ref.get("required", [])
        extra = body_schema_ref.get("additionalProperties")

    assert set(props.keys()) <= {"intent", "question", "locale"}
    for field in _FORBIDDEN_REQUEST_FIELDS:
        assert field not in props
    assert "intent" in required or "intent" in props
    # AgentCommand uses extra=forbid → OpenAPI additionalProperties false when exported
    assert extra is False or extra is None
    # Response must be AgentExplanation, not raw context
    assert "responses" in post


# --- Happy path --------------------------------------------------------------


def test_happy_explain_case_calls_model_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    student = "stu_h24_ok"
    case_id = f"rc-{student}"
    _seed_state(case_id, student, "pending_review")
    _patch_loader(monkeypatch, _record(student))
    monkeypatch.setattr(
        "app.agent.context_service.is_snapshot_stale",
        lambda *_a, **_k: False,
    )
    fake = FakeModel(_structured_plan())
    client = _client_with_model(fake)
    res = client.post(f"/review-cases/{case_id}/explanation", json=_body())
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert fake.calls == 1
    assert_no_forbidden_keys(body)
    for key in ("advisor_ref", "source_id", "actor", "context"):
        assert key not in body
    assert "question" not in fake.last_user


# --- Fail-closed (0 model calls) ---------------------------------------------


def test_refused_guardrail_zero_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    student = "stu_h24_refuse"
    case_id = f"rc-{student}"
    _seed_state(case_id, student, "pending_review")
    _patch_loader(monkeypatch, _record(student))
    monkeypatch.setattr(
        "app.agent.context_service.is_snapshot_stale",
        lambda *_a, **_k: False,
    )
    fake = FakeModel(_structured_plan())
    client = _client_with_model(fake)
    res = client.post(
        f"/review-cases/{case_id}/explanation",
        json=_body(question="Em này có trầm cảm không?"),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "refused"
    assert fake.calls == 0


def test_forbidden_intent_neutral_draft_zero_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """pending_review must refuse neutral_draft before any model call."""
    student = "stu_h24_draft"
    case_id = f"rc-{student}"
    _seed_state(case_id, student, "pending_review")
    _patch_loader(monkeypatch, _record(student, advisor_ref="adv-ok"))
    monkeypatch.setattr(
        "app.agent.context_service.is_snapshot_stale",
        lambda *_a, **_k: False,
    )
    fake = FakeModel(_structured_plan())
    client = _client_with_model(fake)
    res = client.post(
        f"/review-cases/{case_id}/explanation",
        json=_body(intent="neutral_draft", question="Soạn tin hỏi thăm trung lập"),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "refused"
    assert fake.calls == 0


def test_insufficient_data_zero_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    student = "stu_h24_insuf"
    case_id = f"rc-{student}"
    cov = _coverage(
        n_valid_terms=0,
        n_courses=0,
        last_term_code=None,
        status="insufficient",
        reason_codes=["grade_coverage_insufficient"],
    )
    _patch_loader(monkeypatch, _record(student, grades=[], coverage=cov))
    fake = FakeModel(_structured_plan())
    client = _client_with_model(fake)
    res = client.post(f"/review-cases/{case_id}/explanation", json=_body())
    assert res.status_code == 200
    assert res.json()["status"] == "insufficient_data"
    assert fake.calls == 0


def test_stale_snapshot_zero_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    student = "stu_h24_stale"
    case_id = f"rc-{student}"
    _seed_state(case_id, student, "pending_review")
    _patch_loader(monkeypatch, _record(student))
    old = NOW - timedelta(days=30)

    def _proj(record, case_store, **kwargs):
        from app.cases import review_projection as rp

        kwargs["calculated_at"] = old
        return rp.project_review_case(record, case_store, **kwargs)

    monkeypatch.setattr("app.agent.context_service.project_review_case", _proj)
    fake = FakeModel(_structured_plan())
    client = _client_with_model(fake)
    res = client.post(f"/review-cases/{case_id}/explanation", json=_body())
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "insufficient_data"
    assert fake.calls == 0


def test_context_unavailable_zero_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_loader(
        monkeypatch,
        None,
        error=ReadAdapterError(["source_unapproved"], "nope"),
    )
    fake = FakeModel(_structured_plan())
    client = _client_with_model(fake)
    res = client.post("/review-cases/rc-anyone/explanation", json=_body())
    assert res.status_code == 200
    assert res.json()["status"] == "unavailable"
    assert fake.calls == 0


def test_client_forged_context_rejected_422() -> None:
    fake = FakeModel(_structured_plan())
    client = _client_with_model(fake)
    res = client.post(
        "/review-cases/rc-stu/explanation",
        json={
            **_body(),
            "context": {"status": "ready"},
            "source_id": "evil",
            "advisor_ref": "adv-leak",
        },
    )
    assert res.status_code == 422
    assert fake.calls == 0


def test_missing_fpt_key_fail_closed_no_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without DI model override, empty FPT key → unavailable (not raw 500)."""
    from pydantic import SecretStr

    student = "stu_h24_nokey"
    case_id = f"rc-{student}"
    _seed_state(case_id, student, "pending_review")
    _patch_loader(monkeypatch, _record(student))
    monkeypatch.setattr(
        "app.agent.context_service.is_snapshot_stale",
        lambda *_a, **_k: False,
    )

    empty_settings = Settings(fpt_api_key=SecretStr(""))
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_settings] = lambda: empty_settings
    app.dependency_overrides.pop(get_text_model, None)
    client = TestClient(app)
    res = client.post(f"/review-cases/{case_id}/explanation", json=_body())
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "unavailable"
    assert "500" not in body.get("answer_vi", "")
    assert_no_forbidden_keys(body)


def test_demo_identity_limitation_documented_in_module() -> None:
    """H24 must not claim production RBAC — module docstring is the limitation note."""
    import app.agent.runtime as runtime

    doc = (runtime.__doc__ or "").lower()
    assert "not" in doc and "production rbac" in doc
    assert "demo" in doc
