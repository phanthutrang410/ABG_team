"""H39 — shared RBAC helpers for care / review / config routes."""

from __future__ import annotations

from typing import FrozenSet, Optional

from fastapi import HTTPException

from app.auth.principal import Principal, record_access_event
from app.auth.scope import can_access_case, gvcn_may_see_case_state
from app.dwh.importer import SEMESTER_SOURCE_ID

#: MVP care/review cases belong to the demo org (seed accounts use the same).
DEFAULT_CASE_ORG_SCOPE = "org-demo"

BAN_QUAN_LY_ACTIONS: FrozenSet[str] = frozenset(
    {
        "queue_for_review",
        "approve",
        "dismiss",
        "defer",
        "assign",
    }
)
GVCN_ACTIONS: FrozenSet[str] = frozenset(
    {
        "accept",
        "monitor",
        "resolve",
    }
)


def server_source_id() -> str:
    """Allowlisted semester source — never accept browser ``source_id``."""
    return SEMESTER_SOURCE_ID


def assert_active_role(principal: Principal) -> str:
    if not principal.active_role:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "active_role_required",
                "message": "select an active role before continuing",
            },
        )
    return principal.active_role


def action_permitted(principal: Principal, action: str) -> bool:
    role = principal.active_role
    if role == "ban_quan_ly":
        return action in BAN_QUAN_LY_ACTIONS
    if role == "gvcn":
        return action in GVCN_ACTIONS
    return False


def principal_can_view_care_case(
    principal: Principal,
    *,
    case_advisor_ref: Optional[str],
    case_state: Optional[str],
    case_org: str = DEFAULT_CASE_ORG_SCOPE,
    student_class_scope: Optional[str] = None,
) -> bool:
    """Care/review visibility for the current principal.

    ``student_class_scope`` is the class-roster overlay scope for the case's
    student (``app.cases.class_scope``). When it matches a ``gvcn`` principal's
    ``advisor_scope`` the case is visible in ANY state — the lecturer owns the
    whole class roster. Callers that do not resolve the overlay (e.g. the
    ``/cases`` workflow API) pass ``None`` and keep the legacy handoff semantics:
    a ``gvcn`` then only sees cases assigned to them in a post-handoff state.
    """
    # Roster overlay path: a lecturer sees every case for a student in their own
    # class, regardless of case state or whether a case has been assigned yet.
    if (
        principal.active_role == "gvcn"
        and student_class_scope
        and principal.org_scope == case_org
        and principal.advisor_scope
        and principal.advisor_scope == student_class_scope
    ):
        return True
    if not can_access_case(principal, case_advisor_ref, case_org):
        return False
    if principal.active_role == "gvcn":
        return gvcn_may_see_case_state(case_state)
    return True


def audit(
    principal: Principal,
    *,
    action: str,
    resource_handle: str,
    allowed: bool,
    db=None,
) -> None:
    record_access_event(
        actor_id=principal.actor_id,
        role=principal.active_role or "",
        action=action,
        resource_handle=resource_handle,
        decision="allowed" if allowed else "denied",
        db=db,
    )
