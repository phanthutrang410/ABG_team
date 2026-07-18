"""H24 — POST /review-cases/{case_id}/explanation (AgentCommand body only).

Mounted on the same ``/review-cases`` prefix as H02. OpenAPI must not expose
context, source_id, actor, advisor, or other server-only fields.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.model import TextModel
from app.agent.runtime import get_text_model, run_explanation
from app.agent.schemas import AgentCommand, AgentExplanation
from app.config import Settings, get_settings
from app.database import get_db

router = APIRouter(prefix="/review-cases", tags=["review-cases"])


@router.post(
    "/{case_id}/explanation",
    response_model=AgentExplanation,
    summary="Grounded case explanation (server-derived context)",
    response_description=(
        "AgentExplanation — ok / refused / insufficient_data / unavailable. "
        "Context and trusted scope are built on the server (MVP demo identity, "
        "not production RBAC)."
    ),
)
def create_case_explanation(
    case_id: str,
    command: AgentCommand,
    db: Session = Depends(get_db),
    model: TextModel = Depends(get_text_model),
    settings: Settings = Depends(get_settings),
) -> AgentExplanation:
    """Body: intent / question / locale only. Never accept client-supplied context."""
    return run_explanation(
        case_id,
        command,
        session=db,
        model=model,
        settings=settings,
    )
