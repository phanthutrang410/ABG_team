"""H37 — Global Agent backend turn + strict capability registry.

``run_turn`` is the whole decision surface for ``POST /agent/turns``:
resolve a safe page context from ``surface``, derive the (deny-by-default)
allowed capability set, optionally ask an injected :class:`TextModel` to
pick **at most one** capability (one call, one JSON field — never a list,
never a raw tool/URL/SQL string), and render a deterministic Vietnamese
answer from a fixed template. The model never drives navigation directly —
``ui_actions`` are always the backend-issued capability catalog for the
surface, exactly like ``app.weekly.briefing`` action cards, so a chosen
capability that fails validation has zero effect on what is returned.

Forbidden effects (Ethics §8 / target architecture §§10-11) — ``run_workflow``,
``send_mail``, ``transition``, ``approve``, ``assign``, and any arbitrary
URL/SQL payload in ``question``/``resource_handle`` — are screened out by a
guardrail scan *before* any capability/model logic runs, exactly like
prompt injection: the turn is refused with zero side effects and zero model
calls, not silently downgraded.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Literal, Optional, Sequence, Tuple

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.agent.model import ModelUnavailable, TextModel
from app.auth.principal import Principal, record_access_event

Surface = Literal["weekly_report", "case_analysis", "advisor_drafts"]

#: Strict capability registry (target architecture §11) — nothing outside
#: this frozenset may ever be returned as a ``ui_actions[].key`` or chosen
#: by the model, regardless of what a question/model response asks for.
CAPABILITY_REGISTRY: frozenset[str] = frozenset(
    {
        "open_weekly_report",
        "open_case_analysis",
        "open_advisor_drafts",
        "explain_report_limitation",
        "copy_draft_preview",
    }
)

#: Explicitly named forbidden effects — must always fail closed with zero
#: state change, never partially applied and never silently ignored.
FORBIDDEN_TOOLS: frozenset[str] = frozenset(
    {"run_workflow", "send_mail", "transition", "approve", "assign"}
)

#: surface -> ordered allowed capabilities (deny-by-default; unlisted
#: surfaces are out of scope, not merged/expanded).
SURFACE_CAPABILITIES: Dict[str, Tuple[str, ...]] = {
    "weekly_report": ("open_weekly_report", "explain_report_limitation"),
    "case_analysis": ("open_case_analysis", "explain_report_limitation"),
    "advisor_drafts": ("open_advisor_drafts", "copy_draft_preview"),
}
assert all(cap in CAPABILITY_REGISTRY for caps in SURFACE_CAPABILITIES.values() for cap in caps)

_ROUTE_KEYS: Dict[str, str] = {
    "open_weekly_report": "reports.weekly",
    "open_case_analysis": "reports.weekly.case",
    "open_advisor_drafts": "notify",
    "explain_report_limitation": "reports.weekly.limitation",
    "copy_draft_preview": "notify.copy",
}

_LABELS_VI: Dict[str, str] = {
    "open_weekly_report": "Xem báo cáo tuần",
    "open_case_analysis": "Xem phân tích case",
    "open_advisor_drafts": "Soạn thông báo cho GVCN (bản nháp)",
    "explain_report_limitation": "Xem giới hạn dữ liệu báo cáo",
    "copy_draft_preview": "Copy nội dung bản nháp",
}

_ANSWER_TEMPLATES_VI: Dict[str, str] = {
    "open_weekly_report": (
        "Anh/chị có thể mở báo cáo tuần để xem tín hiệu mới, case đang theo dõi và thay đổi."
    ),
    "open_case_analysis": (
        "Anh/chị có thể mở phân tích case để xem mức ưu tiên rà soát và yếu tố đóng góp."
    ),
    "open_advisor_drafts": (
        "Anh/chị có thể mở bản nháp thông báo cho GVCN — vẫn cần con người duyệt trước khi gửi."
    ),
    "explain_report_limitation": (
        "Báo cáo tuần chỉ hiển thị tổng hợp có thể so sánh được; dữ liệu thiếu hoặc cũ sẽ được "
        "đánh dấu insufficient_data/stale, không suy diễn thành \"ổn định\"."
    ),
    "copy_draft_preview": (
        "Anh/chị có thể copy nội dung bản nháp để dán vào email/tin nhắn của mình — hệ thống "
        "không tự gửi thay anh/chị."
    ),
}

_OUT_OF_SCOPE_ANSWER_VI = (
    "Yêu cầu này nằm ngoài phạm vi màn hình mà trợ lý có thể hỗ trợ điều hướng."
)


class TurnStatus(str, Enum):
    OK = "ok"
    REFUSED = "refused"


class TurnRefusalReason(str, Enum):
    """Machine-readable refusal codes — every one implies zero side effects."""

    FORBIDDEN_TOOL = "forbidden_tool_requested"
    OUT_OF_SCOPE = "out_of_scope_surface"
    INJECTION_DETECTED = "prompt_injection_detected"
    ARBITRARY_ACTION = "arbitrary_url_or_sql_requested"


# --- guardrail scan (runs BEFORE any capability/model logic) --------------

_FORBIDDEN_ACTION_KEYWORDS: Tuple[str, ...] = (
    "gửi email",
    "gửi tin",
    "gửi cho",
    "gửi giúp",
    "gửi hộ",
    "gửi luôn",
    "send mail",
    "send email",
    "duyệt case",
    "duyệt luôn",
    "approve case",
    "approve this",
    "chuyển trạng thái",
    "đổi trạng thái",
    "transition case",
    "change state",
    "change the state",
    "giao case",
    "assign case",
    "assign this",
    "phân công",
    "chạy workflow",
    "run_workflow",
    "run workflow",
    "chạy weekly",
    "kích hoạt workflow",
    "trigger workflow",
)

_INJECTION_KEYWORDS: Tuple[str, ...] = (
    "ignore previous instructions",
    "ignore all previous",
    "disregard the rules",
    "disregard previous",
    "bỏ qua hướng dẫn",
    "bỏ qua mọi hướng dẫn",
    "bỏ qua các quy tắc",
    "bỏ qua giới hạn",
    "you are now",
    "bạn là một ai khác",
    "reveal your system prompt",
    "tiết lộ system prompt",
    "tiết lộ hướng dẫn hệ thống",
    "act as",
    "jailbreak",
    "no longer bound",
    "không còn giới hạn",
)

_SQL_PATTERN = re.compile(
    r"(?i)\b(select|drop|delete|insert|update|union)\b[^\n]*\b(from|table|into|values)\b|;\s*--|--\s*$"
)
_URL_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9+.\-]*://")


def _scan_forbidden(text: Optional[str]) -> Optional[TurnRefusalReason]:
    """Deny-by-default scan of one field; never mutates/executes anything."""
    if not text:
        return None
    if _URL_PATTERN.search(text) or _SQL_PATTERN.search(text):
        return TurnRefusalReason.ARBITRARY_ACTION
    lowered = text.lower()
    for keyword in _FORBIDDEN_ACTION_KEYWORDS:
        if keyword in lowered:
            return TurnRefusalReason.FORBIDDEN_TOOL
    for keyword in _INJECTION_KEYWORDS:
        if keyword in lowered:
            return TurnRefusalReason.INJECTION_DETECTED
    return None


_REFUSAL_ANSWERS_VI: Dict[TurnRefusalReason, str] = {
    TurnRefusalReason.FORBIDDEN_TOOL: (
        "Tôi không thể gửi, duyệt, giao case, đổi trạng thái hay chạy workflow — mọi hành động "
        "này do con người thực hiện. Tôi chỉ hỗ trợ điều hướng và giải thích nội dung có sẵn."
    ),
    TurnRefusalReason.OUT_OF_SCOPE: _OUT_OF_SCOPE_ANSWER_VI,
    TurnRefusalReason.INJECTION_DETECTED: (
        "Tôi không thể bỏ qua hướng dẫn hệ thống hoặc đổi vai trò theo yêu cầu trong câu hỏi. "
        "Tôi chỉ thực hiện điều hướng/giải thích đã được cho phép."
    ),
    TurnRefusalReason.ARBITRARY_ACTION: (
        "Tôi không thể truy cập một URL hoặc thực thi câu lệnh dữ liệu tùy ý theo yêu cầu này."
    ),
}


# --- request/response contracts --------------------------------------------


class AgentTurnRequest(BaseModel):
    """Public HTTP body — server resolves everything else (no client context)."""

    model_config = ConfigDict(extra="forbid")

    surface: str = Field(min_length=1, max_length=64)
    resource_handle: Optional[str] = Field(default=None, max_length=200)
    question: Optional[str] = Field(default=None, max_length=500)
    locale: Literal["vi"] = "vi"


class UIAction(BaseModel):
    """Backend-issued capability card — never a raw URL/tool-call from the model."""

    model_config = ConfigDict(extra="forbid")

    key: str
    label_vi: str
    route_key: str

    @model_validator(mode="after")
    def _key_in_registry(self) -> "UIAction":
        if self.key not in CAPABILITY_REGISTRY:
            raise ValueError(f"ui_action key {self.key!r} not in CAPABILITY_REGISTRY")
        return self


class AgentTurnResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: TurnStatus
    answer_vi: str = Field(min_length=1)
    evidence_refs: List[str] = Field(default_factory=list)
    ui_actions: List[UIAction] = Field(default_factory=list)
    refusal_reason: Optional[TurnRefusalReason] = None

    @model_validator(mode="after")
    def _check_invariants(self) -> "AgentTurnResponse":
        if self.status is TurnStatus.REFUSED:
            if self.refusal_reason is None:
                raise ValueError("refused status requires a refusal_reason")
            if self.ui_actions:
                raise ValueError("refused status must carry zero ui_actions (zero effect)")
        if self.status is TurnStatus.OK and self.refusal_reason is not None:
            raise ValueError("refusal_reason must be null unless status is 'refused'")
        for action in self.ui_actions:
            if action.key in FORBIDDEN_TOOLS:
                raise ValueError(f"forbidden tool leaked into ui_actions: {action.key!r}")
        return self


def _action_card(capability: str) -> UIAction:
    return UIAction(
        key=capability, label_vi=_LABELS_VI[capability], route_key=_ROUTE_KEYS[capability]
    )


_TOOL_CHOICE_SYSTEM = (
    "Bạn chọn tối đa một capability_key duy nhất từ allowed_capabilities được cấp. "
    "Không tự tạo capability_key khác, không trả URL/SQL/tool khác. "
    'Trả JSON duy nhất: {"capability_key": string} — không giải thích thêm.'
)


def _choose_capability(model: Optional[TextModel], allowed: Sequence[str]) -> str:
    """At most ONE model call, at most ONE chosen capability — never a list."""
    default = allowed[0]
    if model is None:
        return default
    try:
        raw = model.complete(
            system=_TOOL_CHOICE_SYSTEM,
            user=json.dumps({"allowed_capabilities": list(allowed)}, ensure_ascii=False),
        )
    except ModelUnavailable:
        return default
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError):
        return default
    if not isinstance(payload, dict):
        return default
    choice = payload.get("capability_key")
    if not isinstance(choice, str) or choice not in allowed:
        return default
    return choice


@dataclass(frozen=True)
class TurnContext:
    """Server-resolved safe page context — never built from client fields."""

    surface: str
    allowed_capabilities: Tuple[str, ...]


def resolve_safe_context(surface: str) -> Optional[TurnContext]:
    """Deny-by-default: only a surface in ``SURFACE_CAPABILITIES`` resolves."""
    allowed = SURFACE_CAPABILITIES.get(surface)
    if allowed is None:
        return None
    return TurnContext(surface=surface, allowed_capabilities=allowed)


def run_turn(
    request: AgentTurnRequest,
    principal: Principal,
    *,
    model: Optional[TextModel] = None,
) -> AgentTurnResponse:
    """Guardrail scan -> safe context -> allowed capabilities -> one tool decision."""
    refusal = _scan_forbidden(request.question) or _scan_forbidden(request.resource_handle)
    if refusal is not None:
        record_access_event(
            actor_id=principal.actor_id,
            role=principal.active_role,
            action=f"agent_turn_refused:{refusal.value}",
            resource_handle=f"surface:{request.surface}",
        )
        return AgentTurnResponse(
            status=TurnStatus.REFUSED,
            answer_vi=_REFUSAL_ANSWERS_VI[refusal],
            evidence_refs=[],
            ui_actions=[],
            refusal_reason=refusal,
        )

    context = resolve_safe_context(request.surface)
    if context is None:
        record_access_event(
            actor_id=principal.actor_id,
            role=principal.active_role,
            action="agent_turn_refused:out_of_scope_surface",
            resource_handle=f"surface:{request.surface}",
        )
        return AgentTurnResponse(
            status=TurnStatus.REFUSED,
            answer_vi=_OUT_OF_SCOPE_ANSWER_VI,
            evidence_refs=[],
            ui_actions=[],
            refusal_reason=TurnRefusalReason.OUT_OF_SCOPE,
        )

    chosen = _choose_capability(model, context.allowed_capabilities)
    ui_actions = [_action_card(cap) for cap in context.allowed_capabilities]

    evidence_refs: List[str] = [f"capability:{chosen}"]
    handle = (request.resource_handle or "").strip()
    if handle:
        evidence_refs.append(f"resource:{handle}")

    record_access_event(
        actor_id=principal.actor_id,
        role=principal.active_role,
        action=f"agent_turn:{context.surface}",
        resource_handle=handle or f"surface:{context.surface}",
    )

    return AgentTurnResponse(
        status=TurnStatus.OK,
        answer_vi=_ANSWER_TEMPLATES_VI[chosen],
        evidence_refs=evidence_refs,
        ui_actions=ui_actions,
        refusal_reason=None,
    )
