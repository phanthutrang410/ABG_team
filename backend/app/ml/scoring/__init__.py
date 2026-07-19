"""M02 feature extraction plus the active M10 scoring registry."""

from __future__ import annotations

from app.ml.scoring.engine import (
    ScoredResult,
    active_artifact,
    active_model_version,
    active_thresholds,
    score_record,
)
from app.ml.scoring.estimator import (
    band_for_score,
    compute_attendance_rate_window,
    compute_attendance_trend_slope,
    compute_failed_credits,
    compute_grade_trend_slope,
    compute_grade_volatility,
    compute_latest_term_gpa,
    compute_model_score,
    contributing_factors,
    score_student,
)
from app.ml.scoring.models import (
    BASELINE_MODEL_VERSION,
    BASELINE_THRESHOLDS,
    DEFAULT_THRESHOLDS,
    MODEL_VERSION,
    THRESHOLD_CONFIG_VERSION,
    ThresholdConfig,
)

__all__ = [
    "BASELINE_MODEL_VERSION",
    "BASELINE_THRESHOLDS",
    "DEFAULT_THRESHOLDS",
    "MODEL_VERSION",
    "THRESHOLD_CONFIG_VERSION",
    "ScoredResult",
    "ThresholdConfig",
    "active_artifact",
    "active_model_version",
    "active_thresholds",
    "band_for_score",
    "compute_attendance_rate_window",
    "compute_attendance_trend_slope",
    "compute_failed_credits",
    "compute_grade_trend_slope",
    "compute_grade_volatility",
    "compute_latest_term_gpa",
    "compute_model_score",
    "contributing_factors",
    "score_record",
    "score_student",
]
