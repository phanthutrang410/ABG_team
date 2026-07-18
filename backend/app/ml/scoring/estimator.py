"""M02 — baseline semester + attendance-over-time scoring estimator.

Pure feature/score computation over `NormalizedStudentRecord` /
`ScoringFeatures` (H08 contracts) — no DB session, no outcome label. Semantics:
docs/04-engineering/08-data-ml-scoring-fairness-contract.md §§2–5.

Two independent branches (grade / attendance) never cross-join; each
contributes to `model_score` only when its own coverage produced a usable
feature. `model_score` and its sub-signals stay internal — H02 must only
project `review_priority_band` + `contributing_factors` + coverage.

`academic_status.is_dropout_outcome` is never read here (M02/M03 evaluation
only, Data-ML §5) — this module does not import the evaluation label.
"""

from __future__ import annotations

import statistics
from datetime import datetime
from typing import Dict, List, Optional

from app.contracts.normalized import (
    NormalizedAttendanceEvent,
    NormalizedStudentRecord,
    NormalizedTermGrade,
)
from app.contracts.review_case import ContributingFactor, ReviewPriorityBand
from app.contracts.scoring import ScoringFeatures
from app.dwh.read_adapter import to_scoring_features
from app.ml.domain.models import (
    ATTENDANCE_MIN_EVENTS,
    ATTENDANCE_MIN_TREND_POINTS,
    TERM_MIN_FOR_TREND,
)
from app.ml.scoring.models import DEFAULT_THRESHOLDS, MODEL_VERSION, ThresholdConfig

#: Heuristic normalization scales (uncalibrated — Data-ML §4). A component
#: reaches its full [0,1] contribution at these magnitudes; documented so the
#: baseline is auditable, not a black box.
GRADE_TREND_SCALE = 2.0
GRADE_VOLATILITY_SCALE = 3.0
ATTENDANCE_RATE_TARGET = 0.8
ATTENDANCE_TREND_SCALE = 0.1

#: Minimum clamped sub-signal value to surface as a contributing factor —
#: avoids flagging noise-level slope/volatility as an explained risk driver.
FACTOR_MATERIALITY = 0.05


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _ols_slope(xs: List[float], ys: List[float]) -> Optional[float]:
    """Least-squares slope of `ys` on `xs`; `None` if fewer than 2 distinct `xs`."""
    n = len(xs)
    if n < 2:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs)
    if var_x == 0:
        return None
    cov_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    return cov_xy / var_x


def _term_avg(term_grades: List[NormalizedTermGrade]) -> Dict[str, float]:
    """Credit-weighted average `final_grade` per `term_code` (Data-ML §2.1)."""
    sums: Dict[str, float] = {}
    weights: Dict[str, float] = {}
    for g in term_grades:
        if g.final_grade is None:
            continue
        w = g.credits if g.credits and g.credits > 0 else 1.0
        sums[g.term_code] = sums.get(g.term_code, 0.0) + g.final_grade * w
        weights[g.term_code] = weights.get(g.term_code, 0.0) + w
    return {t: sums[t] / weights[t] for t in sums}


def compute_grade_trend_slope(term_grades: List[NormalizedTermGrade]) -> Optional[float]:
    """OLS slope of `term_avg` over normalized term order (Data-ML §2.1).

    `None` when fewer than `TERM_MIN_FOR_TREND` valid terms.
    """
    term_avg = _term_avg(term_grades)
    terms = sorted(term_avg)
    if len(terms) < TERM_MIN_FOR_TREND:
        return None
    xs = list(range(len(terms)))
    ys = [term_avg[t] for t in terms]
    return _ols_slope(xs, ys)


def compute_grade_volatility(term_grades: List[NormalizedTermGrade]) -> Optional[float]:
    """Sample stddev of valid `final_grade` records (Data-ML §2.1). `None` if <2."""
    values = [g.final_grade for g in term_grades if g.final_grade is not None]
    if len(values) < 2:
        return None
    return statistics.stdev(values)


def compute_attendance_trend_slope(
    events: List[NormalizedAttendanceEvent],
) -> Optional[float]:
    """Slope of presence rate over distinct `observed_at` timestamps (Data-ML §2.2).

    Gated exactly like `attendance_rate_window`: requires
    `ATTENDANCE_MIN_EVENTS` valid (`presence_status` not null) events, then
    `ATTENDANCE_MIN_TREND_POINTS` distinct timestamps among the non-excused
    (counted) set. `excused=true` is excluded from the trend the same way it
    is excluded from the rate denominator.
    """
    valid = [e for e in events if e.presence_status is not None]
    if len(valid) < ATTENDANCE_MIN_EVENTS:
        return None
    counted = [e for e in valid if e.excused is not True]
    if not counted:
        return None
    by_ts: Dict[datetime, List[float]] = {}
    for e in counted:
        by_ts.setdefault(e.observed_at, []).append(1.0 if e.presence_status == "present" else 0.0)
    timestamps = sorted(by_ts)
    if len(timestamps) < ATTENDANCE_MIN_TREND_POINTS:
        return None
    xs = list(range(len(timestamps)))
    ys = [sum(by_ts[t]) / len(by_ts[t]) for t in timestamps]
    return _ols_slope(xs, ys)


def score_student(
    record: NormalizedStudentRecord,
    *,
    calculated_at: Optional[datetime] = None,
    model_version: str = MODEL_VERSION,
    threshold_config_version: str = DEFAULT_THRESHOLDS.version,
) -> ScoringFeatures:
    """Project a `NormalizedStudentRecord` to `ScoringFeatures` with M02 outputs.

    Only fills the branch(es) the record's own coverage supports (H08 already
    fail-closes cross-source joins) — never imputes a missing branch.
    """
    return to_scoring_features(
        record,
        model_version=model_version,
        threshold_config_version=threshold_config_version,
        calculated_at=calculated_at,
        grade_trend_slope=compute_grade_trend_slope(record.term_grades),
        grade_volatility=compute_grade_volatility(record.term_grades),
        attendance_trend_slope=compute_attendance_trend_slope(record.attendance_events),
    )


def _grade_signals(features: ScoringFeatures) -> Dict[str, float]:
    """Clamped [0,1] risk contribution per grade sub-signal; empty keys omitted."""
    signals: Dict[str, float] = {}
    if features.grade_trend_slope is not None:
        signals["grade_trend_declining"] = _clamp01(
            -features.grade_trend_slope / GRADE_TREND_SCALE
        )
    if features.grade_volatility is not None:
        signals["grade_volatility_elevated"] = _clamp01(
            features.grade_volatility / GRADE_VOLATILITY_SCALE
        )
    return signals


def _attendance_signals(features: ScoringFeatures) -> Dict[str, float]:
    """Clamped [0,1] risk contribution per attendance sub-signal."""
    signals: Dict[str, float] = {}
    if features.attendance_rate_window is not None:
        signals["attendance_rate_below_target"] = _clamp01(
            (ATTENDANCE_RATE_TARGET - features.attendance_rate_window) / ATTENDANCE_RATE_TARGET
        )
    if features.attendance_trend_slope is not None:
        signals["attendance_trend_declining"] = _clamp01(
            -features.attendance_trend_slope / ATTENDANCE_TREND_SCALE
        )
    return signals


def compute_model_score(features: ScoringFeatures) -> Optional[float]:
    """Internal risk score in [0,1] from ready branches only (Data-ML §§2.3, 4).

    `None` when neither branch has a usable feature — caller must not create a
    case / band in that situation (mirrors `coverage.status=insufficient`).
    Each ready branch is a simple average of its own available sub-signals
    (a feature that is present but not risky contributes 0, not "missing") so
    a branch with one weak signal is not artificially inflated by a small
    denominator. Branches are averaged with equal weight when both are ready.
    """
    grade_signals = _grade_signals(features)
    attendance_signals = _attendance_signals(features)
    grade_ready = features.grade_trend_slope is not None or features.grade_volatility is not None
    attendance_ready = (
        features.attendance_rate_window is not None or features.attendance_trend_slope is not None
    )
    if not grade_ready and not attendance_ready:
        return None

    branch_scores: List[float] = []
    if grade_ready:
        n = sum(1 for f in (features.grade_trend_slope, features.grade_volatility) if f is not None)
        branch_scores.append(sum(grade_signals.values()) / n)
    if attendance_ready:
        n = sum(
            1
            for f in (features.attendance_rate_window, features.attendance_trend_slope)
            if f is not None
        )
        branch_scores.append(sum(attendance_signals.values()) / n)
    return round(sum(branch_scores) / len(branch_scores), 6)


def band_for_score(
    score: Optional[float], thresholds: ThresholdConfig = DEFAULT_THRESHOLDS
) -> Optional[ReviewPriorityBand]:
    """Map an internal score to the public band (Data-ML §4). `None` ⇒ no case."""
    if score is None:
        return None
    if score >= thresholds.tau_high:
        return "uu_tien_som"
    if score >= thresholds.tau_case:
        return "can_ra_soat"
    return None


def contributing_factors(features: ScoringFeatures) -> List[ContributingFactor]:
    """Machine-readable factor codes for signals above `FACTOR_MATERIALITY`.

    No weights, no Vietnamese copy (H12a owns copy). `evidence_refs` point at
    the `ScoringFeatures` field name backing each code.
    """
    signals = {**_grade_signals(features), **_attendance_signals(features)}
    evidence_ref = {
        "grade_trend_declining": "grade_trend_slope",
        "grade_volatility_elevated": "grade_volatility",
        "attendance_rate_below_target": "attendance_rate_window",
        "attendance_trend_declining": "attendance_trend_slope",
    }
    return [
        ContributingFactor(code=code, evidence_refs=[evidence_ref[code]])
        for code, value in signals.items()
        if value >= FACTOR_MATERIALITY
    ]
