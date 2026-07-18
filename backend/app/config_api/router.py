"""H04 — GET /config/thresholds(+impact) and GET /fairness/report."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.cases.review_projection import score_band_only
from app.contracts.fairness import FairnessReport
from app.contracts.threshold_public import PublicThresholdConfig, ThresholdImpactResponse
from app.database import get_db
from app.dwh.importer import SEMESTER_SOURCE_ID
from app.dwh.read_adapter import ReadAdapterError, list_normalized_students
from app.ml.fairness import build_fairness_report
from app.ml.scoring import DEFAULT_THRESHOLDS, MODEL_VERSION, ThresholdConfig

router = APIRouter(tags=["config"])

# MVP label rule placeholder — no operational FPR claim (M03 catalog empty).
LABEL_RULE_VERSION = "gt-epu-mvp-insufficient"


def _public_from(thresholds: ThresholdConfig) -> PublicThresholdConfig:
    return PublicThresholdConfig(
        threshold_config_version=thresholds.version,
        tau_case=thresholds.tau_case,
        tau_high=thresholds.tau_high,
        model_version=MODEL_VERSION,
    )


@router.get("/config/thresholds", response_model=PublicThresholdConfig)
def get_thresholds() -> PublicThresholdConfig:
    return _public_from(DEFAULT_THRESHOLDS)


@router.get("/config/thresholds/impact", response_model=ThresholdImpactResponse)
def get_threshold_impact(
    tau_case: float = Query(default=DEFAULT_THRESHOLDS.tau_case, ge=0.0, le=1.0),
    tau_high: float = Query(default=DEFAULT_THRESHOLDS.tau_high, ge=0.0, le=1.0),
    source_id: str = Query(default=SEMESTER_SOURCE_ID),
    db: Session = Depends(get_db),
) -> ThresholdImpactResponse:
    """Aggregate counts only — no per-student model_score in the response."""
    if tau_high < tau_case:
        tau_high = tau_case
    thresholds = ThresholdConfig(
        version=DEFAULT_THRESHOLDS.version,
        tau_case=tau_case,
        tau_high=tau_high,
    )
    try:
        records = list_normalized_students(db, source_id)
    except ReadAdapterError:
        records = []
    except Exception:
        records = []

    n_scored = 0
    n_can = 0
    n_uu = 0
    n_no = 0
    for record in records:
        score, band = score_band_only(record, thresholds=thresholds)
        if score is None:
            n_no += 1
            continue
        n_scored += 1
        if band == "uu_tien_som":
            n_uu += 1
        elif band == "can_ra_soat":
            n_can += 1
        else:
            n_no += 1

    return ThresholdImpactResponse(
        threshold_config_version=thresholds.version,
        tau_case=thresholds.tau_case,
        tau_high=thresholds.tau_high,
        model_version=MODEL_VERSION,
        n_scored=n_scored,
        n_can_ra_soat=n_can,
        n_uu_tien_som=n_uu,
        n_no_case=n_no,
    )


@router.get("/fairness/report", response_model=FairnessReport)
def get_fairness_report(
    source_id: str = Query(default=SEMESTER_SOURCE_ID),
    db: Session = Depends(get_db),
) -> FairnessReport:
    """MVP always insufficient_data via empty APPROVED_AUDIT_ATTRIBUTES catalog."""
    dataset_version = f"{source_id}:mvp:schema-1"
    try:
        records = list_normalized_students(db, source_id)
        if records:
            dataset_version = records[0].dataset_version
    except Exception:
        pass

    return build_fairness_report(
        dataset_version=dataset_version,
        model_version=MODEL_VERSION,
        threshold_config_version=DEFAULT_THRESHOLDS.version,
        label_rule_version=LABEL_RULE_VERSION,
        computed_at=datetime.now(timezone.utc),
        audit_attribute=None,
    )
