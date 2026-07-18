"""M02 — baseline scoring tests (Data-ML §§2–5, M04 §5 test plan).

Pure over `NormalizedStudentRecord`/`ScoringFeatures` — no DB/Postgres needed.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.contracts.coverage import Coverage, attendance_unapproved_defaults
from app.contracts.normalized import (
    NormalizedAttendanceEvent,
    NormalizedStudentRecord,
    NormalizedTermGrade,
)
from app.contracts.scoring import ScoringFeatures
from app.ml.scoring import (
    DEFAULT_THRESHOLDS,
    MODEL_VERSION,
    ThresholdConfig,
    band_for_score,
    compute_attendance_trend_slope,
    compute_failed_credits,
    compute_grade_trend_slope,
    compute_grade_volatility,
    compute_latest_term_gpa,
    compute_model_score,
    contributing_factors,
    score_student,
)

_CALC_AT = datetime(2026, 7, 18, tzinfo=timezone.utc)


def _grade(
    term_code: str,
    grade: float,
    credits: float = 3.0,
    course: str = "c1",
    grade_status: str | None = None,
) -> NormalizedTermGrade:
    return NormalizedTermGrade(
        term_code=term_code,
        course_ref=course,
        credits=credits,
        final_grade=grade,
        grade_status=grade_status,
    )


def _att(observed_at: datetime, status: str = "present", excused: bool = None, course: str = "") -> NormalizedAttendanceEvent:
    return NormalizedAttendanceEvent(
        observed_at=observed_at, course_ref=course, presence_status=status, excused=excused
    )


def _semester_record(
    term_grades: list, coverage: Coverage = None
) -> NormalizedStudentRecord:
    if coverage is None:
        terms = sorted({g.term_code for g in term_grades if g.final_grade is not None})
        n_courses = sum(1 for g in term_grades if g.final_grade is not None)
        coverage = attendance_unapproved_defaults(
            n_valid_terms=len(terms),
            n_courses=n_courses,
            last_term_code=terms[-1] if terms else None,
        )
    return NormalizedStudentRecord(
        student_ref="s-1",
        source_id="v59-empty-program-students",
        dataset_version="v59-empty-program-students:abcd1234:epu-1",
        schema_version="epu-1",
        snapshot_sha256="a" * 64,
        provenance_approved=True,
        term_grades=term_grades,
        attendance_events=[],
        coverage=coverage,
    )


def _attendance_record(events: list, coverage: Coverage) -> NormalizedStudentRecord:
    return NormalizedStudentRecord(
        student_ref="s-1",
        source_id="mvp-attendance-over-time",
        dataset_version="mvp-attendance-over-time:abcd1234:epu-1",
        schema_version="epu-1",
        snapshot_sha256="b" * 64,
        provenance_approved=True,
        term_grades=[],
        attendance_events=events,
        coverage=coverage,
    )


# --- Grade branch feature computation --------------------------------------


def test_grade_trend_slope_none_below_min_terms():
    assert compute_grade_trend_slope([_grade("2022-2023-T1", 8.0)]) is None
    assert compute_grade_trend_slope([]) is None


def test_grade_trend_slope_two_terms_exact():
    grades = [_grade("2022-2023-T1", 8.0), _grade("2022-2023-T2", 6.0)]
    assert compute_grade_trend_slope(grades) == pytest.approx(-2.0)


def test_grade_trend_slope_credit_weighted_average():
    grades = [
        _grade("t1", 8.0, credits=1.0, course="a"),
        _grade("t1", 4.0, credits=3.0, course="b"),  # term_avg t1 = (8*1+4*3)/4 = 5.0
        _grade("t2", 5.0, credits=1.0, course="a"),
    ]
    # single distinct value at t2 -> only 2 terms, slope = (5-5)/(1-0)=0
    assert compute_grade_trend_slope(grades) == pytest.approx(0.0)


def test_grade_trend_slope_three_terms_ols():
    grades = [_grade("t1", 8.0), _grade("t2", 7.0), _grade("t3", 9.0)]
    assert compute_grade_trend_slope(grades) == pytest.approx(0.5)


def test_grade_volatility_none_below_two_records():
    assert compute_grade_volatility([_grade("t1", 8.0)]) is None
    assert compute_grade_volatility([]) is None


def test_grade_volatility_matches_sample_stdev():
    grades = [_grade("t1", 8.0), _grade("t2", 6.0)]
    assert compute_grade_volatility(grades) == pytest.approx(math.sqrt(2))


def test_grade_volatility_ignores_null_final_grade():
    grades = [_grade("t1", 8.0), NormalizedTermGrade(term_code="t2", course_ref="c", final_grade=None)]
    assert compute_grade_volatility(grades) is None


def test_latest_term_gpa_none_without_grades():
    assert compute_latest_term_gpa([]) is None
    assert compute_latest_term_gpa(
        [NormalizedTermGrade(term_code="t1", course_ref="c", final_grade=None)]
    ) is None


def test_latest_term_gpa_picks_latest_term_credit_weighted():
    grades = [
        _grade("t1", 8.0, credits=1.0, course="a"),
        _grade("t1", 4.0, credits=3.0, course="b"),
        _grade("t2", 6.0, credits=2.0, course="a"),
        _grade("t2", 8.0, credits=2.0, course="b"),
    ]
    assert compute_latest_term_gpa(grades) == pytest.approx(7.0)


def test_failed_credits_none_without_term_grades():
    assert compute_failed_credits([]) is None


def test_failed_credits_zero_when_no_fail_status():
    assert compute_failed_credits([_grade("t1", 8.0, grade_status="[B - ]")]) == pytest.approx(0.0)


def test_failed_credits_sums_fail_rows_skips_missing_credits():
    grades = [
        _grade("t1", 3.0, credits=3.0, course="a", grade_status="Không đạt"),
        _grade("t1", 2.0, credits=2.0, course="b", grade_status="không đạt"),
        NormalizedTermGrade(
            term_code="t1",
            course_ref="c",
            credits=None,
            final_grade=1.0,
            grade_status="Không đạt",
        ),
        _grade("t2", 7.0, credits=3.0, course="d", grade_status="[C - ]"),
    ]
    assert compute_failed_credits(grades) == pytest.approx(5.0)


def test_failed_credits_ignores_non_fail_status():
    grades = [_grade("t1", 1.0, credits=3.0, grade_status="[D - ]")]
    assert compute_failed_credits(grades) == pytest.approx(0.0)


# --- Attendance branch feature computation ----------------------------------


def test_attendance_trend_slope_none_below_min_events():
    events = [_att(datetime(2026, 1, d, tzinfo=timezone.utc)) for d in (1, 2, 3)]
    assert compute_attendance_trend_slope(events) is None


def test_attendance_trend_slope_none_when_single_distinct_timestamp():
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    events = [_att(ts, course=str(i)) for i in range(4)]
    assert compute_attendance_trend_slope(events) is None


def test_attendance_trend_slope_excludes_excused_from_trend():
    events = [
        _att(datetime(2026, 1, 1, tzinfo=timezone.utc), status="present"),
        _att(datetime(2026, 1, 2, tzinfo=timezone.utc), status="absent"),
        _att(datetime(2026, 1, 3, tzinfo=timezone.utc), status="absent", excused=True),
        _att(datetime(2026, 1, 4, tzinfo=timezone.utc), status="present"),
    ]
    # valid=4 (gate passes); counted excludes the excused absence -> 3 distinct points
    slope = compute_attendance_trend_slope(events)
    assert slope is not None


def test_attendance_trend_slope_improving_is_positive():
    events = [
        _att(datetime(2026, 1, 1, tzinfo=timezone.utc), status="absent"),
        _att(datetime(2026, 1, 2, tzinfo=timezone.utc), status="absent"),
        _att(datetime(2026, 1, 3, tzinfo=timezone.utc), status="present"),
        _att(datetime(2026, 1, 4, tzinfo=timezone.utc), status="present"),
    ]
    slope = compute_attendance_trend_slope(events)
    assert slope == pytest.approx(0.4)


# --- score_student wiring ----------------------------------------------------


def test_score_student_semester_only_fills_grade_branch():
    record = _semester_record(
        [
            _grade("t1", 8.0, grade_status="[B - ]"),
            _grade("t2", 6.0, grade_status="Không đạt"),
        ]
    )
    features = score_student(record, calculated_at=_CALC_AT)
    assert isinstance(features, ScoringFeatures)
    assert features.model_version == MODEL_VERSION
    assert features.latest_term_gpa == pytest.approx(6.0)
    assert features.grade_trend_slope == pytest.approx(-2.0)
    assert features.grade_volatility == pytest.approx(math.sqrt(2))
    assert features.failed_credits == pytest.approx(3.0)
    assert features.attendance_rate_window is None
    assert features.attendance_trend_slope is None


def test_score_student_no_cross_join_attendance_only():
    coverage = Coverage(
        n_valid_terms=0,
        n_courses=0,
        n_attendance_events=4,
        last_attendance_at=datetime(2026, 1, 4, tzinfo=timezone.utc),
        status="ok",
        reason_codes=[],
    )
    events = [
        _att(datetime(2026, 1, 1, tzinfo=timezone.utc)),
        _att(datetime(2026, 1, 2, tzinfo=timezone.utc)),
        _att(datetime(2026, 1, 3, tzinfo=timezone.utc)),
        _att(datetime(2026, 1, 4, tzinfo=timezone.utc)),
    ]
    record = _attendance_record(events, coverage)
    features = score_student(record, calculated_at=_CALC_AT)
    assert features.latest_term_gpa is None
    assert features.grade_trend_slope is None
    assert features.grade_volatility is None
    assert features.failed_credits is None
    assert features.attendance_rate_window == 1.0


def test_score_student_boundary_no_forbidden_fields():
    record = _semester_record([_grade("t1", 8.0), _grade("t2", 6.0)])
    features = score_student(record, calculated_at=_CALC_AT)
    dumped = features.model_dump()
    for forbidden in ("is_dropout_outcome", "advisor_ref", "student_status", "token"):
        assert forbidden not in dumped


def test_score_student_deterministic():
    record = _semester_record([_grade("t1", 8.0), _grade("t2", 6.0), _grade("t3", 9.0)])
    a = score_student(record, calculated_at=_CALC_AT)
    b = score_student(record, calculated_at=_CALC_AT)
    assert a.model_dump() == b.model_dump()


# --- compute_model_score / band ---------------------------------------------


def test_model_score_none_when_no_branch_ready():
    coverage = attendance_unapproved_defaults(n_valid_terms=0, n_courses=0)
    features = ScoringFeatures(
        dataset_version="v59-empty-program-students:abcd1234:epu-1",
        model_version=MODEL_VERSION,
        threshold_config_version=DEFAULT_THRESHOLDS.version,
        calculated_at=_CALC_AT,
        student_ref="s-1",
        coverage=coverage,
    )
    assert compute_model_score(features) is None
    assert band_for_score(compute_model_score(features)) is None
    assert contributing_factors(features) == []


def test_model_score_monotonic_in_declining_grade_trend():
    coverage = attendance_unapproved_defaults(n_valid_terms=2, n_courses=2, last_term_code="t2")

    def features_for(slope: float) -> ScoringFeatures:
        return ScoringFeatures(
            dataset_version="v59-empty-program-students:abcd1234:epu-1",
            model_version=MODEL_VERSION,
            threshold_config_version=DEFAULT_THRESHOLDS.version,
            calculated_at=_CALC_AT,
            student_ref="s-1",
            grade_trend_slope=slope,
            coverage=coverage,
        )

    mild = compute_model_score(features_for(-0.5))
    steep = compute_model_score(features_for(-1.5))
    improving = compute_model_score(features_for(1.0))
    assert improving == pytest.approx(0.0)
    assert 0.0 < mild < steep <= 1.0


def test_model_score_clamped_at_one():
    coverage = attendance_unapproved_defaults(n_valid_terms=2, n_courses=2, last_term_code="t2")
    features = ScoringFeatures(
        dataset_version="v59-empty-program-students:abcd1234:epu-1",
        model_version=MODEL_VERSION,
        threshold_config_version=DEFAULT_THRESHOLDS.version,
        calculated_at=_CALC_AT,
        student_ref="s-1",
        grade_trend_slope=-100.0,
        grade_volatility=100.0,
        coverage=coverage,
    )
    assert compute_model_score(features) == pytest.approx(1.0)


def test_band_for_score_boundaries():
    thresholds = ThresholdConfig(version="t-1", tau_case=0.3, tau_high=0.6)
    assert band_for_score(None, thresholds) is None
    assert band_for_score(0.29, thresholds) is None
    assert band_for_score(0.3, thresholds) == "can_ra_soat"
    assert band_for_score(0.59, thresholds) == "can_ra_soat"
    assert band_for_score(0.6, thresholds) == "uu_tien_som"
    assert band_for_score(1.0, thresholds) == "uu_tien_som"


def test_threshold_config_rejects_inverted_taus():
    with pytest.raises(ValidationError):
        ThresholdConfig(version="t-1", tau_case=0.6, tau_high=0.3)


def test_band_sweep_is_monotonic_non_increasing():
    """Raising tau_case never *increases* the number of qualifying students."""
    scores = [0.1, 0.2, 0.34, 0.36, 0.5, 0.7, 0.9]
    taus = [0.0, 0.2, 0.35, 0.5, 0.8, 1.0]
    counts = []
    for tau in taus:
        cfg = ThresholdConfig(version="t-1", tau_case=tau, tau_high=max(tau, 0.9))
        counts.append(sum(1 for s in scores if band_for_score(s, cfg) is not None))
    assert counts == sorted(counts, reverse=True)


# --- contributing_factors -----------------------------------------------------


def test_contributing_factors_empty_when_no_signal():
    coverage = attendance_unapproved_defaults(n_valid_terms=2, n_courses=2, last_term_code="t2")
    features = ScoringFeatures(
        dataset_version="v59-empty-program-students:abcd1234:epu-1",
        model_version=MODEL_VERSION,
        threshold_config_version=DEFAULT_THRESHOLDS.version,
        calculated_at=_CALC_AT,
        student_ref="s-1",
        grade_trend_slope=1.0,  # improving, not risky
        coverage=coverage,
    )
    assert contributing_factors(features) == []


def test_contributing_factors_report_correct_codes():
    coverage = Coverage(
        n_valid_terms=2,
        n_courses=2,
        n_attendance_events=4,
        last_term_code="t2",
        last_attendance_at=datetime(2026, 1, 4, tzinfo=timezone.utc),
        status="ok",
        reason_codes=[],
    )
    features = ScoringFeatures(
        dataset_version="v59-empty-program-students:abcd1234:epu-1",
        model_version=MODEL_VERSION,
        threshold_config_version=DEFAULT_THRESHOLDS.version,
        calculated_at=_CALC_AT,
        student_ref="s-1",
        grade_trend_slope=-1.0,
        grade_volatility=2.0,
        attendance_rate_window=0.5,
        attendance_trend_slope=-0.05,
        coverage=coverage,
    )
    codes = {f.code for f in contributing_factors(features)}
    assert codes == {
        "grade_trend_declining",
        "grade_volatility_elevated",
        "attendance_rate_below_target",
        "attendance_trend_declining",
    }
    for factor in contributing_factors(features):
        assert factor.evidence_refs


def test_contributing_factors_include_gpa_and_failed_credits():
    coverage = attendance_unapproved_defaults(n_valid_terms=1, n_courses=2, last_term_code="t1")
    features = ScoringFeatures(
        dataset_version="v59-empty-program-students:abcd1234:epu-1",
        model_version=MODEL_VERSION,
        threshold_config_version=DEFAULT_THRESHOLDS.version,
        calculated_at=_CALC_AT,
        student_ref="s-1",
        latest_term_gpa=2.0,
        failed_credits=6.0,
        coverage=coverage,
    )
    codes = {f.code for f in contributing_factors(features)}
    assert codes == {"gpa_below_target", "failed_credits_elevated"}
    refs = {f.code: f.evidence_refs for f in contributing_factors(features)}
    assert refs["gpa_below_target"] == ["latest_term_gpa"]
    assert refs["failed_credits_elevated"] == ["failed_credits"]


@pytest.mark.parametrize("tau_case", [0.1, 0.2, 0.35, 0.5, 0.8])
def test_qualifying_score_always_has_a_factor(tau_case):
    """Whenever score crosses tau_case, at least one contributing factor exists.

    Property over a grid of grade/attendance sub-signal combinations —
    guards the FR (false alarm + explainability) requirement that every case
    band is accompanied by a visible driver.
    """
    coverage = Coverage(
        n_valid_terms=2,
        n_courses=2,
        n_attendance_events=4,
        last_term_code="t2",
        last_attendance_at=datetime(2026, 1, 4, tzinfo=timezone.utc),
        status="ok",
        reason_codes=[],
    )
    thresholds = ThresholdConfig(version="t-1", tau_case=tau_case, tau_high=max(tau_case, 0.9))
    for trend in (None, -0.1, -0.5, -1.0, -2.0, -3.0):
        for vol in (None, 0.5, 1.5, 3.0):
            for rate in (None, 0.9, 0.6, 0.2):
                for att_trend in (None, -0.02, -0.05, -0.2):
                    features = ScoringFeatures(
                        dataset_version="v59-empty-program-students:abcd1234:epu-1",
                        model_version=MODEL_VERSION,
                        threshold_config_version=DEFAULT_THRESHOLDS.version,
                        calculated_at=_CALC_AT,
                        student_ref="s-1",
                        grade_trend_slope=trend,
                        grade_volatility=vol,
                        attendance_rate_window=rate,
                        attendance_trend_slope=att_trend,
                        coverage=coverage,
                    )
                    score = compute_model_score(features)
                    band = band_for_score(score, thresholds)
                    if band is not None:
                        assert contributing_factors(features), (
                            f"band={band} score={score} but no factors "
                            f"(trend={trend}, vol={vol}, rate={rate}, att_trend={att_trend})"
                        )
