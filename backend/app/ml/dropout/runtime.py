"""Pure-Python runtime for the safe linear JSON artifact."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from app.contracts.review_case import ContributingFactor
from app.contracts.scoring import ScoringFeatures
from app.ml.dropout.artifact import LinearModelArtifact


@dataclass(frozen=True)
class RuntimeScore:
    score: Optional[float]
    review_priority_band: Optional[str]
    factors: List[ContributingFactor]
    limitations: List[str]
    reason_codes: List[str]


def _raw_values(features: ScoringFeatures, artifact: LinearModelArtifact) -> Optional[dict]:
    if features.coverage.n_valid_terms < 2:
        return None
    if features.latest_term_gpa is None or features.failed_credits is None:
        return None
    raw = {
        "latest_term_gpa": float(features.latest_term_gpa),
        "failed_credits_log1p": math.log1p(float(features.failed_credits)),
    }
    if "grade_trend_slope" in artifact.feature_order:
        if features.grade_trend_slope is None:
            return None
        raw["grade_trend_slope"] = float(features.grade_trend_slope)
    return raw


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def _factors(
    features: ScoringFeatures,
    artifact: LinearModelArtifact,
) -> List[ContributingFactor]:
    refs = {
        "latest_term_gpa": (5.0, "gpa_below_target", "latest_term_gpa"),
        "failed_credits_log1p": (0.0, "failed_credits_elevated", "failed_credits"),
        "grade_trend_slope": (0.0, "grade_trend_declining", "grade_trend_slope"),
    }
    raw = _raw_values(features, artifact)
    if raw is None:
        return []
    contributions: list[tuple[str, str, float]] = []
    for name in artifact.feature_order:
        neutral, code, evidence = refs[name]
        value = raw[name]
        if name == "failed_credits_log1p":
            neutral = math.log1p(neutral)
        contribution = artifact.coefficients[name] * (value - neutral) / artifact.scales[name]
        if contribution > 0:
            contributions.append((code, evidence, contribution))
    if not contributions:
        return []
    largest = max(value for _code, _evidence, value in contributions)
    material = [item for item in contributions if item[2] >= 0.2 * largest]
    if not material:
        material = [max(contributions, key=lambda item: item[2])]
    return [
        ContributingFactor(code=code, evidence_refs=[evidence])
        for code, evidence, _value in material
    ]


def score_features(
    features: ScoringFeatures,
    artifact: LinearModelArtifact,
    *,
    tau_case: Optional[float] = None,
    tau_high: Optional[float] = None,
) -> RuntimeScore:
    raw = _raw_values(features, artifact)
    limitations = list(artifact.limitations)
    if raw is None:
        return RuntimeScore(
            score=None,
            review_priority_band=None,
            factors=[],
            limitations=limitations,
            reason_codes=["grade_coverage_insufficient"],
        )
    logit = artifact.intercept
    for name in artifact.feature_order:
        standardized = (raw[name] - artifact.means[name]) / artifact.scales[name]
        logit += artifact.coefficients[name] * standardized
    score = round(_sigmoid(logit), 12)
    case_threshold = artifact.tau_case if tau_case is None else tau_case
    high_threshold = artifact.tau_high if tau_high is None else max(tau_high, case_threshold)
    band: Optional[str]
    if score >= high_threshold:
        band = "uu_tien_som"
    elif score >= case_threshold:
        band = "can_ra_soat"
    else:
        band = None
    factors = _factors(features, artifact) if band is not None else []
    reasons: List[str] = []
    if band is not None and not factors:
        band = None
        reasons.append("factor_coverage_insufficient")
    return RuntimeScore(
        score=score,
        review_priority_band=band,
        factors=factors,
        limitations=limitations,
        reason_codes=reasons,
    )
