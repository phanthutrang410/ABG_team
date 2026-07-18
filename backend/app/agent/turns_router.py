"""H37 — POST /agent/turns (strict capability registry; max one tool decision).

Only the trusted server-resolved ``Principal`` (H36) and a provider-neutral
``TextModel`` chosen strictly for tool-choice (never raw case/report data)
enter :func:`run_turn`. When no OpenAI key is configured — or the provider
call fails — ``model`` is ``None``/unusable and the turn still returns
deterministic action cards (zero live calls either way in default tests).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from app.agent.model import TextModel
from app.agent.openai_client import OpenAIResponsesClient
from app.agent.turns import AgentTurnRequest, AgentTurnResponse, run_turn
from app.auth.principal import Principal, get_principal
from app.config import Settings, get_settings

router = APIRouter(prefix="/agent", tags=["agent"])


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


@router.post(
    "/turns",
    response_model=AgentTurnResponse,
    summary="Global Agent turn — strict capability registry, max one tool decision",
)
def create_agent_turn(
    body: AgentTurnRequest,
    principal: Principal = Depends(get_principal),
    model: Optional[TextModel] = Depends(get_turn_model),
) -> AgentTurnResponse:
    return run_turn(body, principal, model=model)
