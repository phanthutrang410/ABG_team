"""H23 — server-derived AgentContextResponse (client cannot forge context).

Reuses H02 projection (`project_review_case` / freshness) and H03 routing
(`resolve_advisor_for_assign`) for internal advisor mapping checks. Never
exposes `advisor_ref` on the public/agent envelope.

Fail-closed branches (H24 must enforce model.calls == 0 when any apply):

1. Invalid case_id / student not in trusted source scope → empty
2. Upstream / read adapter / unexpected query error → unavailable
3. Below-threshold / no public band → empty
4. Coverage insufficient or missing band/factors → insufficient_data
5. Snapshot stale → insufficient_data + stale_snapshot
6. Intent not in filtered ``allowed_intents`` (incl. neutral_draft before
   approval / without valid internal advisor mapping) → refuse at H24 gate
7. Invalid AgentCommand (intent/locale/question) → reject before context/provider
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.cases.review_projection import (
    is_snapshot_stale,
    project_review_case,
    student_ref_from_case_id,
)
from app.cases.routing import resolve_advisor_for_assign
from app.cases.store import CaseStore, store as default_store
from app.contracts.integration import (
    AgentContextResponse,
    AgentIntent,
    IntegrationProblem,
)
from app.contracts.review_case import ReviewCase
from app.dwh.read_adapter import ReadAdapterError, get_normalized_student
from app.ml.scoring import DEFAULT_THRESHOLDS, ThresholdConfig

#: Process active states that may receive explain_case when context is ready.
_EXPLAIN_CASE_STATES = frozenset(
    {
        "new_signal",
        "pending_review",
        "approved_for_follow_up",
        "assigned",
        "follow_up_in_progress",
        "monitoring",
    }
)

#: Care-gate states for neutral_draft (plus valid internal advisor mapping).
_NEUTRAL_DRAFT_STATES = frozenset({"approved_for_follow_up", "assigned"})


@dataclass(frozen=True)
class TrustedScope:
    """Server-derived identity scope — never accept from the browser."""

    source_id: str


def provider_call_allowed(context: AgentContextResponse, intent: AgentIntent) -> bool:
    """True only when H24 may invoke the model (status ready + intent allowed)."""
    return context.status == "ready" and intent in context.allowed_intents


def _has_valid_internal_advisor(
    session: Session,
    case_id: str,
    case_store: CaseStore,
) -> bool:
    """Internal mapping check via H03 routing — result never includes advisor_ref."""
    snapshot = case_store.get(case_id)
    if snapshot is None:
        return False
    return resolve_advisor_for_assign(session, snapshot) is not None


def _filter_allowed_intents(
    case: ReviewCase,
    *,
    session: Session,
    case_store: CaseStore,
) -> List[AgentIntent]:
    allowed: List[AgentIntent] = []
    if case.case_state in _EXPLAIN_CASE_STATES:
        allowed.append("explain_case")
    if case.case_state in _NEUTRAL_DRAFT_STATES and _has_valid_internal_advisor(
        session, case.case_id, case_store
    ):
        allowed.append("neutral_draft")
    return allowed


def _ready_enough(case: ReviewCase) -> bool:
    """Fresh path needs a public band and at least one contributing factor."""
    return case.review_priority_band is not None and bool(case.contributing_factors)


def build_agent_context(
    case_id: str,
    trusted_scope: TrustedScope,
    *,
    session: Session,
    case_store: Optional[CaseStore] = None,
    thresholds: ThresholdConfig = DEFAULT_THRESHOLDS,
    now: Optional[datetime] = None,
) -> AgentContextResponse:
    """Load ReviewCase once via H02 projection and map to AgentContextResponse."""
    case_store = case_store or default_store
    clock = now or datetime.now(timezone.utc)
    source_id = (trusted_scope.source_id or "").strip()
    if not source_id:
        return AgentContextResponse(
            status="unavailable",
            case=None,
            problem=IntegrationProblem(
                code="upstream_unavailable",
                reason_codes=["missing_trusted_scope"],
            ),
            allowed_intents=[],
        )

    student_ref = student_ref_from_case_id(case_id)
    if student_ref is None:
        return AgentContextResponse(
            status="empty",
            case=None,
            problem=IntegrationProblem(
                code="not_found",
                reason_codes=["invalid_case_id"],
            ),
            allowed_intents=[],
        )

    try:
        record = get_normalized_student(session, source_id, student_ref)
    except ReadAdapterError as err:
        return AgentContextResponse(
            status="unavailable",
            case=None,
            problem=IntegrationProblem(
                code="upstream_unavailable",
                reason_codes=list(err.reason_codes),
            ),
            allowed_intents=[],
        )
    except Exception:
        return AgentContextResponse(
            status="unavailable",
            case=None,
            problem=IntegrationProblem(
                code="upstream_unavailable",
                reason_codes=["query_failed"],
            ),
            allowed_intents=[],
        )

    if record is None:
        return AgentContextResponse(
            status="empty",
            case=None,
            problem=IntegrationProblem(
                code="not_found",
                reason_codes=["student_not_found"],
            ),
            allowed_intents=[],
        )

    case = project_review_case(
        record,
        case_store,
        thresholds=thresholds,
        calculated_at=clock,
        include_below_threshold=False,
    )

    if case is not None and is_snapshot_stale(case.calculated_at, now=clock):
        return AgentContextResponse(
            status="insufficient_data",
            case=case,
            problem=IntegrationProblem(
                code="stale_snapshot",
                reason_codes=["stale_snapshot"],
            ),
            allowed_intents=[],
        )

    if record.coverage.status == "insufficient":
        # Projection still yields a ReviewCase with band=None.
        if case is None:
            return AgentContextResponse(
                status="insufficient_data",
                case=None,
                problem=IntegrationProblem(
                    code="insufficient_data",
                    reason_codes=list(record.coverage.reason_codes),
                ),
                allowed_intents=[],
            )
        return AgentContextResponse(
            status="insufficient_data",
            case=case,
            problem=IntegrationProblem(
                code="insufficient_data",
                reason_codes=list(record.coverage.reason_codes),
            ),
            allowed_intents=[],
        )

    if case is None or case.review_priority_band is None:
        return AgentContextResponse(
            status="empty",
            case=None,
            problem=IntegrationProblem(
                code="empty",
                reason_codes=["below_threshold"],
            ),
            allowed_intents=[],
        )

    if not _ready_enough(case):
        return AgentContextResponse(
            status="insufficient_data",
            case=case,
            problem=IntegrationProblem(
                code="insufficient_data",
                reason_codes=["missing_band_or_factors"],
            ),
            allowed_intents=[],
        )

    return AgentContextResponse(
        status="ready",
        case=case,
        problem=None,
        allowed_intents=_filter_allowed_intents(
            case, session=session, case_store=case_store
        ),
    )
