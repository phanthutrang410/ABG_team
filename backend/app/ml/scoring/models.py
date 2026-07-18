"""M02 — baseline scoring constants + threshold config.

Placeholder tau values are wiring-only (Data-ML §4): "Không chốt số τ trước
M02 trên snapshot đã duyệt." `THRESHOLD_CONFIG_VERSION` carries the
`-uncalibrated` suffix so no consumer can mistake this for a calibrated FPR
claim — recalibrate against an approved snapshot before any operational use.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

#: Feature-spec + estimator version (Data-ML §1). Bump when the formula changes.
MODEL_VERSION = "m02-baseline-0.1"

#: Wiring-only threshold set — matches H08's DEFAULT_THRESHOLD_VERSION placeholder.
THRESHOLD_CONFIG_VERSION = "thr-epu-0.1-uncalibrated"


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


#: Uncalibrated wiring default — do not cite as an operational FPR/TPR claim.
DEFAULT_THRESHOLDS = ThresholdConfig(
    version=THRESHOLD_CONFIG_VERSION, tau_case=0.35, tau_high=0.65
)
