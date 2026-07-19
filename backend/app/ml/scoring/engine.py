"""Single scoring registry shared by all runtime consumers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from app.config import get_settings
from app.contracts.normalized import NormalizedStudentRecord
from app.contracts.review_case import ContributingFactor
from app.contracts.scoring import ScoringFeatures
from app.ml.dropout.artifact import LinearModelArtifact, load_artifact
from app.ml.dropout.runtime import score_features as score_linear_features
from app.ml.scoring.estimator import (
    band_for_score,
    compute_model_score,
    contributing_factors,
    score_student,
)
from app.ml.scoring.models import (
    BASELINE_MODEL_VERSION,
    BASELINE_THRESHOLDS,
    ThresholdConfig,
)


@dataclass(frozen=True)
class ScoredResult:
    features: ScoringFeatures
    model_score: Optional[float]
    review_priority_band: Optional[str]
    factors: List[ContributingFactor]
    limitations: List[str]
    reason_codes: List[str]
    artifact_sha256: Optional[str]


def default_artifact_path() -> Path:
    return Path(__file__).resolve().parents[1] / "artifacts" / "m10_reality460.json"


@lru_cache(maxsize=4)
def _artifact_for_path(path_text: str) -> LinearModelArtifact:
    artifact = load_artifact(Path(path_text))
    if not artifact.promoted:
        raise ValueError("model_artifact_not_promoted")
    return artifact


def active_artifact() -> LinearModelArtifact:
    settings = get_settings()
    path = Path(settings.scoring_model_artifact) if settings.scoring_model_artifact else default_artifact_path()
    artifact = _artifact_for_path(str(path.resolve()))
    if settings.scoring_model_version != artifact.model_version:
        raise ValueError("configured_model_version_mismatch")
    return artifact


def active_model_version() -> str:
    settings = get_settings()
    if settings.scoring_model_version == BASELINE_MODEL_VERSION:
        return BASELINE_MODEL_VERSION
    return active_artifact().model_version


def active_thresholds() -> ThresholdConfig:
    settings = get_settings()
    if settings.scoring_model_version == BASELINE_MODEL_VERSION:
        return BASELINE_THRESHOLDS
    artifact = active_artifact()
    return ThresholdConfig(
        version=artifact.threshold_config_version,
        tau_case=artifact.tau_case,
        tau_high=artifact.tau_high,
    )


def score_features(
    features: ScoringFeatures,
    *,
    thresholds: Optional[ThresholdConfig] = None,
) -> ScoredResult:
    settings = get_settings()
    if settings.scoring_model_version == BASELINE_MODEL_VERSION:
        effective = thresholds or BASELINE_THRESHOLDS
        score = compute_model_score(features)
        band = band_for_score(score, effective)
        factors = contributing_factors(features) if band is not None else []
        return ScoredResult(features, score, band, factors, [], [], None)

    artifact = active_artifact()
    effective = thresholds or active_thresholds()
    runtime = score_linear_features(
        features,
        artifact,
        tau_case=effective.tau_case,
        tau_high=effective.tau_high,
    )
    return ScoredResult(
        features=features,
        model_score=runtime.score,
        review_priority_band=runtime.review_priority_band,
        factors=runtime.factors,
        limitations=runtime.limitations,
        reason_codes=runtime.reason_codes,
        artifact_sha256=artifact.artifact_sha256,
    )


def score_record(
    record: NormalizedStudentRecord,
    *,
    calculated_at: Optional[datetime] = None,
    thresholds: Optional[ThresholdConfig] = None,
) -> ScoredResult:
    version = active_model_version()
    effective = thresholds or active_thresholds()
    features = score_student(
        record,
        calculated_at=calculated_at,
        model_version=version,
        threshold_config_version=effective.version,
    )
    return score_features(features, thresholds=effective)
