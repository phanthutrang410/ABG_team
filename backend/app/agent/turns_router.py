"""H37 — POST /agent/turns (strict capability registry; max one tool decision).

Only the trusted server-resolved ``Principal`` (H36) and a provider-neutral
``TextModel`` chosen strictly for tool-choice (never raw case/report data)
enter :func:`run_turn`. When no OpenAI key is configured — or the provider
call fails — ``model`` is ``None``/unusable and the turn still returns
deterministic action cards (zero live calls either way in default tests).

``POST /agent/turns/stream`` adds SSE status + faux-token deltas after
output_guard, then a final ``done`` event with the same ``AgentTurnResponse``.
"""

from __future__ import annotations

import logging
from typing import Dict, Iterator, List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agent.model import TextModel
from app.agent.openai_client import OpenAIResponsesClient
from app.agent.sse import chunk_text, format_sse
from app.agent.turns import (
    AgentTurnRequest,
    AgentTurnResponse,
    TurnStatus,
    _scan_forbidden,
    resolve_safe_context,
    run_turn,
)
from app.auth.principal import Principal, require_active_role
from app.cases.review_router import build_review_overview_summary
from app.config import Settings, get_settings
from app.contracts.review_overview import ReviewOverviewSummary
from app.database import get_db

router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)

_UNAVAILABLE_VI = (
    "Máy chủ tạm thời không phản hồi. Chưa có câu trả lời từ trợ lý — vui lòng thử lại sau."
)


def get_turn_model(settings: Settings = Depends(get_settings)) -> Optional[TextModel]:
    """DI factory: OpenAI client only when a key is configured; else ``None``.

    ``None`` means "no live provider call" — ``run_turn`` still returns
    deterministic action cards from the briefing-style capability catalog.
    """
    key = settings.openai_api_key
    secret = key.get_secret_value() if hasattr(key, "get_secret_value") else str(key or "")
    if not str(secret or "").strip():
        return None
    return OpenAIResponsesClient.from_settings(settings)


def _overview_facts_from_summary(summary: ReviewOverviewSummary) -> Dict[str, object]:
    """Project the trusted aggregate into the minimal Overview Agent context."""
    problem_codes = list(summary.problem.reason_codes) if summary.problem is not None else []
    if summary.state == "error":
        # Error envelopes carry structural zeroes; do not phrase those as real counts.
        total_students: Optional[int] = None
        review_case_count: Optional[int] = None
    else:
        total_students = summary.total_students
        review_case_count = summary.review_case_count
    return {
        "summary_state": summary.state,
        "total_students": total_students,
        "review_case_count": review_case_count,
        "comparison_status": summary.comparison_status,
        "limitations": problem_codes,
        # Static server-owned evidence handle; never echo a client resource_handle.
        "evidence_ref": "review_overview:organization",
    }


def resolve_overview_facts(
    body: AgentTurnRequest,
    principal: Principal,
    db: Session,
) -> Optional[Dict[str, object]]:
    """Load organization facts only for an authorized management Overview turn."""
    if (
        body.surface != "overview"
        or principal.active_role != "ban_quan_ly"
        or _scan_forbidden(body.question) is not None
        or _scan_forbidden(body.resource_handle) is not None
        or resolve_safe_context(body.surface, role=principal.active_role) is None
    ):
        return None
    try:
        summary = build_review_overview_summary(principal, db)
    except Exception:  # noqa: BLE001 — integration boundary logs and returns an explicit error state
        # Keep both HTTP and SSE contracts controlled if the aggregate loader
        # fails unexpectedly. Counts remain absent, so no structural zero is
        # phrased as a real observation and the failure is still visible in logs.
        logger.exception("overview summary resolution failed for Agent turn")
        return {
            "summary_state": "error",
            "total_students": None,
            "review_case_count": None,
            "comparison_status": "unavailable",
            "limitations": ["overview_summary_unavailable"],
            "evidence_ref": "review_overview:organization",
        }
    return _overview_facts_from_summary(summary)


@router.post(
    "/turns",
    response_model=AgentTurnResponse,
    summary="Global Agent turn — strict capability registry, max one tool decision",
)
def create_agent_turn(
    body: AgentTurnRequest,
    principal: Principal = Depends(require_active_role),
    model: Optional[TextModel] = Depends(get_turn_model),
    db: Session = Depends(get_db),
) -> AgentTurnResponse:
    overview_facts = resolve_overview_facts(body, principal, db)
    return run_turn(body, principal, model=model, overview_facts=overview_facts, db=db)


def _stream_turn_events(
    response: AgentTurnResponse,
    phases: List[str],
) -> Iterator[str]:
    """Yield buffered SSE frames for an already guarded Agent response."""

    for phase in phases:
        yield format_sse("status", {"phase": phase})

    # Faux tokens only for successful answers (refused: skip deltas, still done).
    if response.status is TurnStatus.OK:
        for piece in chunk_text(response.answer_vi):
            yield format_sse("delta", {"text": piece})

    yield format_sse("done", response.model_dump(mode="json"))


@router.post(
    "/turns/stream",
    summary="Global Agent turn (SSE) — status phases, faux answer deltas, then done",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Buffered SSE: status*, optional delta*, then one done or error",
            "content": {
                "text/event-stream": {
                    "schema": {
                        "type": "string",
                        "description": "SSE frames using status, delta, done, and error events",
                    }
                }
            },
        }
    },
)
def create_agent_turn_stream(
    body: AgentTurnRequest,
    principal: Principal = Depends(require_active_role),
    model: Optional[TextModel] = Depends(get_turn_model),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    # Run the guarded turn (including durable audit) before returning the
    # iterator. This is deliberately buffered/faux streaming, so the
    # request-scoped Session is never used after dependency cleanup.
    phases: List[str] = []
    try:
        overview_facts = resolve_overview_facts(body, principal, db)
        response = run_turn(
            body,
            principal,
            model=model,
            overview_facts=overview_facts,
            on_phase=phases.append,
            db=db,
        )
        events: Iterator[str] = _stream_turn_events(response, phases)
    except Exception:  # noqa: BLE001 — logged API boundary, controlled SSE terminal event
        logger.exception("Agent stream turn failed before response emission")
        events = iter(
            [
                format_sse(
                    "error",
                    {"code": "unavailable", "message_vi": _UNAVAILABLE_VI},
                )
            ]
        )
    return StreamingResponse(
        events,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
