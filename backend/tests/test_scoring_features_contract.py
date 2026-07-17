"""Contract + leakage tests for Coverage / ScoringFeatures (H06a)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.contracts.coverage import (
    ATTENDANCE_SOURCE_UNAPPROVED,
    Coverage,
    attendance_unapproved_defaults,
)
from app.contracts.scoring import ScoringFeatures

FIXTURE = Path(__file__).parent / "fixtures" / "scoring_features.json"

FORBIDDEN_SCORING_FIELDS = (
    "model_score",
    "is_dropout_outcome",
    "advisor_ref",
    "full_name",
    "mssv",
    "email",
    "phone",
    "synth_socioeconomic_group",
    "synth_ethnicity_group",
    "Trạng thái",
)


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_scoring_features_fixture_validates() -> None:
    features = ScoringFeatures.model_validate(load_fixture())
    assert features.student_ref.startswith("stu_pseudo_")
    assert features.attendance_rate_window is None
    assert features.attendance_trend_slope is None
    assert ATTENDANCE_SOURCE_UNAPPROVED in features.coverage.reason_codes
    assert features.coverage.n_attendance_events == 0
    assert features.coverage.status == "partial"


def test_versioning_fields_required() -> None:
    for field in (
        "dataset_version",
        "model_version",
        "threshold_config_version",
        "calculated_at",
        "student_ref",
        "coverage",
    ):
        data = load_fixture()
        del data[field]
        with pytest.raises(ValidationError):
            ScoringFeatures.model_validate(data)


@pytest.mark.parametrize("forbidden", FORBIDDEN_SCORING_FIELDS)
def test_scoring_features_rejects_forbidden_fields(forbidden: str) -> None:
    data = load_fixture()
    data[forbidden] = 0.9 if forbidden == "model_score" else "leak"
    with pytest.raises(ValidationError):
        ScoringFeatures.model_validate(data)


def test_attendance_unapproved_defaults_fail_closed() -> None:
    cov = attendance_unapproved_defaults(
        n_valid_terms=2, n_courses=8, last_term_code="20251"
    )
    assert cov.status == "partial"
    assert cov.n_attendance_events == 0
    assert cov.last_attendance_at is None
    assert cov.reason_codes == [ATTENDANCE_SOURCE_UNAPPROVED]


def test_attendance_unapproved_rejects_nonzero_events() -> None:
    with pytest.raises(ValidationError, match="n_attendance_events"):
        Coverage.model_validate(
            {
                "n_valid_terms": 2,
                "n_courses": 8,
                "n_attendance_events": 3,
                "last_term_code": "20251",
                "last_attendance_at": None,
                "status": "partial",
                "reason_codes": [ATTENDANCE_SOURCE_UNAPPROVED],
            }
        )


def test_insufficient_requires_reason_code() -> None:
    with pytest.raises(ValidationError, match="reason_code"):
        Coverage.model_validate(
            {
                "n_valid_terms": 0,
                "n_courses": 0,
                "n_attendance_events": 0,
                "last_term_code": None,
                "last_attendance_at": None,
                "status": "insufficient",
                "reason_codes": [],
            }
        )


def test_unknown_reason_code_rejected() -> None:
    data = load_fixture()
    data["coverage"]["reason_codes"] = ["invented_reason"]
    with pytest.raises(ValidationError):
        ScoringFeatures.model_validate(data)
