"""H04 — public threshold DTO (no raw scores)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PublicThresholdConfig(BaseModel):
    """Versioned public threshold wiring — FR-10 / G04 safe fields only."""

    model_config = ConfigDict(extra="forbid")

    threshold_config_version: str = Field(min_length=1)
    tau_case: float = Field(ge=0.0, le=1.0)
    tau_high: float = Field(ge=0.0, le=1.0)
    model_version: str = Field(min_length=1)


class ThresholdImpactResponse(BaseModel):
    """Aggregate band counts only — never per-student scores (FR-10)."""

    model_config = ConfigDict(extra="forbid")

    threshold_config_version: str = Field(min_length=1)
    tau_case: float = Field(ge=0.0, le=1.0)
    tau_high: float = Field(ge=0.0, le=1.0)
    model_version: str = Field(min_length=1)
    n_scored: int = Field(ge=0)
    n_can_ra_soat: int = Field(ge=0)
    n_uu_tien_som: int = Field(ge=0)
    n_no_case: int = Field(ge=0)
