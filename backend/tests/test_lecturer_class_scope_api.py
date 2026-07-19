"""Class-scoped /review-cases visibility for lecturer (gvcn) accounts.

Each lecturer carries a class-overlay ``advisor_scope`` (class-01..04) and must
see only the flagged students in their own class — never another class's, and
without needing a prior handoff/assign (the roster path in
``principal_can_view_care_case``). Uses Principal + read-adapter overrides, so no
live Postgres is required.
"""

from __future__ import annotations

from typing import List

import pytest
from fastapi.testclient import TestClient

from app.auth.principal import Principal, get_principal
from app.cases.class_scope import LECTURER_CLASS_SCOPES, build_class_scope_map
from app.cases.store import store
from app.contracts.coverage import Coverage
from app.contracts.normalized import NormalizedStudentRecord, NormalizedTermGrade
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_store():
    store.clear()
    yield
    store.clear()
    app.dependency_overrides.pop(get_principal, None)


def _lecturer(advisor_scope: str) -> Principal:
    return Principal(
        actor_id=f"acct:gv-{advisor_scope}",
        active_role="gvcn",
        org_scope="org-demo",
        advisor_scope=advisor_scope,
        roles=("gvcn",),
        display_name=f"Lecturer {advisor_scope}",
    )


def _flagged_record(student_ref: str) -> NormalizedStudentRecord:
    # Strongly declining grades -> score above tau_case (flagged / review-band).
    grades = [
        NormalizedTermGrade(term_code="20241", course_ref="c1", credits=3.0, final_grade=9.0),
        NormalizedTermGrade(term_code="20241", course_ref="c2", credits=3.0, final_grade=8.5),
        NormalizedTermGrade(
            term_code="20251", course_ref="c1", credits=3.0, final_grade=4.0,
            grade_status="Không đạt",
        ),
        NormalizedTermGrade(
            term_code="20251", course_ref="c2", credits=3.0, final_grade=3.5,
            grade_status="Không đạt",
        ),
    ]
    return NormalizedStudentRecord(
        student_ref=student_ref,
        source_id="v59-empty-program-students",
        dataset_version="v59-empty-program-students:abcd1234:epu-1",
        schema_version="epu-1",
        snapshot_sha256="a" * 64,
        provenance_approved=True,
        term_grades=grades,
        attendance_events=[],
        advisor_ref="a-240eb01d2805",  # DWH advisor unchanged; overlay is parallel
        mapping_repair=False,
        coverage=Coverage(
            n_valid_terms=2,
            n_courses=4,
            n_attendance_events=0,
            last_term_code="20251",
            last_attendance_at=None,
            status="partial",
            reason_codes=["attendance_source_unapproved"],
        ),
    )


# 8 students -> 4 classes of 2 each (contiguous by sorted ref).
_REFS = [f"stu-{i:04d}" for i in range(8)]
_CLASS_MAP = build_class_scope_map(_REFS)


def _override_reads(monkeypatch: pytest.MonkeyPatch, records: List[NormalizedStudentRecord]) -> None:
    monkeypatch.setattr(
        "app.cases.review_router.list_normalized_students",
        lambda _db, _sid: list(records),
    )
    by_ref = {r.student_ref: r for r in records}
    monkeypatch.setattr(
        "app.cases.review_router.get_normalized_student",
        lambda _db, _sid, ref: by_ref.get(ref),
    )
    monkeypatch.setattr("app.cases.review_router.is_snapshot_stale", lambda *_a, **_k: False)


def _as(principal: Principal) -> None:
    app.dependency_overrides[get_principal] = lambda: principal


def test_class_map_over_test_refs_is_two_per_class() -> None:
    assert _CLASS_MAP["stu-0000"] == LECTURER_CLASS_SCOPES[0]
    assert _CLASS_MAP["stu-0001"] == LECTURER_CLASS_SCOPES[0]
    assert _CLASS_MAP["stu-0002"] == LECTURER_CLASS_SCOPES[1]
    assert _CLASS_MAP["stu-0006"] == LECTURER_CLASS_SCOPES[3]


def test_lecturer_list_shows_only_own_class(monkeypatch: pytest.MonkeyPatch) -> None:
    _override_reads(monkeypatch, [_flagged_record(r) for r in _REFS])
    _as(_lecturer(LECTURER_CLASS_SCOPES[0]))  # class-01 -> stu-0000, stu-0001

    res = client.get("/review-cases")
    assert res.status_code == 200
    body = res.json()
    refs = {item["student_ref"] for item in body["items"]}
    assert refs == {"stu-0000", "stu-0001"}


def test_different_lecturers_get_disjoint_rosters(monkeypatch: pytest.MonkeyPatch) -> None:
    records = [_flagged_record(r) for r in _REFS]
    _override_reads(monkeypatch, records)

    seen: dict[str, set[str]] = {}
    for scope in LECTURER_CLASS_SCOPES:
        _as(_lecturer(scope))
        body = client.get("/review-cases").json()
        seen[scope] = {item["student_ref"] for item in body["items"]}

    # Each class sees exactly its 2 students; no overlap; union == all 8.
    all_seen: set[str] = set()
    for scope, refs in seen.items():
        assert len(refs) == 2
        assert all_seen.isdisjoint(refs)
        all_seen |= refs
    assert all_seen == set(_REFS)


def test_lecturer_detail_in_class_visible_out_of_class_hidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _override_reads(monkeypatch, [_flagged_record(r) for r in _REFS])
    _as(_lecturer(LECTURER_CLASS_SCOPES[0]))  # class-01

    own = client.get("/review-cases/rc-stu-0000")
    assert own.status_code == 200
    assert own.json()["state"] == "ok"
    assert own.json()["case"]["student_ref"] == "stu-0000"

    other = client.get("/review-cases/rc-stu-0004")  # class-03 student
    assert other.status_code == 200
    body = other.json()
    assert body["state"] == "empty"
    assert body["case"] is None
