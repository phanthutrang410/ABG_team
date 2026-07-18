"""H02 — public ReviewCase list/detail HTTP (H11a envelopes).

Does not change GET /cases/{id} TransitionResponse shape.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.cases.review_projection import (
    is_snapshot_stale,
    project_list_items,
    project_review_case,
    student_ref_from_case_id,
)
from app.cases.store import store
from app.contracts.integration import (
    CaseDetailResponse,
    CaseListResponse,
    IntegrationProblem,
)
from app.database import get_db
from app.dwh.importer import SEMESTER_SOURCE_ID
from app.dwh.read_adapter import ReadAdapterError, get_normalized_student, list_normalized_students
from app.ml.scoring import DEFAULT_THRESHOLDS

router = APIRouter(prefix="/review-cases", tags=["review-cases"])


def _list_error(code: str = "upstream_unavailable", reason_codes: Optional[list] = None) -> CaseListResponse:
    return CaseListResponse(
        items=[],
        state="error",
        problem=IntegrationProblem(
            code=code,  # type: ignore[arg-type]
            reason_codes=list(reason_codes or []),
        ),
    )


def _detail_error(code: str = "upstream_unavailable", reason_codes: Optional[list] = None) -> CaseDetailResponse:
    return CaseDetailResponse(
        case=None,
        state="error",
        freshness="fresh",
        problem=IntegrationProblem(
            code=code,  # type: ignore[arg-type]
            reason_codes=list(reason_codes or []),
        ),
    )


@router.get("", response_model=CaseListResponse)
def list_review_cases(
    source_id: str = Query(default=SEMESTER_SOURCE_ID),
    db: Session = Depends(get_db),
) -> CaseListResponse:
    """Public list envelope — CaseListResponse (ok|empty|stale|error)."""
    try:
        records = list_normalized_students(db, source_id)
    except ReadAdapterError as err:
        return _list_error("upstream_unavailable", err.reason_codes)
    except Exception:
        return _list_error("upstream_unavailable")

    calculated_at = datetime.now(timezone.utc)
    items = project_list_items(
        records,
        store,
        thresholds=DEFAULT_THRESHOLDS,
        calculated_at=calculated_at,
    )
    stale = is_snapshot_stale(calculated_at)
    # Allow tests to force stale via calculated_at injection on items
    if items and any(is_snapshot_stale(i.calculated_at) for i in items):
        stale = True

    if stale:
        return CaseListResponse(
            items=items,
            state="stale",
            problem=IntegrationProblem(
                code="stale_snapshot",
                reason_codes=["stale_snapshot"],
            ),
        )
    if not items:
        return CaseListResponse(
            items=[],
            state="empty",
            problem=IntegrationProblem(code="empty", reason_codes=[]),
        )
    return CaseListResponse(items=items, state="ok", problem=None)


@router.get("/{case_id}", response_model=CaseDetailResponse)
def get_review_case(
    case_id: str,
    source_id: str = Query(default=SEMESTER_SOURCE_ID),
    db: Session = Depends(get_db),
) -> CaseDetailResponse:
    """Public detail envelope — CaseDetailResponse states per H11a."""
    student_ref = student_ref_from_case_id(case_id)
    if student_ref is None:
        return CaseDetailResponse(
            case=None,
            state="empty",
            freshness="fresh",
            problem=IntegrationProblem(code="not_found", reason_codes=["invalid_case_id"]),
        )

    try:
        record = get_normalized_student(db, source_id, student_ref)
    except ReadAdapterError as err:
        return _detail_error("upstream_unavailable", err.reason_codes)
    except Exception:
        return _detail_error("upstream_unavailable")

    if record is None:
        return CaseDetailResponse(
            case=None,
            state="empty",
            freshness="fresh",
            problem=IntegrationProblem(code="not_found", reason_codes=["student_not_found"]),
        )

    calculated_at = datetime.now(timezone.utc)
    if record.coverage.status == "insufficient":
        case = project_review_case(
            record,
            store,
            thresholds=DEFAULT_THRESHOLDS,
            calculated_at=calculated_at,
        )
        freshness = "stale" if (case and is_snapshot_stale(case.calculated_at)) else "fresh"
        if freshness == "stale" and case is not None:
            return CaseDetailResponse(
                case=case,
                state="stale",
                freshness="stale",
                problem=IntegrationProblem(
                    code="stale_snapshot",
                    reason_codes=["stale_snapshot"],
                ),
            )
        return CaseDetailResponse(
            case=case,
            state="insufficient_data",
            freshness="fresh",
            problem=IntegrationProblem(
                code="insufficient_data",
                reason_codes=list(record.coverage.reason_codes),
            ),
        )

    case = project_review_case(
        record,
        store,
        thresholds=DEFAULT_THRESHOLDS,
        calculated_at=calculated_at,
        include_below_threshold=False,
    )
    if case is None or case.review_priority_band is None:
        return CaseDetailResponse(
            case=None,
            state="empty",
            freshness="fresh",
            problem=IntegrationProblem(code="empty", reason_codes=["below_threshold"]),
        )

    if is_snapshot_stale(case.calculated_at):
        return CaseDetailResponse(
            case=case,
            state="stale",
            freshness="stale",
            problem=IntegrationProblem(
                code="stale_snapshot",
                reason_codes=["stale_snapshot"],
            ),
        )
    return CaseDetailResponse(case=case, state="ok", freshness="fresh", problem=None)
