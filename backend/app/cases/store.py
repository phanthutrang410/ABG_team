"""In-memory case store for H06b transition API (persistence / public DTO = later tasks)."""

from __future__ import annotations

from threading import Lock
from typing import Dict, Optional

from app.cases.domain import (
    CaseSnapshot,
    TransitionCommand,
    TransitionError,
    TransitionErrorCode,
    apply_transition,
    mark_mapping_repair,
    parse_action,
    parse_state,
)


class CaseStore:
    def __init__(self) -> None:
        self._cases: Dict[str, CaseSnapshot] = {}
        self._lock = Lock()

    def clear(self) -> None:
        with self._lock:
            self._cases.clear()

    def put(self, case: CaseSnapshot) -> CaseSnapshot:
        with self._lock:
            self._cases[case.case_id] = case
            return case

    def get(self, case_id: str) -> Optional[CaseSnapshot]:
        with self._lock:
            return self._cases.get(case_id)

    def create(
        self,
        case_id: str,
        *,
        state: str = "new_signal",
        advisor_ref: Optional[str] = None,
        student_ref: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> CaseSnapshot:
        if self.get(case_id) is not None:
            raise TransitionError(
                TransitionErrorCode.FORBIDDEN_TRANSITION,
                f"Case already exists: {case_id}",
            )
        snapshot = CaseSnapshot(
            case_id=case_id,
            state=parse_state(state),
            advisor_ref=advisor_ref,
            student_ref=student_ref,
            source_id=source_id,
        )
        return self.put(snapshot)

    def transition(self, case_id: str, command: TransitionCommand) -> CaseSnapshot:
        with self._lock:
            case = self._cases.get(case_id)
            if case is None:
                raise KeyError(case_id)
            try:
                updated = apply_transition(case, command)
            except TransitionError as err:
                if (
                    err.code == TransitionErrorCode.MISSING_ADVISOR_REF
                    and err.mapping_repair_queued
                ):
                    repaired = mark_mapping_repair(case)
                    self._cases[case_id] = repaired
                    err.case = repaired
                raise
            self._cases[case_id] = updated
            return updated


def command_from_strings(
    *,
    action: str,
    actor: str,
    actor_kind: str = "human",
    reason_code: Optional[str] = None,
    review_at=None,
    advisor_ref: Optional[str] = None,
    monitoring_until=None,
) -> TransitionCommand:
    return TransitionCommand(
        action=parse_action(action),
        actor=actor,
        actor_kind=actor_kind,
        reason_code=reason_code,
        review_at=review_at,
        advisor_ref=advisor_ref,
        monitoring_until=monitoring_until,
    )


store = CaseStore()
