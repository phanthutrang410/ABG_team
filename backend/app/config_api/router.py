"""H04 — GET /config/thresholds(+impact) and GET /fairness/report (H39b: ban_quan_ly)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.principal import Principal, require_roles
from app.auth.rbac import audit, server_source_id
from app.cases.review_projection import score_band_only
from app.contracts.fairness import FairnessReport
from app.contracts.threshold_public import PublicThresholdConfig, ThresholdImpactResponse
from app.database import get_db
from app.dwh.read_adapter import ReadAdapterError, list_normalized_students
from app.ml.fairness import build_fairness_report
from app.ml.scoring import (
    ThresholdConfig,
    active_model_version,
    active_thresholds,
)

router = APIRouter(tags=["config"])

# MVP label rule placeholder — no operational FPR claim (M03 catalog empty).
LABEL_RULE_VERSION = "gt-epu-mvp-insufficient"


def _public_from(thresholds: ThresholdConfig) -> PublicThresholdConfig:
    return PublicThresholdConfig(
        threshold_config_version=thresholds.version,
        tau_case=thresholds.tau_case,
        tau_high=thresholds.tau_high,
        model_version=active_model_version(),
    )


@router.get("/config/thresholds", response_model=PublicThresholdConfig)
def get_thresholds(
    principal: Principal = Depends(require_roles("ban_quan_ly")),
    db: Session = Depends(get_db),
) -> PublicThresholdConfig:
    audit(
        principal,
        action="config.thresholds",
        resource_handle="config/thresholds",
        allowed=True,
        db=db,
    )
    return _public_from(active_thresholds())


@router.get("/config/thresholds/impact", response_model=ThresholdImpactResponse)
def get_threshold_impact(
    tau_case: float | None = Query(default=None, ge=0.0, le=1.0),
    tau_high: float | None = Query(default=None, ge=0.0, le=1.0),
    principal: Principal = Depends(require_roles("ban_quan_ly")),
    db: Session = Depends(get_db),
) -> ThresholdImpactResponse:
    """Aggregate counts only — no per-student model_score in the response."""
    source_id = server_source_id()
    active = active_thresholds()
    tau_case = active.tau_case if tau_case is None else tau_case
    tau_high = active.tau_high if tau_high is None else tau_high
    if tau_high < tau_case:
        tau_high = tau_case
    thresholds = ThresholdConfig(
        version=active.version,
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
        score, band = score_band_only(record, thresholds=thresholds, session=db)
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

    audit(
        principal,
        action="config.thresholds.impact",
        resource_handle="config/thresholds/impact",
        allowed=True,
        db=db,
    )
    return ThresholdImpactResponse(
        threshold_config_version=thresholds.version,
        tau_case=thresholds.tau_case,
        tau_high=thresholds.tau_high,
        model_version=active_model_version(),
        n_scored=n_scored,
        n_can_ra_soat=n_can,
        n_uu_tien_som=n_uu,
        n_no_case=n_no,
    )


@router.get("/fairness/report", response_model=FairnessReport)
def get_fairness_report(
    principal: Principal = Depends(require_roles("ban_quan_ly")),
    db: Session = Depends(get_db),
) -> FairnessReport:
    """MVP always insufficient_data via empty APPROVED_AUDIT_ATTRIBUTES catalog."""
    source_id = server_source_id()
    dataset_version = f"{source_id}:mvp:schema-1"
    try:
        records = list_normalized_students(db, source_id)
        if records:
            dataset_version = records[0].dataset_version
    except Exception:
        pass

    audit(
        principal,
        action="fairness.report",
        resource_handle="fairness/report",
        allowed=True,
        db=db,
    )
    return build_fairness_report(
        dataset_version=dataset_version,
        model_version=active_model_version(),
        threshold_config_version=active_thresholds().version,
        label_rule_version=LABEL_RULE_VERSION,
        computed_at=datetime.now(timezone.utc),
        audit_attribute=None,
    )
