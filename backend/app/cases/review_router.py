"""H02 — public ReviewCase list/detail HTTP (H11a envelopes) + H39b RBAC.

Does not change GET /cases/{id} TransitionResponse shape.
Browser must not choose ``source_id`` / org / advisor scope — server derives them.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.principal import Principal, require_active_role, require_roles
from app.auth.rbac import (
    DEFAULT_CASE_ORG_SCOPE,
    audit,
    principal_can_view_care_case,
    server_source_id,
)
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
from app.contracts.review_overview import ReviewOverviewSummary
from app.contracts.review_case import ReviewCase
from app.database import get_db
from app.dwh.read_adapter import ReadAdapterError, get_normalized_student, list_normalized_students
from app.dwh.models import SourceManifest
from app.ml.scoring import DEFAULT_THRESHOLDS

router = APIRouter(prefix="/review-cases", tags=["review-cases"])


def _list_error(
    code: str = "upstream_unavailable", reason_codes: Optional[list] = None
) -> CaseListResponse:
    return CaseListResponse(
        items=[],
        state="error",
        problem=IntegrationProblem(
            code=code,  # type: ignore[arg-type]
            reason_codes=list(reason_codes or []),
        ),
    )


def _detail_error(
    code: str = "upstream_unavailable", reason_codes: Optional[list] = None
) -> CaseDetailResponse:
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


def _source_extracted_at(db: Session, source_id: str) -> Optional[datetime]:
    manifest = db.get(SourceManifest, source_id)
    return manifest.extracted_at if manifest is not None else None


def _summary_error(
    source_id: str,
    generated_at: datetime,
    *,
    reason_codes: Optional[list[str]] = None,
) -> ReviewOverviewSummary:
    return ReviewOverviewSummary(
        state="error",
        source_id=source_id,
        generated_at=generated_at,
        total_students=0,
        review_case_count=0,
        review_student_count=0,
        limited_student_count=0,
        limited_review_case_count=0,
        problem=IntegrationProblem(
            code="upstream_unavailable",
            reason_codes=list(reason_codes or []),
        ),
    )


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


@router.get("/summary", response_model=ReviewOverviewSummary)
def get_review_overview_summary(
    principal: Principal = Depends(require_roles("ban_quan_ly")),
    db: Session = Depends(get_db),
) -> ReviewOverviewSummary:
    """Organization snapshot denominator separated from the scoped review queue.

    ``case_state=new_signal`` is reported only as a workflow-state count.  It is
    never projected as a temporal "new since last snapshot" metric; that field
    remains null until a real weekly delta is joined by a future contract.
    """
    source_id = server_source_id()
    generated_at = datetime.now(timezone.utc)

    if principal.org_scope != DEFAULT_CASE_ORG_SCOPE:
        audit(
            principal,
            action="review_cases.summary",
            resource_handle="review-cases/summary",
            allowed=False,
            db=db,
        )
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "summary not found in scope"},
        )

    try:
        records = list_normalized_students(db, source_id)
        source_extracted_at = _source_extracted_at(db, source_id)
    except ReadAdapterError as err:
        audit(
            principal,
            action="review_cases.summary",
            resource_handle="review-cases/summary",
            allowed=False,
            db=db,
        )
        return _summary_error(source_id, generated_at, reason_codes=err.reason_codes)
    except Exception:
        audit(
            principal,
            action="review_cases.summary",
            resource_handle="review-cases/summary",
            allowed=False,
            db=db,
        )
        return _summary_error(source_id, generated_at)

    if source_extracted_at is None:
        audit(
            principal,
            action="review_cases.summary",
            resource_handle="review-cases/summary",
            allowed=False,
            db=db,
        )
        return _summary_error(
            source_id,
            generated_at,
            reason_codes=["source_manifest_missing"],
        )

    dataset_versions = {record.dataset_version for record in records}
    if len(dataset_versions) > 1:
        audit(
            principal,
            action="review_cases.summary",
            resource_handle="review-cases/summary",
            allowed=False,
            db=db,
        )
        return _summary_error(
            source_id,
            generated_at,
            reason_codes=["mixed_dataset_version"],
        )

    items = project_list_items(
        records,
        store,
        thresholds=DEFAULT_THRESHOLDS,
        calculated_at=generated_at,
        session=db,
    )
    items = _filter_visible(principal, items)

    coverage_counts = Counter(record.coverage.status for record in records)
    priority_counts = Counter(item.review_priority_band for item in items)
    case_state_counts = Counter(item.case_state for item in items)
    review_data_counts = Counter(item.data_state for item in items)

    source_is_stale = is_snapshot_stale(source_extracted_at)
    projection_is_stale = any(is_snapshot_stale(item.calculated_at) for item in items)
    stale = source_is_stale or projection_is_stale

    audit(
        principal,
        action="review_cases.summary",
        resource_handle="review-cases/summary",
        allowed=True,
        db=db,
    )

    state = "empty" if not records else "stale" if stale else "ok"
    problem = (
        IntegrationProblem(code="stale_snapshot", reason_codes=["stale_snapshot"])
        if stale
        else None
    )
    return ReviewOverviewSummary(
        state=state,
        source_id=source_id,
        dataset_version=next(iter(dataset_versions), None),
        source_extracted_at=source_extracted_at,
        generated_at=generated_at,
        total_students=len(records),
        review_case_count=len(items),
        review_student_count=len({item.student_ref for item in items}),
        limited_student_count=sum(1 for record in records if record.coverage.status != "ok"),
        limited_review_case_count=sum(1 for item in items if item.data_state != "ok"),
        priority_band_counts={
            "uu_tien_som": priority_counts["uu_tien_som"],
            "can_ra_soat": priority_counts["can_ra_soat"],
        },
        case_state_counts={
            state_code: case_state_counts[state_code]
            for state_code in (
                "new_signal",
                "pending_review",
                "approved_for_follow_up",
                "dismissed",
                "assigned",
                "follow_up_in_progress",
                "resolved",
                "monitoring",
            )
        },
        student_coverage_counts={
            "ok": coverage_counts["ok"],
            "partial": coverage_counts["partial"],
            "insufficient": coverage_counts["insufficient"],
        },
        review_data_state_counts={
            "ok": review_data_counts["ok"],
            "partial": review_data_counts["partial"],
            "insufficient_data": review_data_counts["insufficient_data"],
        },
        comparison_status="unavailable",
        new_since_previous_snapshot=None,
        problem=problem,
    )


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
