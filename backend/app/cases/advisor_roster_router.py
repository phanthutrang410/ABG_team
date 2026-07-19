"""GET /advisor/roster — server-scoped class roster for GVCN / ban_quan_ly."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.principal import Principal, require_active_role
from app.auth.rbac import audit
from app.cases.advisor_roster import build_advisor_roster
from app.cases.store import store
from app.contracts.advisor_roster import AdvisorRosterResponse
from app.database import get_db

router = APIRouter(prefix="/advisor", tags=["advisor-roster"])


@router.get("/roster", response_model=AdvisorRosterResponse)
def get_advisor_roster(
    principal: Principal = Depends(require_active_role),
    db: Session = Depends(get_db),
) -> AdvisorRosterResponse:
    audit(
        principal,
        action="advisor.roster.list",
        resource_handle="advisor/roster",
        allowed=True,
        db=db,
    )
    return build_advisor_roster(db, principal, store)
