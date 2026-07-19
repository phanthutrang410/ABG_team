"""Safe JSON artifact contract for the M10 linear model.

The artifact contains aggregate training metadata and linear parameters only.
It deliberately contains no student identifiers, labels, raw rows, or OOF
predictions.  The embedded digest is computed with ``artifact_sha256`` blank,
which makes verification deterministic without a self-referential hash.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ARTIFACT_SCHEMA_VERSION = "ml-linear-artifact-v1"
MODEL_VERSION = "m10-reality460-logreg-1.0"
THRESHOLD_CONFIG_VERSION = "thr-reality460-oof-recall70-v1"
LABEL_RULE_VERSION = "gt-epu-status-after-t2-v1"


class LinearModelArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_schema_version: Literal["ml-linear-artifact-v1"] = ARTIFACT_SCHEMA_VERSION
    model_version: Literal["m10-reality460-logreg-1.0"] = MODEL_VERSION
    threshold_config_version: Literal["thr-reality460-oof-recall70-v1"] = (
        THRESHOLD_CONFIG_VERSION
    )
    dataset_version: str = Field(min_length=1)
    source_snapshot_sha256: str = Field(min_length=64, max_length=64)
    training_package_sha256: str = Field(min_length=64, max_length=64)
    label_rule_version: Literal["gt-epu-status-after-t2-v1"] = LABEL_RULE_VERSION
    feature_cutoff: Literal["2022-2023-T2"] = "2022-2023-T2"
    feature_set: Literal["A", "B"]
    feature_order: List[str]
    transforms: Dict[str, str]
    means: Dict[str, float]
    scales: Dict[str, float]
    coefficients: Dict[str, float]
    intercept: float
    regularization_c: float = Field(gt=0)
    random_seed: int
    tau_case: float = Field(ge=0, le=1)
    tau_high: float = Field(ge=0, le=1)
    promoted: bool
    aggregate_metrics: Dict[str, float]
    limitations: List[str] = Field(default_factory=list)
    artifact_sha256: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def _consistent(self) -> "LinearModelArtifact":
        keys = set(self.feature_order)
        for mapping in (self.transforms, self.means, self.scales, self.coefficients):
            if set(mapping) != keys:
                raise ValueError("feature parameter keys must match feature_order")
        if any(self.scales[name] <= 0 for name in self.feature_order):
            raise ValueError("all feature scales must be positive")
        if self.tau_high < self.tau_case:
            raise ValueError("tau_high must be >= tau_case")
        return self

    def canonical_bytes_for_digest(self) -> bytes:
        payload = self.model_dump(mode="json")
        payload["artifact_sha256"] = ""
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def computed_sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes_for_digest()).hexdigest()

    def verify_digest(self) -> None:
        actual = self.computed_sha256()
        if actual != self.artifact_sha256:
            raise ValueError(
                f"artifact_hash_mismatch: expected={self.artifact_sha256} actual={actual}"
            )


def finalized_artifact(payload: dict) -> LinearModelArtifact:
    payload = dict(payload)
    payload["artifact_sha256"] = "0" * 64
    candidate = LinearModelArtifact.model_validate(payload)
    payload["artifact_sha256"] = candidate.computed_sha256()
    return LinearModelArtifact.model_validate(payload)


def load_artifact(path: Path) -> LinearModelArtifact:
    artifact = LinearModelArtifact.model_validate_json(path.read_text(encoding="utf-8"))
    artifact.verify_digest()
    return artifact


def write_artifact(artifact: LinearModelArtifact, path: Path) -> None:
    artifact.verify_digest()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
