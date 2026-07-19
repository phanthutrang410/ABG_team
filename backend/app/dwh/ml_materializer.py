"""Materialize M02 scoring into ``dwh.ml_term_snapshot``.

Reads approved normalized students (H08), runs baseline scoring (M02), and
replaces rows for ``source_id`` in one transaction. ``model_score`` stays in the
typed DB column only — never in ``agent_explain_json``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal, Optional

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.contracts.review_case import ContributingFactor
from app.contracts.scoring import ScoringFeatures
from app.dwh.models import MlTermSnapshot, SourceManifest
from app.dwh.read_adapter import ReadAdapterError, list_normalized_students
from app.ml.scoring import (
    BASELINE_MODEL_VERSION,
    active_artifact,
    active_model_version,
    score_record,
)

EXPLAIN_SCHEMA_VERSION = "agent-explain-v1"

#: Rounding for agent-safe feature projection (matches typed column scales).
_ROUND_GPA = 2
_ROUND_RATE = 4
_ROUND_SLOPE = 6


@dataclass
class MaterializeResult:
    """Outcome of a materialize pass (CLI / tests)."""

    status: Literal["materialized", "rejected"]
    source_id: str
    row_counts: dict[str, int] = field(default_factory=dict)
    reason_codes: list[str] = field(default_factory=list)
    detail: Optional[str] = None


def _round_opt(value: Optional[float], digits: int) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), digits)


def _decimal_opt(value: Optional[float], digits: int) -> Optional[Decimal]:
    rounded = _round_opt(value, digits)
    if rounded is None:
        return None
    return Decimal(str(rounded))


def rounded_feature_values(features: ScoringFeatures) -> dict[str, Optional[float]]:
    """Stable, rounded feature map for explain JSON + fingerprints."""
    return {
        "latest_term_gpa": _round_opt(features.latest_term_gpa, _ROUND_GPA),
        "grade_trend_slope": _round_opt(features.grade_trend_slope, _ROUND_SLOPE),
        "grade_volatility": _round_opt(features.grade_volatility, _ROUND_SLOPE),
        "failed_credits": _round_opt(features.failed_credits, _ROUND_GPA),
        "attendance_rate_window": _round_opt(features.attendance_rate_window, _ROUND_RATE),
        "attendance_trend_slope": _round_opt(features.attendance_trend_slope, _ROUND_SLOPE),
    }


def build_agent_explain_json(
    *,
    features: ScoringFeatures,
    review_priority_band: Optional[str],
    factors: list[ContributingFactor],
    limitations: Optional[list[str]] = None,
    artifact_sha256: Optional[str] = None,
) -> dict[str, Any]:
    """Rich agent-explain-v1 payload — never includes ``model_score``."""
    return {
        "explain_schema_version": EXPLAIN_SCHEMA_VERSION,
        "review_priority_band": review_priority_band,
        "factor_codes": [f.code for f in factors],
        "coverage_status": features.coverage.status,
        "coverage_reason_codes": list(features.coverage.reason_codes),
        "dataset_version": features.dataset_version,
        "model_version": features.model_version,
        "threshold_config_version": features.threshold_config_version,
        "last_term_code": features.coverage.last_term_code,
        "features": rounded_feature_values(features),
        "limitations": list(limitations or []),
        "artifact_sha256": artifact_sha256,
    }


def evidence_fingerprint(
    *,
    student_ref: str,
    review_priority_band: Optional[str],
    factor_codes: list[str],
    coverage_status: str,
    features: ScoringFeatures,
) -> str:
    """Deterministic sha256 over band / factors / key features (no wall clock)."""
    payload = {
        "student_ref": student_ref,
        "review_priority_band": review_priority_band,
        "factor_codes": sorted(factor_codes),
        "coverage_status": coverage_status,
        "features": rounded_feature_values(features),
        "last_term_code": features.coverage.last_term_code,
        "model_version": features.model_version,
        "threshold_config_version": features.threshold_config_version,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _row_from_scored(
    *,
    source_id: str,
    features: ScoringFeatures,
    model_score: Optional[float],
    review_priority_band: Optional[str],
    factors: list[ContributingFactor],
    limitations: Optional[list[str]] = None,
    artifact_sha256: Optional[str] = None,
) -> MlTermSnapshot:
    explain = build_agent_explain_json(
        features=features,
        review_priority_band=review_priority_band,
        factors=factors,
        limitations=limitations,
        artifact_sha256=artifact_sha256,
    )
    factor_codes = [f.code for f in factors]
    return MlTermSnapshot(
        source_id=source_id,
        student_ref=features.student_ref,
        dataset_version=features.dataset_version,
        model_version=features.model_version,
        threshold_config_version=features.threshold_config_version,
        calculated_at=features.calculated_at,
        last_term_code=features.coverage.last_term_code,
        latest_term_gpa=_decimal_opt(features.latest_term_gpa, _ROUND_GPA),
        grade_trend_slope=_decimal_opt(features.grade_trend_slope, _ROUND_SLOPE),
        grade_volatility=_decimal_opt(features.grade_volatility, _ROUND_SLOPE),
        failed_credits=_decimal_opt(features.failed_credits, _ROUND_GPA),
        attendance_rate_window=_decimal_opt(features.attendance_rate_window, _ROUND_RATE),
        attendance_trend_slope=_decimal_opt(features.attendance_trend_slope, _ROUND_SLOPE),
        coverage_status=features.coverage.status,
        coverage_json=json.dumps(
            features.coverage.model_dump(mode="json"),
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        review_priority_band=review_priority_band,
        contributing_factors_json=json.dumps(
            [f.model_dump(mode="json") for f in factors],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        model_score=_decimal_opt(model_score, 4),
        artifact_sha256=artifact_sha256,
        explain_schema_version=EXPLAIN_SCHEMA_VERSION,
        agent_explain_json=json.dumps(explain, ensure_ascii=False, separators=(",", ":")),
        evidence_fingerprint=evidence_fingerprint(
            student_ref=features.student_ref,
            review_priority_band=review_priority_band,
            factor_codes=factor_codes,
            coverage_status=features.coverage.status,
            features=features,
        ),
    )


def materialize_ml_term_snapshot(session: Session, source_id: str) -> MaterializeResult:
    """Score all approved students for ``source_id`` and replace ``ml_term_snapshot`` rows.

    Idempotent replace: ``DELETE WHERE source_id=…`` then bulk insert in the caller's
    transaction (caller commits). Fail-closed when H08 rejects the source.
    """
    sid = (source_id or "").strip()
    if not sid:
        return MaterializeResult(
            status="rejected",
            source_id=source_id or "",
            reason_codes=["source_unapproved"],
            detail="empty source_id",
        )

    try:
        records = list_normalized_students(session, sid)
    except ReadAdapterError as exc:
        return MaterializeResult(
            status="rejected",
            source_id=sid,
            reason_codes=list(exc.reason_codes),
            detail=exc.detail or str(exc),
        )

    try:
        model_version = active_model_version()
        if model_version != BASELINE_MODEL_VERSION:
            artifact = active_artifact()
            manifest = session.get(SourceManifest, sid)
            dataset_versions = {record.dataset_version for record in records}
            if (
                manifest is None
                or manifest.snapshot_sha256 != artifact.training_package_sha256
                or dataset_versions != {artifact.dataset_version}
                or len(records) != 460
            ):
                return MaterializeResult(
                    status="rejected",
                    source_id=sid,
                    reason_codes=["model_dataset_mismatch"],
                    detail="DWH source/count/version does not match the promoted artifact",
                )
    except (OSError, ValueError) as exc:
        return MaterializeResult(
            status="rejected",
            source_id=sid,
            reason_codes=["model_artifact_invalid"],
            detail=str(exc),
        )

    rows: list[MlTermSnapshot] = []
    try:
        for record in records:
            scored = score_record(record)
            features = scored.features
            score = scored.model_score
            band = scored.review_priority_band
            factors = scored.factors
            rows.append(
                _row_from_scored(
                    source_id=sid,
                    features=features,
                    model_score=score,
                    review_priority_band=band,
                    factors=factors,
                    limitations=scored.limitations,
                    artifact_sha256=scored.artifact_sha256,
                )
            )
    except (OSError, ValueError) as exc:
        return MaterializeResult(
            status="rejected",
            source_id=sid,
            reason_codes=["model_artifact_invalid"],
            detail=str(exc),
        )

    session.execute(delete(MlTermSnapshot).where(MlTermSnapshot.source_id == sid))
    session.add_all(rows)
    session.flush()

    return MaterializeResult(
        status="materialized",
        source_id=sid,
        row_counts={"ml_term_snapshot": len(rows)},
    )
