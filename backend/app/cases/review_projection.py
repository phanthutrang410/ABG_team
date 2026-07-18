"""H02 — project NormalizedStudentRecord → public ReviewCase (no raw score).

Consumes M02 scoring + CaseStore. Does not invent scores or change formulas.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from app.cases.store import CaseStore
from app.contracts.coverage import Coverage
from app.contracts.normalized import NormalizedStudentRecord
from app.contracts.review_case import ReviewCase
from app.ml.scoring import (
    DEFAULT_THRESHOLDS,
    MODEL_VERSION,
    ThresholdConfig,
    band_for_score,
    compute_model_score,
    contributing_factors,
    score_student,
)

CASE_ID_PREFIX = "rc-"

# Snapshot older than this -> list/detail envelope state=stale (H11a).
DEFAULT_STALE_AFTER = timedelta(days=7)


def case_id_for_student(student_ref: str) -> str:
    return f"{CASE_ID_PREFIX}{student_ref}"


def student_ref_from_case_id(case_id: str) -> Optional[str]:
    cid = (case_id or "").strip()
    if not cid.startswith(CASE_ID_PREFIX):
        return None
    ref = cid[len(CASE_ID_PREFIX) :]
    return ref or None


def _data_state_for(coverage: Coverage) -> str:
    if coverage.status == "insufficient":
        return "insufficient_data"
    if coverage.status == "partial":
        return "partial"
    return "ok"


def _limitations(coverage: Coverage) -> List[str]:
    return list(coverage.reason_codes)


def is_snapshot_stale(
    calculated_at: datetime,
    *,
    now: Optional[datetime] = None,
    stale_after: timedelta = DEFAULT_STALE_AFTER,
) -> bool:
    """Freshness gate for H11a stale envelopes based on projection time."""
    clock = now or datetime.now(timezone.utc)
    ts = calculated_at
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (clock - ts) > stale_after


def ensure_case_snapshot(
    store: CaseStore,
    *,
    case_id: str,
    student_ref: str,
    source_id: str,
) -> str:
    """Ensure CaseStore has a snapshot; return current case_state value."""
    existing = store.get(case_id)
    if existing is None:
        existing = store.create(
            case_id,
            state="new_signal",
            advisor_ref=None,
            student_ref=student_ref,
            source_id=source_id,
        )
    return existing.state.value


def project_review_case(
    record: NormalizedStudentRecord,
    store: CaseStore,
    *,
    thresholds: ThresholdConfig = DEFAULT_THRESHOLDS,
    calculated_at: Optional[datetime] = None,
    include_below_threshold: bool = False,
) -> Optional[ReviewCase]:
    """Build a public ReviewCase, or None when no case should be surfaced.

    Rules (Data-ML + plan):
    - coverage.status=insufficient -> ReviewCase with band=None (detail insufficient_data).
    - score/band is None and coverage ready -> no case (unless include_below_threshold).
    - band set -> ensure CaseStore snapshot; never attach model_score / advisor_ref / PII.
    """
    calc_at = calculated_at or datetime.now(timezone.utc)
    features = score_student(
        record,
        calculated_at=calc_at,
        model_version=MODEL_VERSION,
        threshold_config_version=thresholds.version,
    )
    score = compute_model_score(features)
    band = band_for_score(score, thresholds)
    factors = contributing_factors(features)
    coverage = record.coverage
    data_state = _data_state_for(coverage)

    if coverage.status == "insufficient":
        case_id = case_id_for_student(record.student_ref)
        case_state = ensure_case_snapshot(
            store,
            case_id=case_id,
            student_ref=record.student_ref,
            source_id=record.source_id,
        )
        return ReviewCase(
            case_id=case_id,
            student_ref=record.student_ref,
            case_state=case_state,  # type: ignore[arg-type]
            review_priority_band=None,
            contributing_factors=[],
            coverage=coverage,
            data_state="insufficient_data",
            limitations=_limitations(coverage),
            dataset_version=record.dataset_version,
            model_version=MODEL_VERSION,
            threshold_config_version=thresholds.version,
            calculated_at=calc_at,
        )

    if band is None and not include_below_threshold:
        return None

    # coverage ok requires non-empty factors — skip if materiality filtered everything
    if coverage.status == "ok" and not factors:
        return None
    if data_state == "ok" and not factors:
        data_state = "partial"

    case_id = case_id_for_student(record.student_ref)
    case_state = ensure_case_snapshot(
        store,
        case_id=case_id,
        student_ref=record.student_ref,
        source_id=record.source_id,
    )
    return ReviewCase(
        case_id=case_id,
        student_ref=record.student_ref,
        case_state=case_state,  # type: ignore[arg-type]
        review_priority_band=band,
        contributing_factors=factors,
        coverage=coverage,
        data_state=data_state,  # type: ignore[arg-type]
        limitations=_limitations(coverage),
        dataset_version=record.dataset_version,
        model_version=MODEL_VERSION,
        threshold_config_version=thresholds.version,
        calculated_at=calc_at,
    )


def project_list_items(
    records: List[NormalizedStudentRecord],
    store: CaseStore,
    *,
    thresholds: ThresholdConfig = DEFAULT_THRESHOLDS,
    calculated_at: Optional[datetime] = None,
) -> List[ReviewCase]:
    """List only cases with a public band (skips below-threshold + insufficient)."""
    items: List[ReviewCase] = []
    for record in records:
        if record.coverage.status == "insufficient":
            continue
        case = project_review_case(
            record,
            store,
            thresholds=thresholds,
            calculated_at=calculated_at,
            include_below_threshold=False,
        )
        if case is not None and case.review_priority_band is not None:
            items.append(case)
    return items


def score_band_only(
    record: NormalizedStudentRecord,
    *,
    thresholds: ThresholdConfig = DEFAULT_THRESHOLDS,
) -> Tuple[Optional[float], Optional[str]]:
    """Internal helper for H04 impact aggregates — callers must not leak score."""
    features = score_student(
        record,
        model_version=MODEL_VERSION,
        threshold_config_version=thresholds.version,
    )
    score = compute_model_score(features)
    band = band_for_score(score, thresholds)
    return score, band
