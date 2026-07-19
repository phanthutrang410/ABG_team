"""Unit tests for ml_term_snapshot / attendance_week readers (D460-11 / D460-12)."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.contracts.coverage import attendance_unapproved_defaults
from app.contracts.review_case import ContributingFactor
from app.dwh.ml_snapshot_reader import (
    list_attendance_weeks,
    projection_from_snapshot,
)
from app.dwh.models import AttendanceWeek


_CALC_AT = datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc)


def _fake_ml_row(**overrides):
    coverage = attendance_unapproved_defaults(
        n_valid_terms=2,
        n_courses=2,
        last_term_code="2022-2023-T2",
    )
    factors = [
        ContributingFactor(code="grade_trend_declining", evidence_refs=["term:2022-2023-T2"]),
    ]
    base = dict(
        source_id="v59-empty-program-students",
        student_ref="s-fixture-1",
        dataset_version="v59-empty-program-students:abcd1234:epu-1",
        model_version="m02-baseline-0.2",
        threshold_config_version="thr-epu-0.1-uncalibrated",
        calculated_at=_CALC_AT,
        last_term_code="2022-2023-T2",
        latest_term_gpa=Decimal("3.45"),
        grade_trend_slope=Decimal("-0.123456"),
        grade_volatility=Decimal("1.234567"),
        failed_credits=Decimal("3.00"),
        attendance_rate_window=None,
        attendance_trend_slope=None,
        coverage_status=coverage.status,
        coverage_json=json.dumps(coverage.model_dump(mode="json"), separators=(",", ":")),
        review_priority_band="can_ra_soat",
        contributing_factors_json=json.dumps(
            [f.model_dump(mode="json") for f in factors],
            separators=(",", ":"),
        ),
        model_score=Decimal("0.6123"),
        explain_schema_version="agent-explain-v1",
        agent_explain_json='{"review_priority_band":"can_ra_soat"}',
        evidence_fingerprint="a" * 64,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_projection_from_snapshot_excludes_model_score() -> None:
    row = _fake_ml_row()
    projection = projection_from_snapshot(row)

    assert projection.review_priority_band == "can_ra_soat"
    assert [f.code for f in projection.contributing_factors] == ["grade_trend_declining"]
    assert projection.features.student_ref == "s-fixture-1"
    assert projection.features.latest_term_gpa == 3.45
    assert projection.features.grade_trend_slope == -0.123456
    assert projection.features.failed_credits == 3.0
    assert projection.features.coverage.status == "partial"
    assert projection.features.model_version == "m02-baseline-0.2"
    assert projection.features.calculated_at == _CALC_AT

    # Public projection must never carry model_score.
    assert not hasattr(projection, "model_score")
    blob = json.dumps(
        {
            "band": projection.review_priority_band,
            "factors": [f.model_dump() for f in projection.contributing_factors],
            "features": projection.features.model_dump(mode="json"),
        },
        default=str,
    )
    assert "model_score" not in blob
    assert "0.6123" not in blob


def test_projection_below_threshold_band_null() -> None:
    row = _fake_ml_row(review_priority_band=None, contributing_factors_json="[]", model_score=None)
    projection = projection_from_snapshot(row)
    assert projection.review_priority_band is None
    assert projection.contributing_factors == []


def test_list_attendance_weeks_empty_inputs() -> None:
    session = MagicMock()
    assert list_attendance_weeks(session, "", "s-1") == []
    assert list_attendance_weeks(session, "src", "") == []
    session.scalars.assert_not_called()


def test_list_attendance_weeks_orders_by_week_start() -> None:
    week_a = AttendanceWeek(
        source_id="mvp-attendance-over-time",
        student_ref="s-1",
        week_start_date=date(2026, 1, 5),
        week_end_date=date(2026, 1, 11),
        n_events=2,
        n_in_denominator=2,
        n_present=1,
        n_absent=1,
        n_excused_excluded=0,
        attendance_rate=Decimal("0.5000"),
    )
    week_b = AttendanceWeek(
        source_id="mvp-attendance-over-time",
        student_ref="s-1",
        week_start_date=date(2026, 1, 12),
        week_end_date=date(2026, 1, 18),
        n_events=1,
        n_in_denominator=1,
        n_present=1,
        n_absent=0,
        n_excused_excluded=0,
        attendance_rate=Decimal("1.0000"),
    )
    session = MagicMock()
    session.scalars.return_value.all.return_value = [week_a, week_b]

    rows = list_attendance_weeks(session, "mvp-attendance-over-time", "s-1")
    assert rows == [week_a, week_b]
    session.scalars.assert_called_once()


def test_project_review_case_prefers_snapshot_without_live_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D460-11: when ml_term_snapshot exists, skip live score_student."""
    from app.cases.review_projection import project_review_case
    from app.cases.store import CaseStore
    from app.contracts.normalized import NormalizedStudentRecord
    from app.dwh.ml_snapshot_reader import projection_from_snapshot
    import app.cases.review_projection as rp

    row = _fake_ml_row()
    projection = projection_from_snapshot(row)
    calls = {"score_student": 0}

    def _boom(*_a, **_k):
        calls["score_student"] += 1
        raise AssertionError("live score_student must not run when snapshot exists")

    monkeypatch.setattr(rp, "score_record", _boom)
    monkeypatch.setattr(
        rp,
        "get_ml_term_projection",
        lambda _session, _sid, _ref: projection,
    )

    coverage = attendance_unapproved_defaults(
        n_valid_terms=2, n_courses=2, last_term_code="2022-2023-T2"
    )
    record = NormalizedStudentRecord(
        student_ref="s-fixture-1",
        source_id="v59-empty-program-students",
        dataset_version="v59-empty-program-students:abcd1234:epu-1",
        schema_version="epu-1",
        snapshot_sha256="a" * 64,
        provenance_approved=True,
        term_grades=[],
        attendance_events=[],
        coverage=coverage,
    )
    case = project_review_case(
        record,
        CaseStore(),
        session=MagicMock(),
        include_below_threshold=True,
    )
    assert case is not None
    assert case.review_priority_band == "can_ra_soat"
    assert [f.code for f in case.contributing_factors] == ["grade_trend_declining"]
    assert calls["score_student"] == 0
    assert "model_score" not in case.model_dump()
