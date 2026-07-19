"""Pure Process §4 case state machine (no ReviewCase public envelope)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from typing import Optional


class CaseState(str, Enum):
    """API codes from Process §4.1 — display names are not stored."""

    NEW_SIGNAL = "new_signal"
    PENDING_REVIEW = "pending_review"
    APPROVED_FOR_FOLLOW_UP = "approved_for_follow_up"
    DISMISSED = "dismissed"
    ASSIGNED = "assigned"
    FOLLOW_UP_IN_PROGRESS = "follow_up_in_progress"
    RESOLVED = "resolved"
    MONITORING = "monitoring"


class CaseAction(str, Enum):
    """Actions from Process §4.2–4.3."""

    QUEUE_FOR_REVIEW = "queue_for_review"
    APPROVE = "approve"
    DISMISS = "dismiss"
    DEFER = "defer"
    ASSIGN = "assign"
    ACCEPT = "accept"
    RESOLVE = "resolve"
    MONITOR = "monitor"


# Process §4.1 / §4.5 — never accepted as state or action codes.
FORBIDDEN_STATE_ALIASES = frozenset(
    {
        "new",
        "in_review",
        "deferred",
        "handed_off",
        "low_risk",
        "medium_risk",
        "high_risk",
        "Low Risk",
        "Medium Risk",
        "High Risk",
        "Deferred",
        "Handed Off",
    }
)

AGENT_ACTOR_KINDS = frozenset({"agent", "llm"})

TERMINAL_STATES = frozenset({CaseState.DISMISSED, CaseState.RESOLVED})


class TransitionErrorCode(str, Enum):
    FORBIDDEN_ALIAS = "forbidden_alias"
    UNKNOWN_ACTION = "unknown_action"
    UNKNOWN_STATE = "unknown_state"
    AGENT_FORBIDDEN = "agent_forbidden"
    FORBIDDEN_TRANSITION = "forbidden_transition"
    MISSING_REASON = "missing_reason"
    MISSING_REVIEW_AT = "missing_review_at"
    MISSING_ADVISOR_REF = "missing_advisor_ref"
    MISSING_MONITORING_UNTIL = "missing_monitoring_until"
    MISSING_ACTOR = "missing_actor"
    UNTRUSTED_ACTOR = "untrusted_actor"
    TERMINAL_STATE = "terminal_state"
    CREATE_DISABLED = "create_disabled"


class TransitionError(Exception):
    """Rejected transition — maps to HTTP 4xx in the API layer."""

    def __init__(
        self,
        code: TransitionErrorCode,
        message: str,
        *,
        mapping_repair_queued: bool = False,
        case: Optional[CaseSnapshot] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.mapping_repair_queued = mapping_repair_queued
        self.case = case


@dataclass(frozen=True)
class CaseSnapshot:
    """Minimal internal case record for transitions (not public ReviewCase)."""

    case_id: str
    state: CaseState
    advisor_ref: Optional[str] = None
    student_ref: Optional[str] = None
    source_id: Optional[str] = None
    review_at: Optional[datetime] = None
    reason_code: Optional[str] = None
    monitoring_until: Optional[datetime] = None
    mapping_repair_queued: bool = False
    updated_at: Optional[datetime] = None
    # First time the assigned GVCN opened the secured detail ("đã xem"). Set once,
    # separate from acceptance (which is the assigned → follow_up_in_progress transition).
    viewed_at: Optional[datetime] = None


@dataclass(frozen=True)
class TransitionCommand:
    action: CaseAction
    actor: str
    actor_kind: str = "human"
    reason_code: Optional[str] = None
    review_at: Optional[datetime] = None
    advisor_ref: Optional[str] = None
    monitoring_until: Optional[datetime] = None
    timestamp: Optional[datetime] = None


# (from_state, action) → to_state
_ALLOWED: dict[tuple[CaseState, CaseAction], CaseState] = {
    (CaseState.NEW_SIGNAL, CaseAction.QUEUE_FOR_REVIEW): CaseState.PENDING_REVIEW,
    (CaseState.PENDING_REVIEW, CaseAction.APPROVE): CaseState.APPROVED_FOR_FOLLOW_UP,
    (CaseState.PENDING_REVIEW, CaseAction.DISMISS): CaseState.DISMISSED,
    (CaseState.PENDING_REVIEW, CaseAction.DEFER): CaseState.PENDING_REVIEW,
    (CaseState.APPROVED_FOR_FOLLOW_UP, CaseAction.ASSIGN): CaseState.ASSIGNED,
    (CaseState.ASSIGNED, CaseAction.ACCEPT): CaseState.FOLLOW_UP_IN_PROGRESS,
    (CaseState.FOLLOW_UP_IN_PROGRESS, CaseAction.RESOLVE): CaseState.RESOLVED,
    (CaseState.FOLLOW_UP_IN_PROGRESS, CaseAction.MONITOR): CaseState.MONITORING,
    (CaseState.MONITORING, CaseAction.RESOLVE): CaseState.RESOLVED,
}


def parse_state(value: str) -> CaseState:
    if value in FORBIDDEN_STATE_ALIASES:
        raise TransitionError(
            TransitionErrorCode.FORBIDDEN_ALIAS,
            f"Forbidden state alias: {value!r}",
        )
    try:
        return CaseState(value)
    except ValueError as exc:
        raise TransitionError(
            TransitionErrorCode.UNKNOWN_STATE,
            f"Unknown case state: {value!r}",
        ) from exc


def parse_action(value: str) -> CaseAction:
    if value in FORBIDDEN_STATE_ALIASES:
        raise TransitionError(
            TransitionErrorCode.FORBIDDEN_ALIAS,
            f"Forbidden action/state alias: {value!r}",
        )
    try:
        return CaseAction(value)
    except ValueError as exc:
        raise TransitionError(
            TransitionErrorCode.UNKNOWN_ACTION,
            f"Unknown case action: {value!r}",
        ) from exc


def apply_transition(case: CaseSnapshot, command: TransitionCommand) -> CaseSnapshot:
    """Apply a Process §4 transition or raise TransitionError."""
    if not command.actor or not command.actor.strip():
        raise TransitionError(
            TransitionErrorCode.MISSING_ACTOR,
            "actor is required for every transition",
        )

    kind = (command.actor_kind or "human").strip().lower()
    if kind in AGENT_ACTOR_KINDS:
        raise TransitionError(
            TransitionErrorCode.AGENT_FORBIDDEN,
            "Agent/LLM must not change case state (Process §4.3 / Ethics §8)",
        )

    if case.state in TERMINAL_STATES:
        raise TransitionError(
            TransitionErrorCode.TERMINAL_STATE,
            f"Case is terminal ({case.state.value}); open a new case on significant change",
        )

    target = _ALLOWED.get((case.state, command.action))
    if target is None:
        raise TransitionError(
            TransitionErrorCode.FORBIDDEN_TRANSITION,
            f"Action {command.action.value!r} is not allowed from {case.state.value!r}",
        )

    ts = command.timestamp or datetime.utcnow()
    next_case = replace(case, state=target, updated_at=ts)

    if command.action == CaseAction.DISMISS:
        if not command.reason_code or not command.reason_code.strip():
            raise TransitionError(
                TransitionErrorCode.MISSING_REASON,
                "dismiss requires a standardized reason_code",
            )
        return replace(next_case, reason_code=command.reason_code.strip())

    if command.action == CaseAction.DEFER:
        if command.review_at is None:
            raise TransitionError(
                TransitionErrorCode.MISSING_REVIEW_AT,
                "defer requires review_at; state stays pending_review",
            )
        # Explicitly keep Pending Review (no Deferred state).
        return replace(
            next_case,
            state=CaseState.PENDING_REVIEW,
            review_at=command.review_at,
        )

    if command.action == CaseAction.ASSIGN:
        # Advisor must be supplied on the command (H03: router resolves via H08).
        advisor = (command.advisor_ref or "").strip()
        if not advisor:
            # Care gate §4.4: stop handoff, queue mapping-repair, keep approved.
            raise TransitionError(
                TransitionErrorCode.MISSING_ADVISOR_REF,
                "assign requires advisor_ref; handoff stopped — mapping-repair queued",
                mapping_repair_queued=True,
            )
        return replace(
            next_case,
            advisor_ref=advisor,
            mapping_repair_queued=False,
        )

    if command.action == CaseAction.MONITOR:
        if command.monitoring_until is None:
            raise TransitionError(
                TransitionErrorCode.MISSING_MONITORING_UNTIL,
                "monitor requires monitoring_until",
            )
        return replace(next_case, monitoring_until=command.monitoring_until)

    if command.action == CaseAction.APPROVE:
        # Approve is not handoff — do not clear or invent advisor_ref.
        return next_case

    return next_case


def mark_mapping_repair(case: CaseSnapshot) -> CaseSnapshot:
    """Keep Approved for Follow-up and flag mapping-repair queue (§4.4)."""
    return replace(
        case,
        state=CaseState.APPROVED_FOR_FOLLOW_UP,
        mapping_repair_queued=True,
    )
