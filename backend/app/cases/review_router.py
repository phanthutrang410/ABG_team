"""H02 — public ReviewCase list/detail HTTP (H11a envelopes) + H39b RBAC.

Does not change GET /cases/{id} TransitionResponse shape.
Browser must not choose ``source_id`` / org / advisor scope — server derives them.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.principal import Principal, require_active_role
from app.auth.rbac import audit, principal_can_view_care_case, server_source_id
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
from app.contracts.review_case import ReviewCase
from app.database import get_db
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


def _filter_visible(principal: Principal, items: List[ReviewCase]) -> List[ReviewCase]:
    visible: List[ReviewCase] = []
    for item in items:
        snap = store.get(item.case_id)
        advisor_ref = snap.advisor_ref if snap else None
        if principal_can_view_care_case(
            principal,
            case_advisor_ref=advisor_ref,
            case_state=item.case_state,
        ):
            visible.append(item)
    return visible


@router.get("", response_model=CaseListResponse)
def list_review_cases(
    principal: Principal = Depends(require_active_role),
    db: Session = Depends(get_db),
) -> CaseListResponse:
    """Scoped list envelope — CaseListResponse (ok|empty|stale|error)."""
    source_id = server_source_id()
    try:
        records = list_normalized_students(db, source_id)
    except ReadAdapterError as err:
        audit(
            principal,
            action="review_cases.list",
            resource_handle="review-cases",
            allowed=False,
            db=db,
        )
        return _list_error("upstream_unavailable", err.reason_codes)
    except Exception:
        audit(
            principal,
            action="review_cases.list",
            resource_handle="review-cases",
            allowed=False,
            db=db,
        )
        return _list_error("upstream_unavailable")

    calculated_at = datetime.now(timezone.utc)
    items = project_list_items(
        records,
        store,
        thresholds=DEFAULT_THRESHOLDS,
        calculated_at=calculated_at,
        session=db,
    )
    items = _filter_visible(principal, items)
    audit(
        principal,
        action="review_cases.list",
        resource_handle="review-cases",
        allowed=True,
        db=db,
    )

    stale = is_snapshot_stale(calculated_at)
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
    principal: Principal = Depends(require_active_role),
    db: Session = Depends(get_db),
) -> CaseDetailResponse:
    """Scoped detail envelope — out-of-scope looks like not-found/empty."""
    source_id = server_source_id()
    student_ref = student_ref_from_case_id(case_id)
    if student_ref is None:
        audit(
            principal,
            action="review_cases.detail",
            resource_handle=case_id,
            allowed=False,
            db=db,
        )
        return CaseDetailResponse(
            case=None,
            state="empty",
            freshness="fresh",
            problem=IntegrationProblem(code="not_found", reason_codes=["invalid_case_id"]),
        )

    try:
        record = get_normalized_student(db, source_id, student_ref)
    except ReadAdapterError as err:
        audit(
            principal,
            action="review_cases.detail",
            resource_handle=case_id,
            allowed=False,
            db=db,
        )
        return _detail_error("upstream_unavailable", err.reason_codes)
    except Exception:
        audit(
            principal,
            action="review_cases.detail",
            resource_handle=case_id,
            allowed=False,
            db=db,
        )
        return _detail_error("upstream_unavailable")

    if record is None:
        audit(
            principal,
            action="review_cases.detail",
            resource_handle=case_id,
            allowed=False,
            db=db,
        )
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
            session=db,
        )
        snap = store.get(case_id)
        if case is None or not principal_can_view_care_case(
            principal,
            case_advisor_ref=snap.advisor_ref if snap else None,
            case_state=case.case_state,
        ):
            audit(
                principal,
                action="review_cases.detail",
                resource_handle=case_id,
                allowed=False,
                db=db,
            )
            return CaseDetailResponse(
                case=None,
                state="empty",
                freshness="fresh",
                problem=IntegrationProblem(code="not_found", reason_codes=["not_found"]),
            )
        audit(
            principal,
            action="review_cases.detail",
            resource_handle=case_id,
            allowed=True,
            db=db,
        )
        freshness = "stale" if is_snapshot_stale(case.calculated_at) else "fresh"
        if freshness == "stale":
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
        session=db,
    )
    snap = store.get(case_id)
    if (
        case is None
        or case.review_priority_band is None
        or not principal_can_view_care_case(
            principal,
            case_advisor_ref=snap.advisor_ref if snap else None,
            case_state=case.case_state,
        )
    ):
        audit(
            principal,
            action="review_cases.detail",
            resource_handle=case_id,
            allowed=False,
            db=db,
        )
        # Same envelope as missing — do not leak existence outside scope.
        return CaseDetailResponse(
            case=None,
            state="empty",
            freshness="fresh",
            problem=IntegrationProblem(code="not_found", reason_codes=["not_found"]),
        )

    audit(
        principal,
        action="review_cases.detail",
        resource_handle=case_id,
        allowed=True,
        db=db,
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
