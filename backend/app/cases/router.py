"""HTTP surface for Process §4 transitions (narrow; not public ReviewCase).

H39b: actor/role/scope from session Principal; client actor ignored.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.principal import Principal, require_active_role
from app.auth.rbac import action_permitted, audit, principal_can_view_care_case
from app.cases.auth import seed_create_allowed
from app.cases.domain import AGENT_ACTOR_KINDS, CaseAction, TransitionError, TransitionErrorCode
from app.cases.routing import resolve_advisor_for_assign
from app.cases.schemas import (
    CaseCreateRequest,
    TransitionErrorBody,
    TransitionRequest,
    TransitionResponse,
)
from app.cases.store import command_from_strings, store
from app.database import get_db

router = APIRouter(prefix="/cases", tags=["cases"])

_KNOWN_ACTIONS = frozenset(a.value for a in CaseAction)


def _to_public_response(case) -> TransitionResponse:
    """Public projection — never includes advisor_ref / student_ref / source_id."""
    return TransitionResponse(
        case_id=case.case_id,
        state=case.state.value,
        review_at=case.review_at,
        reason_code=case.reason_code,
        monitoring_until=case.monitoring_until,
        mapping_repair_queued=case.mapping_repair_queued,
        updated_at=case.updated_at,
    )


def _http_status(code: TransitionErrorCode) -> int:
    if code in {
        TransitionErrorCode.FORBIDDEN_ALIAS,
        TransitionErrorCode.UNKNOWN_ACTION,
        TransitionErrorCode.UNKNOWN_STATE,
        TransitionErrorCode.MISSING_REASON,
        TransitionErrorCode.MISSING_REVIEW_AT,
        TransitionErrorCode.MISSING_MONITORING_UNTIL,
        TransitionErrorCode.MISSING_ACTOR,
    }:
        return 422
    if code == TransitionErrorCode.MISSING_ADVISOR_REF:
        return status.HTTP_409_CONFLICT
    if code in {
        TransitionErrorCode.AGENT_FORBIDDEN,
        TransitionErrorCode.UNTRUSTED_ACTOR,
        TransitionErrorCode.CREATE_DISABLED,
    }:
        return status.HTTP_403_FORBIDDEN
    return status.HTTP_409_CONFLICT


@router.post("", response_model=TransitionResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    body: CaseCreateRequest,
    principal: Principal = Depends(require_active_role),
) -> TransitionResponse:
    """Seed a minimal case — disabled outside local/dev/test (deploy-blocker)."""
    if not seed_create_allowed():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=TransitionErrorBody(
                detail="POST /cases is seed-only; disabled outside local/dev/test",
                code=TransitionErrorCode.CREATE_DISABLED.value,
                case_id=body.case_id,
                state=body.state,
                mapping_repair_queued=False,
            ).model_dump(),
        )
    if principal.active_role != "ban_quan_ly":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "role_not_permitted", "message": "role not permitted"},
        )
    try:
        case = store.create(
            body.case_id,
            state=body.state,
            advisor_ref=None,
            student_ref=body.student_ref,
            source_id=body.source_id,
        )
    except TransitionError as err:
        raise HTTPException(
            status_code=_http_status(err.code),
            detail=TransitionErrorBody(
                detail=err.message,
                code=err.code.value,
                case_id=body.case_id,
                state=body.state,
                mapping_repair_queued=False,
            ).model_dump(),
        ) from err
    return _to_public_response(case)


@router.get("/{case_id}", response_model=TransitionResponse)
def get_case(
    case_id: str,
    principal: Principal = Depends(require_active_role),
) -> TransitionResponse:
    case = store.get(case_id)
    if case is None or not principal_can_view_care_case(
        principal,
        case_advisor_ref=case.advisor_ref,
        case_state=case.state.value,
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")
    return _to_public_response(case)


@router.post("/{case_id}/transitions", response_model=TransitionResponse)
def transition_case(
    case_id: str,
    body: TransitionRequest,
    principal: Principal = Depends(require_active_role),
    db: Session = Depends(get_db),
) -> TransitionResponse:
    case = store.get(case_id)
    if case is None or not principal_can_view_care_case(
        principal,
        case_advisor_ref=case.advisor_ref,
        case_state=case.state.value,
    ):
        audit(
            principal,
            action=f"case.transition:{body.action}",
            resource_handle=case_id,
            allowed=False,
            db=db,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")

    if body.action in _KNOWN_ACTIONS and not action_permitted(principal, body.action):
        audit(
            principal,
            action=f"case.transition:{body.action}",
            resource_handle=case_id,
            allowed=False,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "role_not_permitted", "message": "action not permitted for role"},
        )

    if body.actor_kind is not None and body.actor_kind.strip():
        kind = body.actor_kind.strip().lower()
        if kind in AGENT_ACTOR_KINDS:
            audit(
                principal,
                action=f"case.transition:{body.action}",
                resource_handle=case_id,
                allowed=False,
                db=db,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=TransitionErrorBody(
                    detail="Agent/LLM must not change case state",
                    code=TransitionErrorCode.AGENT_FORBIDDEN.value,
                    case_id=case_id,
                    state=case.state.value,
                    mapping_repair_queued=case.mapping_repair_queued,
                ).model_dump(),
            )

    try:
        actor = principal.actor_id
        actor_kind = "human"
        resolved_advisor = None
        if body.action == "assign":
            resolved_advisor = resolve_advisor_for_assign(db, case)
        command = command_from_strings(
            action=body.action,
            actor=actor,
            actor_kind=actor_kind,
            reason_code=body.reason_code,
            review_at=body.review_at,
            advisor_ref=resolved_advisor,
            monitoring_until=body.monitoring_until,
        )
        updated = store.transition(case_id, command)
    except TransitionError as err:
        audit(
            principal,
            action=f"case.transition:{body.action}",
            resource_handle=case_id,
            allowed=False,
            db=db,
        )
        snapshot = err.case or store.get(case_id) or case
        raise HTTPException(
            status_code=_http_status(err.code),
            detail=TransitionErrorBody(
                detail=err.message,
                code=err.code.value,
                case_id=case_id,
                state=snapshot.state.value,
                mapping_repair_queued=err.mapping_repair_queued
                or snapshot.mapping_repair_queued,
            ).model_dump(),
        ) from err

    audit(
        principal,
        action=f"case.transition:{body.action}",
        resource_handle=case_id,
        allowed=True,
        db=db,
    )
    return _to_public_response(updated)
