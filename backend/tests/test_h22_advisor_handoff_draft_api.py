"""H22 — AdvisorHandoffDraftBundle API (draft-only, forbidden-field scan)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.cases.domain import CaseState
from app.cases.store import CaseSnapshot, store
from app.contracts.advisor_handoff_draft import (
    AdvisorHandoffDraft,
    AdvisorHandoffDraftBundle,
    FORBIDDEN_HANDOFF_DRAFT_FIELDS,
    assert_no_handoff_forbidden_keys,
)
from app.contracts.coverage import Coverage
from app.contracts.normalized import NormalizedStudentRecord, NormalizedTermGrade
from app.main import app

client = TestClient(app)
NOW = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)
SHA = "b" * 64


@pytest.fixture(autouse=True)
def _reset_store() -> None:
    store.clear()
    yield
    store.clear()


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


def _record(
    student_ref: str,
    *,
    advisor_ref: str | None = "adv-a1",
    mapping_repair: bool = False,
    class_code: str | None = "CNTT-K18",
) -> NormalizedStudentRecord:
    grades = [
        NormalizedTermGrade(term_code="20241", course_ref="c1", credits=3.0, final_grade=9.0),
        NormalizedTermGrade(term_code="20241", course_ref="c2", credits=3.0, final_grade=8.5),
        NormalizedTermGrade(term_code="20251", course_ref="c1", credits=3.0, final_grade=4.0, grade_status="Không đạt"),
        NormalizedTermGrade(term_code="20251", course_ref="c2", credits=3.0, final_grade=3.5, grade_status="Không đạt"),
    ]
    return NormalizedStudentRecord(
        student_ref=student_ref,
        source_id="v59-empty-program-students",
        dataset_version="v59-empty-program-students:abcd1234:epu-1",
        schema_version="epu-1",
        snapshot_sha256=SHA,
        provenance_approved=True,
        term_grades=grades,
        attendance_events=[],
        advisor_ref=advisor_ref,
        mapping_repair=mapping_repair,
        class_code=class_code,
        coverage=_coverage(),
    )


def _override_list(monkeypatch: pytest.MonkeyPatch, records: List[NormalizedStudentRecord]) -> None:
    monkeypatch.setattr(
        "app.cases.advisor_draft_router.list_normalized_students",
        lambda _db, _sid: list(records),
    )


def _seed_case(
    case_id: str,
    *,
    state: CaseState,
    student_ref: str,
) -> None:
    store.put(
        CaseSnapshot(
            case_id=case_id,
            state=state,
            student_ref=student_ref,
            source_id="v59-empty-program-students",
        )
    )


def test_happy_path_groups_by_advisor(monkeypatch: pytest.MonkeyPatch) -> None:
    records = [
        _record("stu_a", advisor_ref="adv-1"),
        _record("stu_b", advisor_ref="adv-1"),
        _record("stu_c", advisor_ref="adv-2"),
    ]
    _override_list(monkeypatch, records)
    _seed_case("rc-stu_a", state=CaseState.APPROVED_FOR_FOLLOW_UP, student_ref="stu_a")
    _seed_case("rc-stu_b", state=CaseState.ASSIGNED, student_ref="stu_b")
    _seed_case("rc-stu_c", state=CaseState.APPROVED_FOR_FOLLOW_UP, student_ref="stu_c")

    res = client.get("/advisor-handoff-drafts")
    assert res.status_code == 200
    body = res.json()
    assert_no_handoff_forbidden_keys(body)
    assert body["state"] == "ok"
    assert len(body["bundles"]) == 2
    by_adv = {b["advisor_ref"]: b for b in body["bundles"]}
    assert by_adv["adv-1"]["case_count"] == 2
    assert by_adv["adv-2"]["case_count"] == 1
    for bundle in body["bundles"]:
        assert bundle["draft"]["requires_human_approval"] is True
        assert "rà soát" in bundle["draft"]["subject"].lower() or "theo dõi" in bundle["draft"][
            "subject"
        ].lower()
        assert "Bản nháp" in bundle["draft"]["body"]
        assert "advisor_ref" in bundle
        lower = bundle["draft"]["body"].lower()
        assert "bỏ học" not in lower
        assert "nguy cơ" not in lower


def test_excludes_pending_and_dismissed(monkeypatch: pytest.MonkeyPatch) -> None:
    _override_list(monkeypatch, [_record("stu_ok"), _record("stu_skip")])
    _seed_case("rc-stu_ok", state=CaseState.APPROVED_FOR_FOLLOW_UP, student_ref="stu_ok")
    _seed_case("rc-stu_skip", state=CaseState.PENDING_REVIEW, student_ref="stu_skip")
    store.put(
        CaseSnapshot(
            case_id="rc-stu_dismissed",
            state=CaseState.DISMISSED,
            student_ref="stu_ok",
            source_id="v59-empty-program-students",
        )
    )

    res = client.get("/advisor-handoff-drafts")
    body = res.json()
    assert body["state"] == "ok"
    assert len(body["bundles"]) == 1
    assert body["bundles"][0]["case_count"] == 1
    assert body["bundles"][0]["cases"][0]["student_ref"] == "stu_ok"


def test_mapping_repair_bucket(monkeypatch: pytest.MonkeyPatch) -> None:
    records = [
        _record("stu_ok", advisor_ref="adv-1", mapping_repair=False),
        _record("stu_repair", advisor_ref=None, mapping_repair=True),
        _record("stu_blank", advisor_ref="  ", mapping_repair=False),
    ]
    _override_list(monkeypatch, records)
    _seed_case("rc-stu_ok", state=CaseState.APPROVED_FOR_FOLLOW_UP, student_ref="stu_ok")
    _seed_case("rc-stu_repair", state=CaseState.APPROVED_FOR_FOLLOW_UP, student_ref="stu_repair")
    _seed_case("rc-stu_blank", state=CaseState.ASSIGNED, student_ref="stu_blank")

    res = client.get("/advisor-handoff-drafts")
    body = res.json()
    assert_no_handoff_forbidden_keys(body)
    assert len(body["bundles"]) == 1
    assert body["bundles"][0]["advisor_ref"] == "adv-1"
    assert body["mapping_repair"]["case_count"] == 2
    repair_refs = {c["student_ref"] for c in body["mapping_repair"]["cases"]}
    assert repair_refs == {"stu_repair", "stu_blank"}
    assert "mapping_repair" in body["mapping_repair"]["limitations"]


def test_empty_when_no_eligible_cases(monkeypatch: pytest.MonkeyPatch) -> None:
    _override_list(monkeypatch, [_record("stu_x")])
    _seed_case("rc-stu_x", state=CaseState.NEW_SIGNAL, student_ref="stu_x")
    res = client.get("/advisor-handoff-drafts")
    body = res.json()
    assert body["state"] == "empty"
    assert body["bundles"] == []
    assert body["mapping_repair"]["case_count"] == 0


def test_forbidden_fields_not_in_response(monkeypatch: pytest.MonkeyPatch) -> None:
    _override_list(monkeypatch, [_record("stu_ok")])
    _seed_case("rc-stu_ok", state=CaseState.APPROVED_FOR_FOLLOW_UP, student_ref="stu_ok")
    body = client.get("/advisor-handoff-drafts").json()
    assert_no_handoff_forbidden_keys(body)
    blob = str(body).lower()
    for key in ("model_score", "email", "phone", "mssv", "is_dropout_outcome"):
        assert key not in blob
    assert "advisor_ref" not in FORBIDDEN_HANDOFF_DRAFT_FIELDS


def test_requires_human_approval_invariant() -> None:
    with pytest.raises(ValidationError):
        AdvisorHandoffDraft(
            subject="x",
            body="y",
            requires_human_approval=False,  # type: ignore[arg-type]
        )


def test_bundle_schema_accepts_valid() -> None:
    draft = AdvisorHandoffDraft(subject="Danh sách", body="line\nBản nháp", requires_human_approval=True)
    bundle = AdvisorHandoffDraftBundle(
        advisor_ref="adv-1",
        case_count=1,
        cases=[
            {
                "case_id": "rc-1",
                "student_ref": "stu_1",
                "review_priority_band": "can_ra_soat",
                "contributing_factor_codes": ["grade_trend_declining"],
                "coverage_status": "partial",
                "coverage_reason_codes": [],
                "case_state": "approved_for_follow_up",
                "class_code": "K18",
            }
        ],
        draft=draft,
        limitations=["insufficient_contact_map"],
    )
    assert bundle.case_count == 1


def test_no_send_email_route() -> None:
    paths = {route.path for route in app.routes if hasattr(route, "path")}
    send_like = [p for p in paths if "send" in p.lower() and "email" in p.lower()]
    assert send_like == []
    assert any("/advisor-handoff-drafts" in p for p in paths)
    # POST send must not exist
    methods = []
    for route in app.routes:
        if getattr(route, "path", None) == "/advisor-handoff-drafts":
            methods.extend(getattr(route, "methods", set()) or [])
    assert "POST" not in methods
