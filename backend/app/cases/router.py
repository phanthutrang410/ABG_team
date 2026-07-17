"""HTTP surface for Process §4 transitions (narrow; not public ReviewCase)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.cases.domain import TransitionError, TransitionErrorCode
from app.cases.schemas import (
    CaseCreateRequest,
    TransitionErrorBody,
    TransitionRequest,
    TransitionResponse,
)
from app.cases.store import command_from_strings, store

router = APIRouter(prefix="/cases", tags=["cases"])


def _to_response(case) -> TransitionResponse:
    return TransitionResponse(
        case_id=case.case_id,
        state=case.state.value,
        advisor_ref=case.advisor_ref,
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
    if code == TransitionErrorCode.AGENT_FORBIDDEN:
        return status.HTTP_403_FORBIDDEN
    return status.HTTP_409_CONFLICT


@router.post("", response_model=TransitionResponse, status_code=status.HTTP_201_CREATED)
def create_case(body: CaseCreateRequest) -> TransitionResponse:
    """Seed a minimal case for the transition state machine (H06b)."""
    try:
        case = store.create(body.case_id, state=body.state, advisor_ref=body.advisor_ref)
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
    return _to_response(case)


@router.get("/{case_id}", response_model=TransitionResponse)
def get_case(case_id: str) -> TransitionResponse:
    case = store.get(case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")
    return _to_response(case)


@router.post("/{case_id}/transitions", response_model=TransitionResponse)
def transition_case(case_id: str, body: TransitionRequest) -> TransitionResponse:
    case = store.get(case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")
    try:
        command = command_from_strings(
            action=body.action,
            actor=body.actor,
            actor_kind=body.actor_kind,
            reason_code=body.reason_code,
            review_at=body.review_at,
            advisor_ref=body.advisor_ref,
            monitoring_until=body.monitoring_until,
        )
        updated = store.transition(case_id, command)
    except TransitionError as err:
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
    return _to_response(updated)
