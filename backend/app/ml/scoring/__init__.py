"""M02 — baseline semester + attendance-over-time scoring (Data-ML §§2–5)."""

from __future__ import annotations

from app.ml.scoring.estimator import (
    band_for_score,
    compute_attendance_trend_slope,
    compute_grade_trend_slope,
    compute_grade_volatility,
    compute_model_score,
    contributing_factors,
    score_student,
)
from app.ml.scoring.models import (
    DEFAULT_THRESHOLDS,
    MODEL_VERSION,
    THRESHOLD_CONFIG_VERSION,
    ThresholdConfig,
)

__all__ = [
    "DEFAULT_THRESHOLDS",
    "MODEL_VERSION",
    "THRESHOLD_CONFIG_VERSION",
    "ThresholdConfig",
    "band_for_score",
    "compute_attendance_trend_slope",
    "compute_grade_trend_slope",
    "compute_grade_volatility",
    "compute_model_score",
    "contributing_factors",
    "score_student",
]
