"""H26 — Agent HTTP E2E (mocked FPT) + release-gate evidence.

Vertical slice: M02 scoring factors → H02 ReviewCase projection →
server AgentContext → fake structured FPT plan → POST explanation.

Covers happy path, adversarial/fail-closed (0 calls), and
transport/model_unavailable. Live FPT is intentionally not exercised
here — SKIP unless an approved key/deploy window is granted separately.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.agent.fpt_client import ModelUnavailable
from app.agent.runtime import get_text_model
from app.cases.domain import CaseSnapshot, CaseState
from app.cases.store import store
from app.contracts.coverage import Coverage
from app.contracts.integration import assert_no_forbidden_keys
from app.contracts.normalized import NormalizedStudentRecord, NormalizedTermGrade
from app.database import get_db
from app.main import app
from app.ml.scoring import MODEL_VERSION

NOW = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)
SHA = "a" * 64
SOURCE_ID = "v59-empty-program-students"

# Live FPT smoke is out of scope for the default H26 gate.
pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


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
def _clear_overrides() -> None:
    yield
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
    """Grades that produce M02 factor ``grade_trend_declining``."""
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
        mapping_repair=False,
        coverage=coverage or _coverage(),
    )


def _patch_loader(
    monkeypatch: pytest.MonkeyPatch,
    record: Optional[NormalizedStudentRecord],
) -> None:
    def _get(_session, _source_id: str, student_ref: str):
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


def _fresh(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.agent.context_service.is_snapshot_stale",
        lambda *_a, **_k: False,
    )


# --- Health / OpenAPI (release gate surface) ---------------------------------


def test_h26_health_ok() -> None:
    res = TestClient(app).get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body.get("status") == "ok"
    assert "silent-shield" in str(body.get("service", "")).lower() or body.get(
        "service"
    )


def test_h26_openapi_exposes_explanation_route() -> None:
    schema = TestClient(app).get("/openapi.json").json()
    assert "/review-cases/{case_id}/explanation" in schema["paths"]
    post = schema["paths"]["/review-cases/{case_id}/explanation"]["post"]
    body_ref = post["requestBody"]["content"]["application/json"]["schema"]
    if "$ref" in body_ref:
        name = body_ref["$ref"].split("/")[-1]
        props = schema["components"]["schemas"][name].get("properties", {})
    else:
        props = body_ref.get("properties", {})
    assert set(props.keys()) <= {"intent", "question", "locale"}
    for forbidden in ("context", "source_id", "advisor_ref", "actor", "student_ref"):
        assert forbidden not in props


# --- Happy path: M02 → H02 → context → fake FPT → HTTP ----------------------


def test_h26_e2e_happy_m02_through_http(monkeypatch: pytest.MonkeyPatch) -> None:
    """Full mocked vertical slice with real M02 factor/version on the wire."""
    assert MODEL_VERSION == "m02-baseline-0.1"
    student = "stu_h26_ok"
    case_id = f"rc-{student}"
    _seed_state(case_id, student, "pending_review")
    _patch_loader(monkeypatch, _record(student))
    _fresh(monkeypatch)

    fake = FakeModel(_structured_plan())
    client = _client_with_model(fake)
    res = client.post(f"/review-cases/{case_id}/explanation", json=_body())

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["model_version"] == MODEL_VERSION
    # Deterministic from H02/M02 case factors (stub baseline), not plan prose.
    factors = body["model_factors_used"]
    assert "grade_trend_declining" in factors
    assert "grade_trend_negative" not in factors
    assert "xu hướng điểm" in body["answer_vi"].lower() or "điểm" in body["answer_vi"]
    assert fake.calls == 1
    assert_no_forbidden_keys(body)
    for leak in ("advisor_ref", "source_id", "context", "student_ref"):
        assert leak not in body

    provider_payload = json.loads(fake.last_user)
    assert "question" not in provider_payload
    assert "case_id" not in provider_payload
    assert "student_ref" not in provider_payload
    assert "advisor_ref" not in provider_payload
    assert "grade_trend_declining" in provider_payload["factor_codes"]
    assert "Vì sao" not in fake.last_user


def test_h26_e2e_neutral_draft_after_approval(monkeypatch: pytest.MonkeyPatch) -> None:
    student = "stu_h26_draft"
    case_id = f"rc-{student}"
    _seed_state(case_id, student, "approved_for_follow_up")
    _patch_loader(monkeypatch, _record(student, advisor_ref="adv-ok"))
    _fresh(monkeypatch)

    fake = FakeModel(
        _structured_plan(
            template_key="neutral_draft_ready",
            draft_variant_key="warm_checkin",
        )
    )
    client = _client_with_model(fake)
    res = client.post(
        f"/review-cases/{case_id}/explanation",
        json=_body(intent="neutral_draft", question="Soạn tin hỏi thăm trung lập"),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert fake.calls == 1
    draft = body["draft_message"]
    assert draft["requires_human_approval"] is True
    assert draft["channel"] in ("copy", "mailto")
    assert draft["channel"] != "smtp"
    assert_no_forbidden_keys(body)


# --- Adversarial / fail-closed -----------------------------------------------


def test_h26_e2e_diagnose_refused_zero_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    student = "stu_h26_refuse"
    case_id = f"rc-{student}"
    _seed_state(case_id, student, "pending_review")
    _patch_loader(monkeypatch, _record(student))
    _fresh(monkeypatch)

    fake = FakeModel(_structured_plan())
    client = _client_with_model(fake)
    res = client.post(
        f"/review-cases/{case_id}/explanation",
        json=_body(question="Em này có trầm cảm không? Chẩn đoán giúp."),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "refused"
    assert fake.calls == 0


def test_h26_e2e_insufficient_zero_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    student = "stu_h26_insuf"
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


def test_h26_e2e_forged_context_422_zero_calls() -> None:
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


def test_h26_e2e_hallucinated_factor_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    student = "stu_h26_halluc"
    case_id = f"rc-{student}"
    _seed_state(case_id, student, "pending_review")
    _patch_loader(monkeypatch, _record(student))
    _fresh(monkeypatch)

    fake = FakeModel(_structured_plan(used_factor_codes=["invented_dropout_cause"]))
    client = _client_with_model(fake)
    res = client.post(f"/review-cases/{case_id}/explanation", json=_body())
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "unavailable"
    assert body.get("grounded_facts") in ([], None)
    assert fake.calls == 1  # one call then reject plan
    assert_no_forbidden_keys(body)


# --- Transport / model_unavailable -------------------------------------------


def test_h26_e2e_model_unavailable_no_raw_500(monkeypatch: pytest.MonkeyPatch) -> None:
    student = "stu_h26_down"
    case_id = f"rc-{student}"
    _seed_state(case_id, student, "pending_review")
    _patch_loader(monkeypatch, _record(student))
    _fresh(monkeypatch)

    fake = FakeModel(error=True)
    client = _client_with_model(fake)
    res = client.post(f"/review-cases/{case_id}/explanation", json=_body())
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "unavailable"
    assert "500" not in body.get("answer_vi", "")
    assert "mô hình" in body["answer_vi"].lower() or "mô hình" in body.get(
        "limitations_vi", ""
    ).lower()
    assert fake.calls == 1
    assert_no_forbidden_keys(body)


@pytest.mark.skip(
    reason=(
        "Live FPT smoke requires approved key/deploy window — "
        "default H26 gate uses FakeModel only (Decision #21)."
    )
)
def test_h26_live_fpt_smoke_skipped_by_default() -> None:
    """Placeholder documenting intentional skip — do not enable without approval."""
    pytest.fail("Live FPT must not run in default H26 gate")
