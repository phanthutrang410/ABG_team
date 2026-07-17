"""Contract + leakage tests for public ReviewCase (H06a)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.contracts.coverage import ATTENDANCE_SOURCE_UNAPPROVED
from app.contracts.review_case import ReviewCase

FIXTURE = Path(__file__).parent / "fixtures" / "review_case.json"

#: Fields that must never appear on the public projection (Data-ML / RULES).
FORBIDDEN_PUBLIC_FIELDS = (
    "model_score",
    "risk_score",
    "is_dropout_outcome",
    "advisor_ref",
    "full_name",
    "mssv",
    "email",
    "phone",
    "student_name",
    "synth_socioeconomic_group",
    "synth_ethnicity_group",
    "group_attrs",
)


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_review_case_fixture_validates() -> None:
    case = ReviewCase.model_validate(load_fixture())
    assert case.review_priority_band == "can_ra_soat"
    assert case.case_state == "pending_review"
    assert case.data_state == "partial"
    assert "model_score" not in case.model_dump()
    assert ATTENDANCE_SOURCE_UNAPPROVED in case.coverage.reason_codes
    assert ATTENDANCE_SOURCE_UNAPPROVED in case.limitations
    assert case.coverage.n_attendance_events == 0


def test_public_versioning_and_band_required() -> None:
    for field in (
        "case_id",
        "student_ref",
        "case_state",
        "review_priority_band",
        "coverage",
        "data_state",
        "dataset_version",
        "model_version",
        "threshold_config_version",
        "calculated_at",
    ):
        data = load_fixture()
        del data[field]
        with pytest.raises(ValidationError):
            ReviewCase.model_validate(data)


@pytest.mark.parametrize("forbidden", FORBIDDEN_PUBLIC_FIELDS)
def test_public_review_case_rejects_leakage_fields(forbidden: str) -> None:
    data = load_fixture()
    data[forbidden] = 0.87 if "score" in forbidden else "leak"
    with pytest.raises(ValidationError):
        ReviewCase.model_validate(data)


def test_rejects_raw_score_nested_in_factor() -> None:
    data = load_fixture()
    data["contributing_factors"][0]["weight"] = 0.55
    with pytest.raises(ValidationError):
        ReviewCase.model_validate(data)


def test_invalid_band_rejected() -> None:
    data = load_fixture()
    data["review_priority_band"] = "high_risk"
    with pytest.raises(ValidationError):
        ReviewCase.model_validate(data)


def test_legacy_case_state_alias_rejected() -> None:
    data = load_fixture()
    data["case_state"] = "in_review"
    with pytest.raises(ValidationError):
        ReviewCase.model_validate(data)


def test_partial_coverage_cannot_claim_ok_data_state() -> None:
    data = load_fixture()
    data["data_state"] = "ok"
    with pytest.raises(ValidationError, match="partial"):
        ReviewCase.model_validate(data)


def test_insufficient_coverage_requires_insufficient_data_state() -> None:
    data = load_fixture()
    data["coverage"] = {
        "n_valid_terms": 0,
        "n_courses": 0,
        "n_attendance_events": 0,
        "last_term_code": None,
        "last_attendance_at": None,
        "status": "insufficient",
        "reason_codes": ["grade_coverage_insufficient", "attendance_source_unapproved"],
    }
    data["review_priority_band"] = None
    data["contributing_factors"] = []
    data["data_state"] = "partial"
    with pytest.raises(ValidationError, match="insufficient_data"):
        ReviewCase.model_validate(data)


def test_insufficient_rejects_review_priority_band() -> None:
    """Data-ML §3: no band when no ready branch."""
    data = load_fixture()
    data["coverage"] = {
        "n_valid_terms": 0,
        "n_courses": 0,
        "n_attendance_events": 0,
        "last_term_code": None,
        "last_attendance_at": None,
        "status": "insufficient",
        "reason_codes": ["grade_coverage_insufficient", "attendance_source_unapproved"],
    }
    data["data_state"] = "insufficient_data"
    data["review_priority_band"] = "can_ra_soat"
    data["contributing_factors"] = []
    with pytest.raises(ValidationError, match="review_priority_band"):
        ReviewCase.model_validate(data)


def test_insufficient_allows_null_band_and_empty_factors() -> None:
    data = load_fixture()
    data["coverage"] = {
        "n_valid_terms": 0,
        "n_courses": 0,
        "n_attendance_events": 0,
        "last_term_code": None,
        "last_attendance_at": None,
        "status": "insufficient",
        "reason_codes": ["grade_coverage_insufficient", "attendance_source_unapproved"],
    }
    data["data_state"] = "insufficient_data"
    data["review_priority_band"] = None
    data["contributing_factors"] = []
    case = ReviewCase.model_validate(data)
    assert case.review_priority_band is None
    assert case.contributing_factors == []


def test_ok_rejects_empty_contributing_factors() -> None:
    """Data-ML §3: empty factors forbidden when ok."""
    data = load_fixture()
    data["coverage"] = {
        "n_valid_terms": 2,
        "n_courses": 8,
        "n_attendance_events": 4,
        "last_term_code": "20251",
        "last_attendance_at": "2026-07-10T00:00:00Z",
        "status": "ok",
        "reason_codes": [],
    }
    data["data_state"] = "ok"
    data["contributing_factors"] = []
    data["limitations"] = []
    with pytest.raises(ValidationError, match="contributing_factors"):
        ReviewCase.model_validate(data)


def test_rejects_synthetic_dataset_version_on_public_case() -> None:
    """Data-ML §1: synthetic-* forbidden on public ReviewCase."""
    data = load_fixture()
    data["dataset_version"] = "synthetic-v0.2-seed42-n120-w12-uni"
    with pytest.raises(ValidationError, match="synthetic-"):
        ReviewCase.model_validate(data)


def test_partial_still_requires_band() -> None:
    data = load_fixture()
    data["review_priority_band"] = None
    with pytest.raises(ValidationError, match="review_priority_band"):
        ReviewCase.model_validate(data)
