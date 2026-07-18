"""H24 — POST /review-cases/{case_id}/explanation (AgentCommand body only).

H39b: authorize case via Principal before building context.
Mounted on the same ``/review-cases`` prefix as H02. OpenAPI must not expose
context, source_id, actor, advisor, or other server-only fields.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.model import TextModel
from app.agent.runtime import get_text_model, run_explanation
from app.agent.schemas import AgentCommand, AgentExplanation, ExplanationStatus, RefusalReason
from app.agent.guardrails import REFUSAL_ANSWERS_VI, REFUSAL_LIMITATIONS_VI
from app.auth.principal import Principal, require_active_role
from app.auth.rbac import audit, principal_can_view_care_case
from app.cases.store import store
from app.config import Settings, get_settings
from app.database import get_db

router = APIRouter(prefix="/review-cases", tags=["review-cases"])


def _scope_refused() -> AgentExplanation:
    return AgentExplanation(
        status=ExplanationStatus.REFUSED,
        answer_vi=REFUSAL_ANSWERS_VI[RefusalReason.OUT_OF_SCOPE_DATA],
        limitations_vi=REFUSAL_LIMITATIONS_VI[RefusalReason.OUT_OF_SCOPE_DATA],
        refusal_reason=RefusalReason.OUT_OF_SCOPE_DATA,
        model_version=None,
    )


@router.post(
    "/{case_id}/explanation",
    response_model=AgentExplanation,
    summary="Grounded case explanation (server-derived context)",
    response_description=(
        "AgentExplanation — ok / refused / insufficient_data / unavailable. "
        "Context and trusted scope are built on the server from the session Principal."
    ),
)
def create_case_explanation(
    case_id: str,
    command: AgentCommand,
    principal: Principal = Depends(require_active_role),
    db: Session = Depends(get_db),
    model: TextModel = Depends(get_text_model),
    settings: Settings = Depends(get_settings),
) -> AgentExplanation:
    """Body: intent / question / locale only. Never accept client-supplied context."""
    snap = store.get(case_id)
    if snap is not None:
        allowed = principal_can_view_care_case(
            principal,
            case_advisor_ref=snap.advisor_ref,
            case_state=snap.state.value,
        )
    else:
        # No care snapshot yet — only ban_quan_ly may open explanation
        # (pre-handoff / projection path). gvcn never sees pre-handoff.
        allowed = principal.active_role == "ban_quan_ly"

    if not allowed:
        audit(
            principal,
            action="agent.explanation",
            resource_handle=case_id,
            allowed=False,
            db=db,
        )
        return _scope_refused()

    audit(
        principal,
        action="agent.explanation",
        resource_handle=case_id,
        allowed=True,
        db=db,
    )
    return run_explanation(
        case_id,
        command,
        session=db,
        model=model,
        settings=settings,
    )
