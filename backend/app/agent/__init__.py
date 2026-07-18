"""Silent Shield explanation agent — grounding & guardrail contracts (T03/H23/H24)."""
from app.agent.context_service import (
    TrustedScope,
    build_agent_context,
    provider_call_allowed,
)
from app.agent.grounded import explain as explain_grounded
from app.agent.runtime import get_text_model, run_explanation
from app.agent.schemas import AgentCommand

__all__ = [
    "AgentCommand",
    "TrustedScope",
    "build_agent_context",
    "explain_grounded",
    "get_text_model",
    "provider_call_allowed",
    "run_explanation",
]
