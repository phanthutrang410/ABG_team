"""H24 — Agent HTTP orchestration (server-derived context → explain).

Limitation (MVP demo): trusted identity/scope is read from server settings /
allowlisted demo source constants — **not** production RBAC. Browser must not
send context, source_id, actor, or advisor fields.

Zero-call rule: invoke TextModel only when ``provider_call_allowed`` is True
and an FPT key is configured (or a test injects a fake model via DI).
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from app.agent.context_service import (
    TrustedScope,
    build_agent_context,
    provider_call_allowed,
)
from app.agent.fpt_client import FPTChatClient, ModelUnavailable, TextModel
from app.agent.grounded import explain as explain_grounded
from app.agent.guardrails import REFUSAL_ANSWERS_VI, REFUSAL_LIMITATIONS_VI
from app.agent.schemas import (
    AgentCommand,
    AgentExplanation,
    AgentExplanationRequest,
    ExplanationStatus,
    RefusalReason,
)
from app.agent.stub import explain as explain_stub
from app.config import Settings, get_settings
from app.dwh.importer import SEMESTER_SOURCE_ID

#: Fail-closed copy when the provider key is missing (distinct from context unavailable).
_MODEL_KEY_UNAVAILABLE = AgentExplanation(
    status=ExplanationStatus.UNAVAILABLE,
    answer_vi=(
        "Dịch vụ mô hình tạm thời không phản hồi hoặc trả kết quả không hợp lệ. "
        "Anh/chị vui lòng thử lại sau. Dữ liệu case vẫn dùng được cho thao tác rà soát "
        "của con người."
    ),
    limitations_vi=(
        "FPT API key chưa được cấu hình trên server — không phải kết luận về dữ liệu "
        "hay về sinh viên. (MVP demo identity; chưa phải production RBAC.)"
    ),
)


class _MissingKeyModel:
    """Injectable stand-in when Settings has no FPT key — never hits the network."""

    def complete(self, *, system: str, user: str) -> str:
        raise ModelUnavailable("FPT_API_KEY is not configured")


def trusted_scope_from_settings(settings: Optional[Settings] = None) -> TrustedScope:
    """Demo scope from server — never accept source_id from the browser.

    Uses the semester allowlist source (same default as H02). MVP demo identity
    only — not production RBAC. ``settings`` reserved for future server override.
    """
    _ = settings or get_settings()
    return TrustedScope(source_id=SEMESTER_SOURCE_ID)


def get_text_model(settings: Settings = Depends(get_settings)) -> TextModel:
    """DI factory: real FPT client when key present; else fail-closed stand-in."""
    key = settings.fpt_api_key
    secret = key.get_secret_value() if hasattr(key, "get_secret_value") else str(key or "")
    if not str(secret or "").strip():
        return _MissingKeyModel()
    return FPTChatClient.from_settings(settings)


def _intent_not_allowed(request: AgentExplanationRequest) -> AgentExplanation:
    """Ready context but intent outside filtered allowed_intents — refuse, 0 model calls."""
    case = request.context.case
    model_version = case.model_version if case else None
    reason = RefusalReason.OUT_OF_SCOPE_DATA
    if request.intent == "neutral_draft":
        reason = RefusalReason.DECIDE_ACTION
    return AgentExplanation(
        status=ExplanationStatus.REFUSED,
        answer_vi=REFUSAL_ANSWERS_VI[reason],
        limitations_vi=REFUSAL_LIMITATIONS_VI[reason],
        refusal_reason=reason,
        model_version=model_version,
    )


def _fpt_key_configured(settings: Settings) -> bool:
    key = settings.fpt_api_key
    secret = key.get_secret_value() if hasattr(key, "get_secret_value") else str(key or "")
    return bool(str(secret or "").strip())


def run_explanation(
    case_id: str,
    command: AgentCommand,
    *,
    session: Session,
    model: TextModel,
    settings: Optional[Settings] = None,
) -> AgentExplanation:
    """Validate command → build context → gate → explain (black box) or fail closed."""
    cfg = settings or get_settings()
    scope = trusted_scope_from_settings(cfg)
    context = build_agent_context(case_id, scope, session=session)
    request = AgentExplanationRequest(
        context=context,
        question=command.question,
        intent=command.intent,
        locale=command.locale,
    )

    if not provider_call_allowed(context, command.intent):
        # Never call the model. Map non-ready via stub; ready+forbidden → refuse.
        if context.status == "ready":
            return _intent_not_allowed(request)
        return explain_stub(request)

    # Provider path: missing key fail-closed before network (still 0 live calls).
    # Injected fakes (tests) are not MissingKeyModel and may run without a key.
    if isinstance(model, _MissingKeyModel) or (
        not _fpt_key_configured(cfg) and type(model).__name__ == "FPTChatClient"
    ):
        return _MODEL_KEY_UNAVAILABLE

    return explain_grounded(request, model)
