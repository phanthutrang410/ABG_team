"""Care CaseStore — in-memory (tests) + Postgres durable (app schema)."""

from __future__ import annotations

import json
import os
from datetime import datetime
from threading import Lock
from typing import Dict, Optional, Protocol, runtime_checkable

from sqlalchemy import delete, inspect, select
from sqlalchemy.orm import Session, sessionmaker

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
from app.cases.models import CareCaseEvent, CareReviewCase


@runtime_checkable
class CaseStorePort(Protocol):
    def clear(self) -> None: ...

    def put(self, case: CaseSnapshot) -> CaseSnapshot: ...

    def get(self, case_id: str) -> Optional[CaseSnapshot]: ...

    def list_snapshots(self) -> list[CaseSnapshot]: ...

    def create(
        self,
        case_id: str,
        *,
        state: str = "new_signal",
        advisor_ref: Optional[str] = None,
        student_ref: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> CaseSnapshot: ...

    def transition(self, case_id: str, command: TransitionCommand) -> CaseSnapshot: ...


class InMemoryCaseStore:
    """Process §4 care ledger kept in RAM (unit-test default)."""

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

    def list_snapshots(self) -> list[CaseSnapshot]:
        """Return a shallow copy of all snapshots (H22 aggregation)."""
        with self._lock:
            return list(self._cases.values())

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


# Backward-compatible name used by fixtures (`CaseStore()`).
CaseStore = InMemoryCaseStore


def _snapshot_from_row(row: CareReviewCase) -> CaseSnapshot:
    return CaseSnapshot(
        case_id=row.case_id,
        state=parse_state(row.state),
        advisor_ref=row.advisor_ref,
        student_ref=row.student_ref,
        source_id=row.source_id,
        review_at=row.review_at,
        reason_code=row.reason_code,
        monitoring_until=row.monitoring_until,
        mapping_repair_queued=bool(row.mapping_repair_queued),
        updated_at=row.updated_at,
    )


def _apply_snapshot_to_row(row: CareReviewCase, case: CaseSnapshot) -> None:
    row.state = case.state.value
    row.advisor_ref = case.advisor_ref
    row.student_ref = case.student_ref
    row.source_id = case.source_id
    row.review_at = case.review_at
    row.reason_code = case.reason_code
    row.monitoring_until = case.monitoring_until
    row.mapping_repair_queued = case.mapping_repair_queued
    row.updated_at = case.updated_at or datetime.utcnow()


def _detail_json(case: CaseSnapshot, **extra: object) -> str:
    payload: dict[str, object] = {
        "reason_code": case.reason_code,
        "review_at": case.review_at.isoformat() if case.review_at else None,
        "advisor_ref": case.advisor_ref,
        "monitoring_until": (
            case.monitoring_until.isoformat() if case.monitoring_until else None
        ),
        "mapping_repair_queued": case.mapping_repair_queued,
    }
    payload.update(extra)
    return json.dumps(payload, default=str)


class PostgresCaseStore:
    """Durable CaseStore backed by ``app.review_case`` + append-only ``app.case_event``."""

    def __init__(self, session_factory: Optional[sessionmaker[Session]] = None) -> None:
        self._session_factory = session_factory

    def _factory(self) -> sessionmaker[Session]:
        if self._session_factory is not None:
            return self._session_factory
        from app.database import get_session_factory

        return get_session_factory()

    def clear(self) -> None:
        session = self._factory()()
        try:
            session.execute(delete(CareCaseEvent))
            session.execute(delete(CareReviewCase))
            session.commit()
        finally:
            session.close()

    def put(self, case: CaseSnapshot) -> CaseSnapshot:
        session = self._factory()()
        try:
            row = session.get(CareReviewCase, case.case_id)
            if row is None:
                now = case.updated_at or datetime.utcnow()
                row = CareReviewCase(
                    case_id=case.case_id,
                    state=case.state.value,
                    student_ref=case.student_ref,
                    source_id=case.source_id,
                    advisor_ref=case.advisor_ref,
                    review_at=case.review_at,
                    reason_code=case.reason_code,
                    monitoring_until=case.monitoring_until,
                    mapping_repair_queued=case.mapping_repair_queued,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
            else:
                _apply_snapshot_to_row(row, case)
            session.commit()
            session.refresh(row)
            return _snapshot_from_row(row)
        finally:
            session.close()

    def get(self, case_id: str) -> Optional[CaseSnapshot]:
        session = self._factory()()
        try:
            row = session.get(CareReviewCase, case_id)
            if row is None:
                return None
            return _snapshot_from_row(row)
        finally:
            session.close()

    def list_snapshots(self) -> list[CaseSnapshot]:
        session = self._factory()()
        try:
            rows = session.scalars(select(CareReviewCase)).all()
            return [_snapshot_from_row(row) for row in rows]
        finally:
            session.close()

    def create(
        self,
        case_id: str,
        *,
        state: str = "new_signal",
        advisor_ref: Optional[str] = None,
        student_ref: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> CaseSnapshot:
        session = self._factory()()
        try:
            if session.get(CareReviewCase, case_id) is not None:
                raise TransitionError(
                    TransitionErrorCode.FORBIDDEN_TRANSITION,
                    f"Case already exists: {case_id}",
                )
            parsed = parse_state(state)
            now = datetime.utcnow()
            row = CareReviewCase(
                case_id=case_id,
                state=parsed.value,
                advisor_ref=advisor_ref,
                student_ref=student_ref,
                source_id=source_id,
                mapping_repair_queued=False,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.flush()
            snapshot = _snapshot_from_row(row)
            session.add(
                CareCaseEvent(
                    case_id=case_id,
                    kind="created",
                    actor="system",
                    actor_kind="system",
                    action=None,
                    from_state=None,
                    to_state=parsed.value,
                    detail_json=_detail_json(snapshot),
                    occurred_at=now,
                )
            )
            session.commit()
            session.refresh(row)
            return _snapshot_from_row(row)
        except TransitionError:
            session.rollback()
            raise
        finally:
            session.close()

    def transition(self, case_id: str, command: TransitionCommand) -> CaseSnapshot:
        session = self._factory()()
        try:
            row = session.get(CareReviewCase, case_id, with_for_update=True)
            if row is None:
                raise KeyError(case_id)
            case = _snapshot_from_row(row)
            try:
                updated = apply_transition(case, command)
            except TransitionError as err:
                if (
                    err.code == TransitionErrorCode.MISSING_ADVISOR_REF
                    and err.mapping_repair_queued
                ):
                    repaired = mark_mapping_repair(case)
                    _apply_snapshot_to_row(row, repaired)
                    session.add(
                        CareCaseEvent(
                            case_id=case_id,
                            kind="mapping_repair",
                            actor=command.actor,
                            actor_kind=command.actor_kind or "human",
                            action=command.action.value,
                            from_state=case.state.value,
                            to_state=repaired.state.value,
                            detail_json=_detail_json(repaired),
                            occurred_at=datetime.utcnow(),
                        )
                    )
                    session.commit()
                    session.refresh(row)
                    err.case = _snapshot_from_row(row)
                else:
                    session.rollback()
                raise
            _apply_snapshot_to_row(row, updated)
            session.add(
                CareCaseEvent(
                    case_id=case_id,
                    kind=f"transition:{command.action.value}",
                    actor=command.actor,
                    actor_kind=command.actor_kind or "human",
                    action=command.action.value,
                    from_state=case.state.value,
                    to_state=updated.state.value,
                    detail_json=_detail_json(updated),
                    occurred_at=updated.updated_at or datetime.utcnow(),
                )
            )
            session.commit()
            session.refresh(row)
            return _snapshot_from_row(row)
        except (KeyError, TransitionError):
            raise
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


_memory_store = InMemoryCaseStore()
_postgres_store: Optional[PostgresCaseStore] = None
_prefer_postgres = False


def care_tables_ready(engine=None) -> bool:
    """True when ``app.review_case`` exists (migration applied)."""
    try:
        if engine is None:
            from app.database import get_engine

            engine = get_engine()
        return "review_case" in inspect(engine).get_table_names(schema="app")
    except Exception:
        return False


def try_enable_postgres_case_store(
    session_factory: Optional[sessionmaker[Session]] = None,
) -> bool:
    """Enable Postgres backing after successful schema/migration readiness.

    Skipped when ``CASES_STORE_BACKEND=memory`` (unit tests stay in-memory).
    """
    global _postgres_store, _prefer_postgres
    backend = os.environ.get("CASES_STORE_BACKEND", "").strip().lower()
    if backend == "memory":
        _prefer_postgres = False
        return False
    if backend and backend != "postgres":
        _prefer_postgres = False
        return False
    try:
        from app.database import get_engine

        engine = get_engine()
        if not care_tables_ready(engine):
            _prefer_postgres = False
            return False
        _postgres_store = PostgresCaseStore(session_factory=session_factory)
        _prefer_postgres = True
        return True
    except Exception:
        _prefer_postgres = False
        return False


def reset_case_store_backend_for_tests() -> None:
    """Force in-memory backend (pytest fixtures)."""
    global _postgres_store, _prefer_postgres
    _prefer_postgres = False
    _postgres_store = None
    _memory_store.clear()


def get_case_store() -> CaseStorePort:
    """Return Postgres store when enabled and tables ready; else in-memory."""
    backend = os.environ.get("CASES_STORE_BACKEND", "").strip().lower()
    if backend == "memory":
        return _memory_store
    if _prefer_postgres and _postgres_store is not None:
        return _postgres_store
    return _memory_store


class _DelegatingCaseStore:
    """Module ``store`` proxy — delegates to :func:`get_case_store`."""

    def clear(self) -> None:
        get_case_store().clear()

    def put(self, case: CaseSnapshot) -> CaseSnapshot:
        return get_case_store().put(case)

    def get(self, case_id: str) -> Optional[CaseSnapshot]:
        return get_case_store().get(case_id)

    def list_snapshots(self) -> list[CaseSnapshot]:
        return get_case_store().list_snapshots()

    def create(
        self,
        case_id: str,
        *,
        state: str = "new_signal",
        advisor_ref: Optional[str] = None,
        student_ref: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> CaseSnapshot:
        return get_case_store().create(
            case_id,
            state=state,
            advisor_ref=advisor_ref,
            student_ref=student_ref,
            source_id=source_id,
        )

    def transition(self, case_id: str, command: TransitionCommand) -> CaseSnapshot:
        return get_case_store().transition(case_id, command)


store = _DelegatingCaseStore()


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
