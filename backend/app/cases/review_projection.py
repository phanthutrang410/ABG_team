"""H02 — project NormalizedStudentRecord → public ReviewCase (no raw score).

Consumes M02 scoring + CaseStore. Prefers ``ml_term_snapshot`` when a DB session
is provided and a row exists (D460-11); otherwise live ``score_student``.
Does not invent scores or change formulas.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.cases.store import CaseStore
from app.contracts.coverage import Coverage
from app.contracts.normalized import NormalizedStudentRecord
from app.contracts.review_case import ContributingFactor, ReviewCase
from app.contracts.scoring import ScoringFeatures
from app.dwh.ml_snapshot_reader import get_ml_term_projection, get_ml_term_snapshot
from app.ml.scoring import DEFAULT_THRESHOLDS, ThresholdConfig, score_record

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


def _resolve_scored(
    record: NormalizedStudentRecord,
    *,
    session: Optional[Session],
    thresholds: ThresholdConfig,
    calculated_at: datetime,
) -> tuple[
    ScoringFeatures,
    Optional[str],
    List[ContributingFactor],
    Optional[float],
    List[str],
]:
    """Prefer materialized ``ml_term_snapshot``; else live M02.

    Returns ``(features, band, factors, model_score_or_none)``.
    ``model_score_or_none`` is only for internal callers (H04); public path
    must ignore it. Snapshot path never recomputes M02.
    """
    if session is not None:
        projection = get_ml_term_projection(session, record.source_id, record.student_ref)
        if projection is not None:
            return (
                projection.features,
                projection.review_priority_band,
                list(projection.contributing_factors),
                None,
                list(projection.limitations),
            )

    scored = score_record(
        record,
        calculated_at=calculated_at,
        thresholds=thresholds,
    )
    return (
        scored.features,
        scored.review_priority_band,
        scored.factors,
        scored.model_score,
        scored.limitations,
    )


def project_review_case(
    record: NormalizedStudentRecord,
    store: CaseStore,
    *,
    thresholds: ThresholdConfig = DEFAULT_THRESHOLDS,
    calculated_at: Optional[datetime] = None,
    include_below_threshold: bool = False,
    session: Optional[Session] = None,
) -> Optional[ReviewCase]:
    """Build a public ReviewCase, or None when no case should be surfaced.

    Rules (Data-ML + plan):
    - coverage.status=insufficient -> ReviewCase with band=None (detail insufficient_data).
    - score/band is None and coverage ready -> no ReviewCase. Existing workflow
      records remain in CaseStore and may be represented by internal consumers.
    - band set -> ensure CaseStore snapshot; never attach model_score / advisor_ref / PII.
    - When ``session`` is set and ``ml_term_snapshot`` exists, use that band/factors
      (no live M02 recompute).
    """
    calc_at = calculated_at or datetime.now(timezone.utc)
    features, band, factors, _score, model_limitations = _resolve_scored(
        record,
        session=session,
        thresholds=thresholds,
        calculated_at=calc_at,
    )
    # Prefer materialization clock when snapshot was used.
    calc_at = features.calculated_at
    coverage = features.coverage
    data_state = _data_state_for(coverage)
    model_version = features.model_version
    threshold_version = features.threshold_config_version
    dataset_version = features.dataset_version

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
            limitations=_limitations(coverage) + model_limitations,
            dataset_version=dataset_version,
            model_version=model_version,
            threshold_config_version=threshold_version,
            calculated_at=calc_at,
        )

    if band is None:
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
        review_priority_band=band,  # type: ignore[arg-type]
        contributing_factors=factors,
        coverage=coverage,
        data_state=data_state,  # type: ignore[arg-type]
        limitations=_limitations(coverage) + model_limitations,
        dataset_version=dataset_version,
        model_version=model_version,
        threshold_config_version=threshold_version,
        calculated_at=calc_at,
    )


def project_list_items(
    records: List[NormalizedStudentRecord],
    store: CaseStore,
    *,
    thresholds: ThresholdConfig = DEFAULT_THRESHOLDS,
    calculated_at: Optional[datetime] = None,
    session: Optional[Session] = None,
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
            session=session,
        )
        if case is not None and case.review_priority_band is not None:
            items.append(case)
    return items


def score_band_only(
    record: NormalizedStudentRecord,
    *,
    thresholds: ThresholdConfig = DEFAULT_THRESHOLDS,
    session: Optional[Session] = None,
) -> Tuple[Optional[float], Optional[str]]:
    """Internal helper for H04 impact aggregates — callers must not leak score."""
    if session is not None:
        row = get_ml_term_snapshot(session, record.source_id, record.student_ref)
        if row is not None:
            score = float(row.model_score) if row.model_score is not None else None
            # The stored score is authoritative; only remap the requested
            # threshold instead of reusing the materialized band.
            if score is None:
                return None, None
            if score >= thresholds.tau_high:
                return score, "uu_tien_som"
            if score >= thresholds.tau_case:
                return score, "can_ra_soat"
            return score, None

    scored = score_record(record, thresholds=thresholds)
    return scored.model_score, scored.review_priority_band
