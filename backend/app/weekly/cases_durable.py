"""H33a — durable weekly case/event persistence (MVP in-memory repository).

Per the task brief, a full Alembic-backed store is heavier than this wave
needs; this module keeps the same guarantees the real table would (opaque
episode id, append-only event history, one active episode per
`(student_ref, branch)`, GET never creates/mutates) behind a small
thread-safe in-memory repository so H33b/H34a/H34b can build on a stable
contract now. Swapping the storage engine later does not have to change
this module's public surface.

State vocabulary here is the weekly-episode model (Decision #23 §7):
`pending_review -> approved -> assigned -> monitoring/resolved`, or
`pending_review -> dismissed`. It intentionally does not reuse
`app.cases.domain` 1:1 — that module drives the existing `/cases` transition
API on a different (legacy RAM) case shape; this module is the durable
episode ledger the H33b delta/reconcile engine reads and writes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Dict, List, Optional, Tuple

#: Never accepted as a state/action here either (Process §4.1/§4.5 lock).
FORBIDDEN_ALIASES = frozenset(
    {
        "new",
        "in_review",
        "deferred",
        "handed_off",
        "low_risk",
        "medium_risk",
        "high_risk",
    }
)

#: Agent/LLM must never drive a case transition (Ethics §8 / Process §4.3).
AGENT_ACTOR_KINDS = frozenset({"agent", "llm"})

EPISODE_STATES = frozenset(
    {"pending_review", "approved", "assigned", "monitoring", "dismissed", "resolved"}
)
TERMINAL_STATES = frozenset({"dismissed", "resolved"})

# (state, action) -> next_state
_ALLOWED: Dict[Tuple[str, str], str] = {
    ("pending_review", "approve"): "approved",
    ("pending_review", "dismiss"): "dismissed",
    ("approved", "assign"): "assigned",
    ("assigned", "monitor"): "monitoring",
    ("assigned", "resolve"): "resolved",
    ("monitoring", "resolve"): "resolved",
}


class DurableCaseError(Exception):
    """Rejected create/transition — caller maps this to an API error."""

    def __init__(self, code: str, message: str, *, mapping_repair_queued: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.mapping_repair_queued = mapping_repair_queued


@dataclass
class CaseEvent:
    """Append-only history entry — never mutated after creation."""

    kind: str
    actor: str
    actor_kind: str = "human"
    detail: dict = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CaseEpisode:
    """Durable weekly case episode (H33a) — opaque id, not `rc-{student_ref}`."""

    episode_id: str
    student_ref: str
    branch: str
    state: str = "pending_review"
    advisor_ref: Optional[str] = None
    org_scope: Optional[str] = None
    active: bool = True
    mapping_repair_queued: bool = False
    events: List[CaseEvent] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def _new_episode_id() -> str:
    return f"ep-{uuid.uuid4().hex[:20]}"


def _check_actor(actor: str, actor_kind: str) -> None:
    if not actor or not actor.strip():
        raise DurableCaseError("missing_actor", "actor is required")
    if (actor_kind or "human").strip().lower() in AGENT_ACTOR_KINDS:
        raise DurableCaseError(
            "agent_forbidden", "Agent/LLM must not change case state (Ethics §8)"
        )


class CaseRepository:
    """In-memory durable episode/event store — thread-safe for MVP tests."""

    def __init__(self) -> None:
        self._episodes: Dict[str, CaseEpisode] = {}
        self._applied_effect_keys: set = set()
        self._lock = Lock()

    def clear(self) -> None:
        with self._lock:
            self._episodes.clear()
            self._applied_effect_keys.clear()

    # --- GET helpers: read-only, never create/mutate --------------------

    def get(self, episode_id: str) -> Optional[CaseEpisode]:
        with self._lock:
            return self._episodes.get(episode_id)

    def list_active(
        self, *, branch: Optional[str] = None, org_scope: Optional[str] = None
    ) -> List[CaseEpisode]:
        with self._lock:
            items = [e for e in self._episodes.values() if e.active]
        if branch is not None:
            items = [e for e in items if e.branch == branch]
        if org_scope is not None:
            items = [e for e in items if e.org_scope == org_scope]
        return items

    def get_active_for(self, student_ref: str, branch: str) -> Optional[CaseEpisode]:
        with self._lock:
            for episode in self._episodes.values():
                if (
                    episode.active
                    and episode.student_ref == student_ref
                    and episode.branch == branch
                ):
                    return episode
        return None

    def list_all(self) -> List[CaseEpisode]:
        with self._lock:
            return list(self._episodes.values())

    # --- Writes -----------------------------------------------------------

    def create_episode(
        self,
        student_ref: str,
        branch: str,
        *,
        org_scope: Optional[str] = None,
        actor: str = "system:weekly-workflow",
        actor_kind: str = "system",
        detail: Optional[dict] = None,
    ) -> CaseEpisode:
        """Open a new pending-review episode; refuses a second active one."""
        if not student_ref or not student_ref.strip():
            raise DurableCaseError("missing_student_ref", "student_ref is required")
        if branch not in ("semester", "attendance"):
            raise DurableCaseError("unknown_branch", f"unknown branch: {branch!r}")

        with self._lock:
            for episode in self._episodes.values():
                if (
                    episode.active
                    and episode.student_ref == student_ref
                    and episode.branch == branch
                ):
                    raise DurableCaseError(
                        "active_episode_exists",
                        f"one active episode already open for {student_ref}/{branch}",
                    )
            episode = CaseEpisode(
                episode_id=_new_episode_id(),
                student_ref=student_ref,
                branch=branch,
                org_scope=org_scope,
            )
            episode.events.append(
                CaseEvent(kind="episode_created", actor=actor, actor_kind=actor_kind, detail=detail or {})
            )
            self._episodes[episode.episode_id] = episode
            return episode

    def append_event(
        self,
        episode_id: str,
        kind: str,
        *,
        actor: str = "system:weekly-workflow",
        actor_kind: str = "system",
        detail: Optional[dict] = None,
    ) -> CaseEpisode:
        """Append-only history entry — never changes `state`."""
        with self._lock:
            episode = self._episodes.get(episode_id)
            if episode is None:
                raise DurableCaseError("episode_not_found", f"no episode {episode_id}")
            episode.events.append(
                CaseEvent(kind=kind, actor=actor, actor_kind=actor_kind, detail=detail or {})
            )
            episode.updated_at = datetime.now(timezone.utc)
            return episode

    def has_applied_effect(self, effect_key: str) -> bool:
        with self._lock:
            return effect_key in self._applied_effect_keys

    def mark_effect_applied(self, effect_key: str) -> bool:
        """Returns True the first time `effect_key` is seen; False on repeat."""
        with self._lock:
            if effect_key in self._applied_effect_keys:
                return False
            self._applied_effect_keys.add(effect_key)
            return True

    def transition(
        self,
        episode_id: str,
        action: str,
        *,
        actor: str,
        actor_kind: str = "human",
        reason_code: Optional[str] = None,
        advisor_ref: Optional[str] = None,
        monitoring_until: Optional[datetime] = None,
    ) -> CaseEpisode:
        """Authorized human transition only — Process-style guardrails."""
        if action in FORBIDDEN_ALIASES:
            raise DurableCaseError("forbidden_alias", f"forbidden action alias: {action!r}")
        _check_actor(actor, actor_kind)

        with self._lock:
            episode = self._episodes.get(episode_id)
            if episode is None:
                raise DurableCaseError("episode_not_found", f"no episode {episode_id}")
            if episode.state in TERMINAL_STATES:
                raise DurableCaseError(
                    "terminal_state",
                    f"episode {episode_id} is terminal ({episode.state}); "
                    "open a new episode on significant change",
                )
            target = _ALLOWED.get((episode.state, action))
            if target is None:
                raise DurableCaseError(
                    "forbidden_transition",
                    f"action {action!r} not allowed from {episode.state!r}",
                )

            if action == "dismiss" and not (reason_code or "").strip():
                raise DurableCaseError("missing_reason", "dismiss requires reason_code")
            if action == "assign":
                advisor = (advisor_ref or "").strip()
                if not advisor:
                    episode.mapping_repair_queued = True
                    episode.events.append(
                        CaseEvent(
                            kind="mapping_repair_queued",
                            actor=actor,
                            actor_kind=actor_kind,
                        )
                    )
                    raise DurableCaseError(
                        "missing_advisor_ref",
                        "assign requires advisor_ref; mapping-repair queued",
                        mapping_repair_queued=True,
                    )
                episode.advisor_ref = advisor
                episode.mapping_repair_queued = False
            if action == "monitor" and monitoring_until is None:
                raise DurableCaseError("missing_monitoring_until", "monitor requires monitoring_until")

            episode.state = target
            episode.updated_at = datetime.now(timezone.utc)
            if target in TERMINAL_STATES:
                episode.active = False
            detail: dict = {"action": action}
            if reason_code:
                detail["reason_code"] = reason_code
            if monitoring_until is not None:
                detail["monitoring_until"] = monitoring_until.isoformat()
            episode.events.append(
                CaseEvent(kind=f"transition:{action}", actor=actor, actor_kind=actor_kind, detail=detail)
            )
            return episode
