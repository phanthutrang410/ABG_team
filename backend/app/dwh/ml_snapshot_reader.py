"""Read helpers for ``dwh.ml_term_snapshot`` and ``dwh.attendance_week``.

Public/agent consumers must use ``MlTermProjection`` (features + band + factors).
``model_score`` stays on the ORM row only — never copied onto the projection.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.coverage import Coverage
from app.contracts.review_case import ContributingFactor
from app.contracts.scoring import ScoringFeatures
from app.dwh.models import AttendanceWeek, MlTermSnapshot


@dataclass(frozen=True)
class MlTermProjection:
    """Public-safe materialization of one ``ml_term_snapshot`` row.

    Intentionally omits ``model_score`` so H02/H23 cannot leak raw score.
    """

    features: ScoringFeatures
    review_priority_band: Optional[str]
    contributing_factors: List[ContributingFactor]
    limitations: List[str]


def _float_opt(value: Optional[Decimal]) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def get_ml_term_snapshot(
    session: Session,
    source_id: str,
    student_ref: str,
) -> Optional[MlTermSnapshot]:
    """Load one ``ml_term_snapshot`` row by primary key, or ``None``.

    Returns ``None`` for missing rows and for non-ORM mocks (tests that pass
    a MagicMock session must fall back to live M02).
    """
    sid = (source_id or "").strip()
    ref = (student_ref or "").strip()
    if not sid or not ref:
        return None
    try:
        row = session.get(MlTermSnapshot, {"source_id": sid, "student_ref": ref})
    except Exception:  # noqa: BLE001 — mock / disconnected session → live path
        return None
    if row is None or not isinstance(row, MlTermSnapshot):
        return None
    return row


def projection_from_snapshot(row: MlTermSnapshot) -> MlTermProjection:
    """Convert a DB row to ScoringFeatures + band + factors — no M02 recompute.

    Never reads ``row.model_score`` into the returned projection.
    """
    coverage = Coverage.model_validate(json.loads(row.coverage_json))
    raw_factors = json.loads(row.contributing_factors_json or "[]")
    factors = [ContributingFactor.model_validate(item) for item in raw_factors]
    explain = json.loads(row.agent_explain_json or "{}")
    limitations = [str(item) for item in explain.get("limitations", [])]
    features = ScoringFeatures(
        dataset_version=row.dataset_version,
        model_version=row.model_version,
        threshold_config_version=row.threshold_config_version,
        calculated_at=row.calculated_at,
        student_ref=row.student_ref,
        latest_term_gpa=_float_opt(row.latest_term_gpa),
        grade_trend_slope=_float_opt(row.grade_trend_slope),
        grade_volatility=_float_opt(row.grade_volatility),
        failed_credits=_float_opt(row.failed_credits),
        attendance_rate_window=_float_opt(row.attendance_rate_window),
        attendance_trend_slope=_float_opt(row.attendance_trend_slope),
        coverage=coverage,
    )
    return MlTermProjection(
        features=features,
        review_priority_band=row.review_priority_band,
        contributing_factors=factors,
        limitations=limitations,
    )


def get_ml_term_projection(
    session: Session,
    source_id: str,
    student_ref: str,
) -> Optional[MlTermProjection]:
    """Load and project a snapshot when present; ``None`` → caller falls back to live M02."""
    row = get_ml_term_snapshot(session, source_id, student_ref)
    if row is None:
        return None
    try:
        return projection_from_snapshot(row)
    except Exception:  # noqa: BLE001 — corrupt JSON / schema → live M02
        return None


def list_attendance_weeks(
    session: Session,
    source_id: str,
    student_ref: str,
) -> List[AttendanceWeek]:
    """List ISO-week attendance rollups for one student (G07 / weekly UI consumer).

    Ordered by ``week_start_date`` ascending. Empty list when none exist.
    No public FastAPI route yet — call from backend services.
    """
    sid = (source_id or "").strip()
    ref = (student_ref or "").strip()
    if not sid or not ref:
        return []
    rows: Sequence[AttendanceWeek] = session.scalars(
        select(AttendanceWeek)
        .where(
            AttendanceWeek.source_id == sid,
            AttendanceWeek.student_ref == ref,
        )
        .order_by(AttendanceWeek.week_start_date.asc())
    ).all()
    return list(rows)
