"""H22 — GET /advisor-handoff-drafts (draft-only; H39b: ban_quan_ly only)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.principal import Principal, require_roles
from app.auth.rbac import audit, server_source_id
from app.cases.advisor_draft import build_advisor_handoff_drafts
from app.cases.store import store
from app.contracts.advisor_handoff_draft import AdvisorHandoffDraftListResponse
from app.contracts.integration import IntegrationProblem
from app.database import get_db
from app.dwh.read_adapter import ReadAdapterError, list_normalized_students
from app.ml.scoring import DEFAULT_THRESHOLDS

router = APIRouter(prefix="/advisor-handoff-drafts", tags=["advisor-handoff-drafts"])


def _error(code: str = "upstream_unavailable", reason_codes: Optional[list] = None) -> AdvisorHandoffDraftListResponse:
    return AdvisorHandoffDraftListResponse(
        state="error",
        bundles=[],
        problem=IntegrationProblem(
            code=code,  # type: ignore[arg-type]
            reason_codes=list(reason_codes or []),
        ),
    )


@router.get("", response_model=AdvisorHandoffDraftListResponse)
def list_advisor_handoff_drafts(
    principal: Principal = Depends(require_roles("ban_quan_ly")),
    db: Session = Depends(get_db),
) -> AdvisorHandoffDraftListResponse:
    """Draft bundles grouped by H08 advisor_ref — no send, no case mutation."""
    source_id = server_source_id()
    try:
        records = list_normalized_students(db, source_id)
    except ReadAdapterError as err:
        audit(
            principal,
            action="advisor_drafts.list",
            resource_handle="advisor-handoff-drafts",
            allowed=False,
            db=db,
        )
        return _error("upstream_unavailable", err.reason_codes)
    except Exception:
        audit(
            principal,
            action="advisor_drafts.list",
            resource_handle="advisor-handoff-drafts",
            allowed=False,
            db=db,
        )
        return _error("upstream_unavailable")

    by_ref = {r.student_ref: r for r in records}
    audit(
        principal,
        action="advisor_drafts.list",
        resource_handle="advisor-handoff-drafts",
        allowed=True,
        db=db,
    )
    return build_advisor_handoff_drafts(
        store,
        by_ref,
        thresholds=DEFAULT_THRESHOLDS,
        calculated_at=datetime.now(timezone.utc),
        session=db,
    )
