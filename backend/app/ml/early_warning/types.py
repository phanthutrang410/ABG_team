"""Feature and prediction contracts for Silent Shield early-warning."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EarlyWarningFeatures:
    """Non-invasive meta signals only (ADR-0002)."""

    student_id: str
    grade_volatility_30d: float
    attendance_rate_30d: float
    attendance_trend_slope: float
    grade_trend_slope: float
    # Synthetic protected attrs for fairness demo — never real PII
    synth_socioeconomic_group: str | None = None
    synth_ethnicity_group: str | None = None


@dataclass(frozen=True)
class EarlyWarningPrediction:
    """Stored in schema ml; LLM may explain but not invent (ADR-0001)."""

    student_id: str
    risk_score: float
    model_version: str
    contributing_factors: dict[str, float] = field(default_factory=dict)
