"""Rollup ``attendance_event`` → ``attendance_week`` (student × ISO Monday week).

Fail-closed on missing/unapproved provenance (same gate as H08 read adapter).
Idempotent: DELETE by ``source_id`` then insert within the caller's transaction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Iterable, Literal, Optional, Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.dwh.models import AttendanceEvent, AttendanceWeek
from app.dwh.read_adapter import ReadAdapterError, require_approved_manifest

DEFAULT_ATTENDANCE_SOURCE_ID = "mvp-attendance-over-time"

_RATE_QUANTUM = Decimal("0.0001")


@dataclass(frozen=True)
class WeekAgg:
    """Pure aggregation for one ``(student_ref, week_start_date)`` bucket."""

    student_ref: str
    week_start_date: date
    week_end_date: date
    n_events: int
    n_in_denominator: int
    n_present: int
    n_absent: int
    n_excused_excluded: int
    attendance_rate: Optional[Decimal]
    first_observed_at: Optional[datetime]
    last_observed_at: Optional[datetime]


@dataclass
class RollupResult:
    status: Literal["rolled_up", "rejected"]
    source_id: str
    reason_codes: list[str] = field(default_factory=list)
    row_counts: dict[str, int] = field(default_factory=dict)
    detail: Optional[str] = None


def iso_week_monday(observed: date | datetime) -> date:
    """Return the Monday (ISO week start) for an observation date/datetime."""
    d = observed.date() if isinstance(observed, datetime) else observed
    return d - timedelta(days=d.weekday())


def aggregate_week_bucket(
    student_ref: str,
    week_start: date,
    events: Sequence[AttendanceEvent],
) -> WeekAgg:
    """Count events for one student×Monday week; excused excluded from rate denom."""
    week_end = week_start + timedelta(days=6)
    n_events = len(events)
    n_excused = sum(1 for e in events if e.excused is True)
    counted = [
        e
        for e in events
        if e.excused is not True and e.presence_status is not None
    ]
    n_denom = len(counted)
    n_present = sum(1 for e in counted if e.presence_status == "present")
    n_absent = sum(1 for e in counted if e.presence_status == "absent")
    rate: Optional[Decimal] = None
    if n_denom > 0:
        rate = (Decimal(n_present) / Decimal(n_denom)).quantize(_RATE_QUANTUM)
    observed_ats = [e.observed_at for e in events if e.observed_at is not None]
    return WeekAgg(
        student_ref=student_ref,
        week_start_date=week_start,
        week_end_date=week_end,
        n_events=n_events,
        n_in_denominator=n_denom,
        n_present=n_present,
        n_absent=n_absent,
        n_excused_excluded=n_excused,
        attendance_rate=rate,
        first_observed_at=min(observed_ats) if observed_ats else None,
        last_observed_at=max(observed_ats) if observed_ats else None,
    )


def bucket_events_by_iso_week(
    events: Iterable[AttendanceEvent],
) -> list[WeekAgg]:
    """Group events by ``(student_ref, ISO Monday)`` and aggregate each bucket."""
    buckets: dict[tuple[str, date], list[AttendanceEvent]] = {}
    for event in events:
        key = (event.student_ref, iso_week_monday(event.observed_at))
        buckets.setdefault(key, []).append(event)
    return [
        aggregate_week_bucket(student_ref, week_start, group)
        for (student_ref, week_start), group in sorted(buckets.items())
    ]


def rollup_attendance_weeks(
    session: Session,
    source_id: str = DEFAULT_ATTENDANCE_SOURCE_ID,
) -> RollupResult:
    """Delete existing week rows for ``source_id``, then insert fresh rollup rows.

    Caller's transaction: this function does not commit. Fail-closed when the
    ``source_manifest`` is missing, unapproved, or not allowlisted.
    """
    try:
        require_approved_manifest(session, source_id)
    except ReadAdapterError as exc:
        return RollupResult(
            status="rejected",
            source_id=source_id,
            reason_codes=list(exc.reason_codes),
            row_counts={"attendance_week": 0},
            detail=exc.detail or "provenance gate rejected",
        )

    events = session.scalars(
        select(AttendanceEvent).where(AttendanceEvent.source_id == source_id)
    ).all()
    aggs = bucket_events_by_iso_week(events)

    session.execute(
        delete(AttendanceWeek).where(AttendanceWeek.source_id == source_id)
    )
    for agg in aggs:
        session.add(
            AttendanceWeek(
                source_id=source_id,
                student_ref=agg.student_ref,
                week_start_date=agg.week_start_date,
                week_end_date=agg.week_end_date,
                n_events=agg.n_events,
                n_in_denominator=agg.n_in_denominator,
                n_present=agg.n_present,
                n_absent=agg.n_absent,
                n_excused_excluded=agg.n_excused_excluded,
                attendance_rate=agg.attendance_rate,
                first_observed_at=agg.first_observed_at,
                last_observed_at=agg.last_observed_at,
            )
        )
    session.flush()

    return RollupResult(
        status="rolled_up",
        source_id=source_id,
        row_counts={"attendance_week": len(aggs)},
        detail=f"rolled up {len(events)} events into {len(aggs)} week rows",
    )
