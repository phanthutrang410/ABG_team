"""M02 — baseline scoring constants + threshold config.

Placeholder tau values are wiring-only (Data-ML §4): "Không chốt số τ trước
M02 trên snapshot đã duyệt." `THRESHOLD_CONFIG_VERSION` carries the
`-uncalibrated` suffix so no consumer can mistake this for a calibrated FPR
claim — recalibrate against an approved snapshot before any operational use.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

#: Explicit rollback target; never selected automatically on artifact failure.
BASELINE_MODEL_VERSION = "m02-baseline-0.2"

#: Active supervised Reality-460 model.
MODEL_VERSION = "m10-reality460-logreg-1.0"

#: Wiring-only threshold set — matches H08's DEFAULT_THRESHOLD_VERSION placeholder.
BASELINE_THRESHOLD_CONFIG_VERSION = "thr-epu-0.1-uncalibrated"
THRESHOLD_CONFIG_VERSION = "thr-reality460-oof-recall70-v1"


class ThresholdConfig(BaseModel):
    """Versioned `tau_case` / `tau_high` pair (Data-ML §4). H04 will expose this."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1)
    tau_case: float = Field(ge=0.0, le=1.0)
    tau_high: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _ordered(self) -> "ThresholdConfig":
        if self.tau_high < self.tau_case:
            raise ValueError("tau_high phải >= tau_case")
        return self


#: OOF-selected Reality-460 thresholds. Raw score remains internal-only.
DEFAULT_THRESHOLDS = ThresholdConfig(
    version=THRESHOLD_CONFIG_VERSION,
    tau_case=0.46559848023232425,
    tau_high=0.5502363412821223,
)

BASELINE_THRESHOLDS = ThresholdConfig(
    version=BASELINE_THRESHOLD_CONFIG_VERSION,
    tau_case=0.35,
    tau_high=0.65,
)
