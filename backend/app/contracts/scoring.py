"""Internal ScoringFeatures envelope (H06a).

Semantics: docs/04-engineering/08-data-ml-scoring-fairness-contract.md §§1–2.
Internal only — estimator / H08. Không chiếu outcome, PII, advisor_ref, audit attrs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.contracts.coverage import Coverage


class ScoringFeatures(BaseModel):
    """Feature envelope for internal scoring — không phải public ReviewCase."""

    model_config = ConfigDict(extra="forbid")

    dataset_version: str = Field(min_length=1)
    model_version: str = Field(min_length=1, description="Feature spec + estimator version")
    threshold_config_version: str = Field(min_length=1)
    calculated_at: datetime

    student_ref: str = Field(min_length=1, description="Pseudonym; không phải MSSV")
    latest_term_gpa: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    grade_trend_slope: Optional[float] = None
    grade_volatility: Optional[float] = None
    failed_credits: Optional[float] = Field(default=None, ge=0.0)
    attendance_rate_window: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    attendance_trend_slope: Optional[float] = None
    coverage: Coverage
