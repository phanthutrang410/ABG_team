"""H02 — ReviewCase list/detail API (H11a envelopes, no forbidden fields)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import pytest
from fastapi.testclient import TestClient

from app.cases.store import store
from app.contracts.coverage import Coverage
from app.contracts.integration import FORBIDDEN_PUBLIC_FIELDS, assert_no_forbidden_keys
from app.contracts.normalized import (
    NormalizedAttendanceEvent,
    NormalizedStudentRecord,
    NormalizedTermGrade,
)
from app.dwh.read_adapter import ReadAdapterError
from app.main import app

client = TestClient(app)
NOW = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)
SHA = "a" * 64


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
    grades: List[NormalizedTermGrade] | None = None,
    coverage: Coverage | None = None,
    events: List[NormalizedAttendanceEvent] | None = None,
) -> NormalizedStudentRecord:
    if grades is None:
        # Strongly declining grades -> score above tau_case
        grades = [
            NormalizedTermGrade(term_code="20241", course_ref="c1", credits=3.0, final_grade=9.0),
            NormalizedTermGrade(term_code="20241", course_ref="c2", credits=3.0, final_grade=8.5),
            NormalizedTermGrade(term_code="20251", course_ref="c1", credits=3.0, final_grade=4.0),
            NormalizedTermGrade(term_code="20251", course_ref="c2", credits=3.0, final_grade=3.5),
        ]
    return NormalizedStudentRecord(
        student_ref=student_ref,
        source_id="v59-empty-program-students",
        dataset_version="v59-empty-program-students:abcd1234:epu-1",
        schema_version="epu-1",
        snapshot_sha256=SHA,
        provenance_approved=True,
        term_grades=grades,
        attendance_events=events or [],
        advisor_ref="adv-secret",
        mapping_repair=False,
        coverage=coverage or _coverage(),
    )


def _override_list(monkeypatch: pytest.MonkeyPatch, records: List[NormalizedStudentRecord]) -> None:
    monkeypatch.setattr(
        "app.cases.review_router.list_normalized_students",
        lambda _db, _sid: list(records),
    )
    by_ref = {r.student_ref: r for r in records}
    monkeypatch.setattr(
        "app.cases.review_router.get_normalized_student",
        lambda _db, _sid, ref: by_ref.get(ref),
    )


def test_list_ok_happy(monkeypatch: pytest.MonkeyPatch) -> None:
    _override_list(monkeypatch, [_record("stu_ok_001")])
    monkeypatch.setattr(
        "app.cases.review_router.is_snapshot_stale",
        lambda *_a, **_k: False,
    )
    res = client.get("/review-cases")
    assert res.status_code == 200
    body = res.json()
    assert_no_forbidden_keys(body)
    assert body["state"] == "ok"
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["case_id"] == "rc-stu_ok_001"
    assert item["student_ref"] == "stu_ok_001"
    assert item["review_priority_band"] in ("can_ra_soat", "uu_tien_som")
    assert "advisor_ref" not in item
    assert "model_score" not in item
    for key in FORBIDDEN_PUBLIC_FIELDS:
        assert key not in item


def test_list_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    # Flat high grades -> low/no risk band
    grades = [
        NormalizedTermGrade(term_code="20241", course_ref="c1", credits=3.0, final_grade=8.0),
        NormalizedTermGrade(term_code="20251", course_ref="c1", credits=3.0, final_grade=8.1),
    ]
    _override_list(monkeypatch, [_record("stu_low", grades=grades)])
    monkeypatch.setattr("app.cases.review_router.is_snapshot_stale", lambda *_a, **_k: False)
    res = client.get("/review-cases")
    assert res.status_code == 200
    body = res.json()
    assert body["state"] == "empty"
    assert body["items"] == []
    assert_no_forbidden_keys(body)


def test_list_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(_db, _sid):
        raise ReadAdapterError(["source_unapproved"], "nope")

    monkeypatch.setattr("app.cases.review_router.list_normalized_students", _boom)
    res = client.get("/review-cases")
    assert res.status_code == 200
    body = res.json()
    assert body["state"] == "error"
    assert body["items"] == []
    assert body["problem"]["code"] == "upstream_unavailable"
    assert_no_forbidden_keys(body)


def test_list_stale(monkeypatch: pytest.MonkeyPatch) -> None:
    _override_list(monkeypatch, [_record("stu_stale")])
    monkeypatch.setattr("app.cases.review_router.is_snapshot_stale", lambda *_a, **_k: True)
    res = client.get("/review-cases")
    assert res.status_code == 200
    body = res.json()
    assert body["state"] == "stale"
    assert body["problem"]["code"] == "stale_snapshot"
    assert len(body["items"]) >= 1
    assert_no_forbidden_keys(body)


def test_detail_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    _override_list(monkeypatch, [_record("stu_ok_001")])
    monkeypatch.setattr("app.cases.review_router.is_snapshot_stale", lambda *_a, **_k: False)
    res = client.get("/review-cases/rc-stu_ok_001")
    assert res.status_code == 200
    body = res.json()
    assert body["state"] == "ok"
    assert body["freshness"] == "fresh"
    assert body["case"]["case_id"] == "rc-stu_ok_001"
    assert_no_forbidden_keys(body)
    for key in FORBIDDEN_PUBLIC_FIELDS:
        assert key not in body["case"]


def test_detail_insufficient_data(monkeypatch: pytest.MonkeyPatch) -> None:
    cov = _coverage(
        n_valid_terms=0,
        n_courses=0,
        last_term_code=None,
        status="insufficient",
        reason_codes=["grade_coverage_insufficient", "attendance_source_unapproved"],
    )
    _override_list(
        monkeypatch,
        [_record("stu_insuf", grades=[], coverage=cov)],
    )
    monkeypatch.setattr("app.cases.review_router.is_snapshot_stale", lambda *_a, **_k: False)
    res = client.get("/review-cases/rc-stu_insuf")
    assert res.status_code == 200
    body = res.json()
    assert body["state"] == "insufficient_data"
    assert body["case"]["data_state"] == "insufficient_data"
    assert body["case"]["review_priority_band"] is None
    assert_no_forbidden_keys(body)


def test_detail_empty_below_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    grades = [
        NormalizedTermGrade(term_code="20241", course_ref="c1", credits=3.0, final_grade=8.0),
        NormalizedTermGrade(term_code="20251", course_ref="c1", credits=3.0, final_grade=8.1),
    ]
    _override_list(monkeypatch, [_record("stu_low", grades=grades)])
    monkeypatch.setattr("app.cases.review_router.is_snapshot_stale", lambda *_a, **_k: False)
    res = client.get("/review-cases/rc-stu_low")
    assert res.status_code == 200
    body = res.json()
    assert body["state"] == "empty"
    assert body["case"] is None
    assert_no_forbidden_keys(body)


def test_detail_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(_db, _sid, _ref):
        raise RuntimeError("db down")

    monkeypatch.setattr("app.cases.review_router.get_normalized_student", _boom)
    res = client.get("/review-cases/rc-anyone")
    assert res.status_code == 200
    body = res.json()
    assert body["state"] == "error"
    assert body["case"] is None
    assert_no_forbidden_keys(body)


def test_detail_stale(monkeypatch: pytest.MonkeyPatch) -> None:
    _override_list(monkeypatch, [_record("stu_stale")])
    old = NOW - timedelta(days=30)

    def _proj(record, store, **kwargs):
        from app.cases import review_projection as rp

        kwargs["calculated_at"] = old
        return rp.project_review_case(record, store, **kwargs)

    monkeypatch.setattr("app.cases.review_router.project_review_case", _proj)
    # is_snapshot_stale with real DEFAULT will mark old as stale
    res = client.get("/review-cases/rc-stu_stale")
    assert res.status_code == 200
    body = res.json()
    assert body["state"] == "stale"
    assert body["freshness"] == "stale"
    assert body["case"] is not None
    assert_no_forbidden_keys(body)


def test_cases_transition_shape_unchanged() -> None:
    """GET /cases/{id} remains TransitionResponse — not ReviewCase."""
    create = client.post(
        "/cases",
        json={"case_id": "seed-1", "state": "new_signal", "student_ref": "s1"},
    )
    assert create.status_code == 201
    got = client.get("/cases/seed-1")
    assert got.status_code == 200
    body = got.json()
    assert set(body.keys()) >= {"case_id", "state"}
    assert "review_priority_band" not in body
    assert "model_score" not in body
