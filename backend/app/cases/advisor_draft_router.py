"""H22 — GET /advisor-handoff-drafts (draft-only; no send endpoint)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.cases.advisor_draft import build_advisor_handoff_drafts
from app.cases.store import store
from app.contracts.advisor_handoff_draft import AdvisorHandoffDraftListResponse
from app.contracts.integration import IntegrationProblem
from app.database import get_db
from app.dwh.importer import SEMESTER_SOURCE_ID
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
    source_id: str = Query(default=SEMESTER_SOURCE_ID),
    db: Session = Depends(get_db),
) -> AdvisorHandoffDraftListResponse:
    """Public draft bundles grouped by H08 advisor_ref — no send, no case mutation."""
    try:
        records = list_normalized_students(db, source_id)
    except ReadAdapterError as err:
        return _error("upstream_unavailable", err.reason_codes)
    except Exception:
        return _error("upstream_unavailable")

    by_ref = {r.student_ref: r for r in records}
    return build_advisor_handoff_drafts(
        store,
        by_ref,
        thresholds=DEFAULT_THRESHOLDS,
        calculated_at=datetime.now(timezone.utc),
    )
