"""H04 — threshold config / impact / fairness public API."""

from __future__ import annotations


import pytest
from fastapi.testclient import TestClient

from app.contracts.coverage import Coverage
from app.contracts.integration import FORBIDDEN_PUBLIC_FIELDS, assert_no_forbidden_keys
from app.contracts.normalized import NormalizedStudentRecord, NormalizedTermGrade
from app.main import app
from app.ml.scoring import DEFAULT_THRESHOLDS, MODEL_VERSION

client = TestClient(app)
SHA = "b" * 64


def _coverage() -> Coverage:
    return Coverage(
        n_valid_terms=2,
        n_courses=4,
        n_attendance_events=0,
        last_term_code="20251",
        last_attendance_at=None,
        status="partial",
        reason_codes=["attendance_source_unapproved"],
    )


def _high_risk(student_ref: str) -> NormalizedStudentRecord:
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
        attendance_events=[],
        advisor_ref="adv-secret",
        mapping_repair=False,
        coverage=_coverage(),
    )


def test_get_thresholds_happy() -> None:
    res = client.get("/config/thresholds")
    assert res.status_code == 200
    body = res.json()
    assert body["threshold_config_version"] == DEFAULT_THRESHOLDS.version
    assert body["tau_case"] == DEFAULT_THRESHOLDS.tau_case
    assert body["tau_high"] == DEFAULT_THRESHOLDS.tau_high
    assert body["model_version"] == MODEL_VERSION
    assert_no_forbidden_keys(body)
    for key in FORBIDDEN_PUBLIC_FIELDS:
        assert key not in body


def test_impact_aggregates_no_raw_score(monkeypatch: pytest.MonkeyPatch) -> None:
    records = [_high_risk("stu_a"), _high_risk("stu_b")]
    monkeypatch.setattr(
        "app.config_api.router.list_normalized_students",
        lambda _db, _sid: records,
    )
    res = client.get("/config/thresholds/impact", params={"tau_case": 0.1, "tau_high": 0.5})
    assert res.status_code == 200
    body = res.json()
    assert set(body.keys()) == {
        "threshold_config_version",
        "tau_case",
        "tau_high",
        "model_version",
        "n_scored",
        "n_can_ra_soat",
        "n_uu_tien_som",
        "n_no_case",
    }
    assert body["n_scored"] >= 1
    assert body["n_can_ra_soat"] + body["n_uu_tien_som"] + body["n_no_case"] == len(records)
    assert_no_forbidden_keys(body)
    for key in FORBIDDEN_PUBLIC_FIELDS:
        assert key not in body
    # Explicit: no nested student payloads
    assert "items" not in body
    assert "students" not in body
    assert "scores" not in body


def test_fairness_report_fail_closed_mvp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.config_api.router.list_normalized_students",
        lambda _db, _sid: [_high_risk("stu_a")],
    )
    res = client.get("/fairness/report")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "insufficient_data"
    assert body["reason_code"] == "no_approved_audit_attribute"
    assert body["groups"] is None
    assert body["fairness_flag"] is None
    assert body["model_version"] == MODEL_VERSION
    assert_no_forbidden_keys(body)
    for key in FORBIDDEN_PUBLIC_FIELDS:
        assert key not in body


def test_openapi_includes_h04_paths() -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "/config/thresholds" in paths
    assert "/config/thresholds/impact" in paths
    assert "/fairness/report" in paths
