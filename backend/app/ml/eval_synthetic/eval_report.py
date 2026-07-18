"""Thin M02 baseline eval harness (uncalibrated — decision #26)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.contracts.normalized import NormalizedStudentRecord
from app.ml.scoring import (
    DEFAULT_THRESHOLDS,
    MODEL_VERSION,
    band_for_score,
    compute_model_score,
    contributing_factors,
    score_student,
)


def run_baseline_eval(
    records: List[NormalizedStudentRecord],
    *,
    outcomes: Optional[Dict[str, Optional[bool]]] = None,
    calculated_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Score linked eval records; optional uncalibrated confusion vs outcomes."""
    calculated_at = calculated_at or datetime(2026, 7, 18, tzinfo=timezone.utc)
    outcomes = outcomes or {}

    n = len(records)
    feature_ready = {
        "latest_term_gpa": 0,
        "grade_trend_slope": 0,
        "grade_volatility": 0,
        "failed_credits": 0,
        "failed_credits_positive": 0,
        "attendance_rate_window": 0,
        "attendance_trend_slope": 0,
    }
    bands: Dict[str, int] = {"uu_tien_som": 0, "can_ra_soat": 0, "none": 0}
    tp = fp = tn = fn = skipped = 0

    for record in records:
        features = score_student(record, calculated_at=calculated_at)
        if features.latest_term_gpa is not None:
            feature_ready["latest_term_gpa"] += 1
        if features.grade_trend_slope is not None:
            feature_ready["grade_trend_slope"] += 1
        if features.grade_volatility is not None:
            feature_ready["grade_volatility"] += 1
        if features.failed_credits is not None:
            feature_ready["failed_credits"] += 1
            if features.failed_credits > 0:
                feature_ready["failed_credits_positive"] += 1
        if features.attendance_rate_window is not None:
            feature_ready["attendance_rate_window"] += 1
        if features.attendance_trend_slope is not None:
            feature_ready["attendance_trend_slope"] += 1

        score = compute_model_score(features)
        band = band_for_score(score, DEFAULT_THRESHOLDS)
        bands[band if band else "none"] += 1
        _ = contributing_factors(features)

        label = outcomes.get(record.student_ref)
        if label is None:
            skipped += 1
            continue
        predicted_positive = band is not None
        if predicted_positive and label:
            tp += 1
        elif predicted_positive and not label:
            fp += 1
        elif not predicted_positive and not label:
            tn += 1
        else:
            fn += 1

    rates = {k: (v / n if n else 0.0) for k, v in feature_ready.items()}
    return {
        "calibrated": False,
        "model_version": MODEL_VERSION,
        "threshold_config_version": DEFAULT_THRESHOLDS.version,
        "n_students": n,
        "feature_ready_counts": feature_ready,
        "feature_ready_rates": rates,
        "band_counts": bands,
        "confusion_uncalibrated": {
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
            "skipped_unknown_outcome": skipped,
        },
        "disclaimer": (
            "Uncalibrated wiring metrics on eval synthetic only; "
            "not operational FPR/TPR; not for public demo claims."
        ),
    }
