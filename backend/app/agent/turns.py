"""H37 — Global Agent backend turn + strict capability registry.

``run_turn`` is the whole decision surface for ``POST /agent/turns``.
Non-overview surfaces keep the H37 template path: resolve a safe page context
from ``surface`` and server principal, derive the (deny-by-default) allowed
capability set, optionally ask an injected :class:`TextModel` to pick **at
most one** capability (one call, one JSON field — never a list, never a raw
tool/URL/SQL string), and render a deterministic Vietnamese answer from a
fixed template.

Surface ``overview`` uses the in-house bounded routing DAG (``overview_graph``):
guardrails → context packet → route → answer|tool|clarify → output guard,
bounded to ≤1 model call and ≤1 tool decision.  This is deliberately not an
open-ended ReAct loop.

The model never drives navigation directly — ``ui_actions`` are always the
backend-issued capability catalog for the surface, exactly like
``app.weekly.briefing`` action cards, so a chosen capability that fails
validation has zero effect on what is returned.

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
from typing import Callable, Dict, List, Literal, Optional, Sequence, Tuple

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from app.agent.model import ModelUnavailable, TextModel
from app.agent.tracing import (
    redact_turn_inputs,
    redact_turn_outputs,
    trace_agent_run,
)
from app.auth.principal import Principal, record_access_event

Surface = Literal["weekly_report", "case_analysis", "advisor_drafts", "overview"]

#: Strict capability registry (target architecture §11) — nothing outside
#: this frozenset may ever be returned as a ``ui_actions[].key`` or chosen
#: by the model, regardless of what a question/model response asks for.
CAPABILITY_REGISTRY: frozenset[str] = frozenset(
    {
        "open_weekly_report",
        "open_case_analysis",
        "open_advisor_drafts",
        "open_overview_report",
        "open_review_list",
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
    "overview": ("open_overview_report", "open_review_list", "open_advisor_drafts"),
}
assert all(cap in CAPABILITY_REGISTRY for caps in SURFACE_CAPABILITIES.values() for cap in caps)

# H36/H39b: explicit role × surface allowlist.  Unknown/missing roles and
# empty capability sets fail closed; a client cannot obtain leader cards by
# forging ``surface``.
ROLE_SURFACE_CAPABILITIES: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "ban_quan_ly": dict(SURFACE_CAPABILITIES),
    "gvcn": {
        "weekly_report": ("explain_report_limitation",),
        "case_analysis": ("open_case_analysis", "explain_report_limitation"),
        "advisor_drafts": (),
        # A scoped ``my-class`` capability is not implemented in H37 yet.
        # Refuse instead of leaking organization-wide Overview navigation.
        "overview": (),
    },
}

_ROUTE_KEYS: Dict[str, str] = {
    "open_weekly_report": "reports.weekly",
    "open_case_analysis": "reports.weekly.case",
    "open_advisor_drafts": "notify",
    "open_overview_report": "overview.report",
    "open_review_list": "analysis.reviews",
    "explain_report_limitation": "reports.weekly.limitation",
    "copy_draft_preview": "notify.copy",
}

_LABELS_VI: Dict[str, str] = {
    "open_weekly_report": "Xem báo cáo tuần",
    "open_case_analysis": "Xem phân tích case",
    "open_advisor_drafts": "Soạn thông báo cho GVCN (bản nháp)",
    "open_overview_report": "Xem báo cáo tổng quan",
    "open_review_list": "Xem danh sách rà soát",
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
    "open_overview_report": (
        "Anh/chị có thể mở báo cáo tổng quan để xem tóm tắt tín hiệu và giới hạn dữ liệu hiện có."
    ),
    "open_review_list": (
        "Anh/chị có thể mở danh sách rà soát để xem các case đang chờ ưu tiên xem xét."
    ),
    "explain_report_limitation": (
        "Báo cáo tuần chỉ hiển thị phần tổng hợp có đủ căn cứ để so sánh. Dữ liệu thiếu hoặc "
        "cũ sẽ được nêu rõ, không suy diễn thành \"ổn định\"."
    ),
    "copy_draft_preview": (
        "Anh/chị có thể copy nội dung bản nháp để dán vào email/tin nhắn của mình — hệ thống "
        "không tự gửi thay anh/chị."
    ),
}

assert all(
    capability in CAPABILITY_REGISTRY
    for surface_map in ROLE_SURFACE_CAPABILITIES.values()
    for capabilities in surface_map.values()
    for capability in capabilities
)
assert set(_ROUTE_KEYS) == set(_LABELS_VI) == set(_ANSWER_TEMPLATES_VI) == set(
    CAPABILITY_REGISTRY
)

_OUT_OF_SCOPE_ANSWER_VI = (
    "Yêu cầu này nằm ngoài phạm vi màn hình mà trợ lý có thể hỗ trợ điều hướng."
)

_AVAILABLE_ACTIONS_ANSWER_VI = (
    "Trợ lý chưa chọn hành động tự động. Anh/chị vẫn có thể dùng các thẻ "
    "đã được cấp quyền bên dưới."
)

_MODEL_UNAVAILABLE_ANSWER_VI = (
    "Trợ lý tạm thời không kết nối được mô hình hoặc nhận phản hồi không hợp lệ. "
    "Anh/chị vẫn có thể dùng các thẻ đã được cấp quyền bên dưới."
)


class TurnStatus(str, Enum):
    OK = "ok"
    REFUSED = "refused"
    UNAVAILABLE = "unavailable"


class TurnRefusalReason(str, Enum):
    """Machine-readable refusal codes — every one implies zero side effects."""

    FORBIDDEN_TOOL = "forbidden_tool_requested"
    OUT_OF_SCOPE = "out_of_scope_surface"
    INJECTION_DETECTED = "prompt_injection_detected"
    ARBITRARY_ACTION = "arbitrary_url_or_sql_requested"
    SENSITIVE_DATA = "sensitive_data_requested"
    UNSAFE_INFERENCE = "unsafe_inference_requested"


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
_EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)
_PHONE_PATTERN = re.compile(r"(?:\+?\d[\d\-\s]{7,}\d)")
_SENSITIVE_LOOKUP_PATTERN = re.compile(
    r"(?i)\b(mssv|student[ _-]?id|sđt|so dien thoai|số điện thoại|"
    r"email\s+(của|cua)|ngày sinh|ngay sinh|địa chỉ|dia chi|"
    r"quê(?:\s+quán|\s+ở|\s+đâu)?|que(?:\s+quan|\s+o|\s+dau)?|"
    r"tiểu sử|tieu su|thông tin cá nhân|thong tin ca nhan)\b"
)
_THIRD_PARTY_LOOKUP_PATTERN = re.compile(
    r"(?i)\b(?:thằng|thang|đứa|dua|ông|ong|cô|chị|chi|anh|sinh\s+viên|sinh\s+vien)"
    r"\s+[a-zà-ỹđ]{2,}(?:\s+[a-zà-ỹđ]{2,}){0,3}"
    r"\s+(?:là|la)\s+(?:ai|thằng\s+nào|thang\s+nao|người\s+nào|nguoi\s+nao)\b"
)
# A likely full Vietnamese personal name. Requiring at least three components
# catches lower-case names too without treating ordinary two-word phrases as a
# person merely because their first token can also be a surname.
_PERSON_NAME_CONTEXT_PATTERN = re.compile(
    r"\b(?:nguyễn|trần|lê|phạm|hoàng|huỳnh|phan|vũ|võ|đặng|bùi|đỗ|hồ|ngô|dương|lý)"
    r"(?:\s+[a-zà-ỹđ]{2,}){2,4}\b",
    re.IGNORECASE,
)
_STREET_ADDRESS_PATTERN = re.compile(
    r"(?i)(?:\b(?:số\s+nhà|địa\s+chỉ|ở\s+tại|sống\s+tại)\s+\d{1,4}[a-z]?(?:[/-]\d{1,4})?\b|"
    r"\b\d{1,4}[a-z]?(?:[/-]\d{1,4})?\s+(?:đường|phố|ngõ|hẻm|ấp|thôn|tổ)\b)"
)
_UNSAFE_INFERENCE_PATTERN = re.compile(
    r"(?i)\b("
    r"trầm cảm|tram cam|tự tử|tu tu|bắt nạt|bat nat|"
    r"khủng hoảng tâm lý|khung hoang tam ly|"
    r"chẩn đoán|chan doan|điểm rủi ro|diem rui ro|raw score|risk score|"
    r"xác suất bỏ học|xac suat bo hoc|phần trăm bỏ học|phan tram bo hoc|"
    r"mấy\s*%\s*bỏ học|may\s*%\s*bo hoc|probability|weights?|"
    r"tự tính( lại)? điểm|tu tinh( lai)? diem|trọng số|trong so|kỷ luật|ky luat|"
    r"nhà nghèo|nha ngheo|bạn nghèo|ban ngheo|dân tộc|dan toc|"
    r"khó khăn tài chính|kho khan tai chinh|"
    r"hoàn cảnh gia đình|hoan canh gia dinh|nguyên nhân cá nhân|nguyen nhan ca nhan"
    r")\b"
)


def _scan_forbidden(text: Optional[str]) -> Optional[TurnRefusalReason]:
    """Deny-by-default scan of one field; never mutates/executes anything."""
    if not text:
        return None
    if _URL_PATTERN.search(text) or _SQL_PATTERN.search(text):
        return TurnRefusalReason.ARBITRARY_ACTION
    if (
        _EMAIL_PATTERN.search(text)
        or _PHONE_PATTERN.search(text)
        or _SENSITIVE_LOOKUP_PATTERN.search(text)
        or _THIRD_PARTY_LOOKUP_PATTERN.search(text)
        or _PERSON_NAME_CONTEXT_PATTERN.search(text)
        or _STREET_ADDRESS_PATTERN.search(text)
    ):
        return TurnRefusalReason.SENSITIVE_DATA
    if _UNSAFE_INFERENCE_PATTERN.search(text):
        return TurnRefusalReason.UNSAFE_INFERENCE
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
    TurnRefusalReason.SENSITIVE_DATA: (
        "Tôi không thể tra cứu hoặc xử lý MSSV, thông tin liên hệ, ngày sinh hay địa chỉ trong "
        "Global Agent. Vui lòng dùng màn hình nghiệp vụ đã được phân quyền nếu cần."
    ),
    TurnRefusalReason.UNSAFE_INFERENCE: (
        "Tôi không thể chẩn đoán, suy đoán nguyên nhân cá nhân, tiết lộ/tự tính điểm rủi ro "
        "hoặc xác suất. Tôi chỉ giải thích dữ kiện và giới hạn đã được hệ thống cấp."
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
    #: Deprecated compatibility field. It is accepted but never used as model
    #: context or guardrail input; trusted context is resolved server-side.
    thread_summary: Optional[str] = Field(default=None, max_length=800)


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
        if self.route_key != _ROUTE_KEYS[self.key]:
            raise ValueError(f"ui_action route_key does not match registry key {self.key!r}")
        if self.label_vi != _LABELS_VI[self.key]:
            raise ValueError(f"ui_action label_vi does not match registry key {self.key!r}")
        return self


class AgentTurnResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: TurnStatus
    answer_vi: str = Field(min_length=1)
    evidence_refs: List[str] = Field(default_factory=list)
    ui_actions: List[UIAction] = Field(default_factory=list)
    refusal_reason: Optional[TurnRefusalReason] = None
    #: Capability chosen for this turn (nullable). When set, must be in registry.
    selected_capability: Optional[str] = None

    @model_validator(mode="after")
    def _check_invariants(self) -> "AgentTurnResponse":
        if self.status is TurnStatus.REFUSED:
            if self.refusal_reason is None:
                raise ValueError("refused status requires a refusal_reason")
            if self.ui_actions:
                raise ValueError("refused status must carry zero ui_actions (zero effect)")
            if self.selected_capability is not None:
                raise ValueError("refused status must not carry selected_capability")
        if self.status is TurnStatus.OK and self.refusal_reason is not None:
            raise ValueError("refusal_reason must be null unless status is 'refused'")
        if self.status is TurnStatus.UNAVAILABLE:
            if self.refusal_reason is not None:
                raise ValueError("unavailable status must not carry refusal_reason")
            if self.selected_capability is not None:
                raise ValueError("unavailable status must not auto-select a capability")
        if self.selected_capability is not None and self.selected_capability not in CAPABILITY_REGISTRY:
            raise ValueError(
                f"selected_capability {self.selected_capability!r} not in CAPABILITY_REGISTRY"
            )
        if self.selected_capability is not None and not any(
            action.key == self.selected_capability for action in self.ui_actions
        ):
            raise ValueError("selected_capability must match a returned ui_action")
        for action in self.ui_actions:
            if action.key in FORBIDDEN_TOOLS:
                raise ValueError(f"forbidden tool leaked into ui_actions: {action.key!r}")
        return self


def _action_card(capability: str) -> UIAction:
    return UIAction(
        key=capability, label_vi=_LABELS_VI[capability], route_key=_ROUTE_KEYS[capability]
    )


_TOOL_CHOICE_SYSTEM = (
    "Bạn định tuyến câu hỏi sang tối đa một capability_key trong allowed_capabilities. "
    "Nếu câu hỏi không yêu cầu rõ một capability, trả null. Không tự tạo key, URL, SQL "
    "hay tool khác. Trả đúng một JSON object theo schema."
)

_TOOL_CHOICE_SCHEMA = {
    "type": "object",
    "properties": {"capability_key": {"type": ["string", "null"]}},
    "required": ["capability_key"],
    "additionalProperties": False,
}


def _choose_capability(
    model: Optional[TextModel],
    allowed: Sequence[str],
    *,
    question: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """Return ``(choice, failure)``; failure is unavailable|invalid|None."""
    normalized_question = (question or "").strip()
    if not normalized_question:
        return None, None
    if model is None:
        return None, "unavailable"
    try:
        user = json.dumps(
            {
                "question": normalized_question,
                "allowed_capabilities": list(allowed),
            },
            ensure_ascii=False,
        )
        complete_json = getattr(model, "complete_json", None)
        if callable(complete_json):
            payload = complete_json(
                system=_TOOL_CHOICE_SYSTEM,
                user=user,
                schema=_TOOL_CHOICE_SCHEMA,
                name="agent_capability_route",
            )
        else:
            raw = model.complete(system=_TOOL_CHOICE_SYSTEM, user=user)
            payload = json.loads(raw)
    except ModelUnavailable:
        return None, "unavailable"
    except (ValueError, TypeError, json.JSONDecodeError):
        return None, "invalid"
    if not isinstance(payload, dict):
        return None, "invalid"
    choice = payload.get("capability_key")
    if choice is None:
        return None, None
    if not isinstance(choice, str) or choice not in allowed:
        return None, "invalid"
    return choice, None


@dataclass(frozen=True)
class TurnContext:
    """Server-resolved safe page context — never built from client fields."""

    surface: str
    allowed_capabilities: Tuple[str, ...]


def resolve_safe_context(surface: str, *, role: Optional[str]) -> Optional[TurnContext]:
    """Deny-by-default role × surface capability resolution."""
    role_matrix = ROLE_SURFACE_CAPABILITIES.get(role or "")
    if role_matrix is None:
        return None
    allowed = role_matrix.get(surface)
    if not allowed:
        return None
    return TurnContext(surface=surface, allowed_capabilities=allowed)


def _emit_phase(on_phase: Optional[Callable[[str], None]], phase: str) -> None:
    if on_phase is not None:
        on_phase(phase)


@trace_agent_run(
    "agent_turn",
    process_inputs=redact_turn_inputs,
    process_outputs=redact_turn_outputs,
)
def run_turn(
    request: AgentTurnRequest,
    principal: Principal,
    *,
    model: Optional[TextModel] = None,
    overview_facts: Optional[Dict[str, object]] = None,
    on_phase: Optional[Callable[[str], None]] = None,
    db: Optional[Session] = None,
) -> AgentTurnResponse:
    """Guardrail scan -> safe context -> allowed capabilities -> one tool decision.

    Surface ``overview`` uses the bounded routing DAG. Other
    surfaces keep the H37 template tool-choice path.

    ``on_phase`` is optional SSE progress callback (phase name only; no prose).
    """
    _emit_phase(on_phase, "guardrails")
    refusal = (
        _scan_forbidden(request.question)
        or _scan_forbidden(request.resource_handle)
    )
    if refusal is not None:
        record_access_event(
            actor_id=principal.actor_id,
            role=principal.active_role,
            action=f"agent_turn_refused:{refusal.value}",
            resource_handle=f"surface:{request.surface}",
            decision="denied",
            db=db,
        )
        return AgentTurnResponse(
            status=TurnStatus.REFUSED,
            answer_vi=_REFUSAL_ANSWERS_VI[refusal],
            evidence_refs=[],
            ui_actions=[],
            refusal_reason=refusal,
            selected_capability=None,
        )

    context = resolve_safe_context(request.surface, role=principal.active_role)
    if context is None:
        record_access_event(
            actor_id=principal.actor_id,
            role=principal.active_role,
            action="agent_turn_refused:out_of_scope_surface",
            resource_handle=f"surface:{request.surface}",
            decision="denied",
            db=db,
        )
        return AgentTurnResponse(
            status=TurnStatus.REFUSED,
            answer_vi=_OUT_OF_SCOPE_ANSWER_VI,
            evidence_refs=[],
            ui_actions=[],
            refusal_reason=TurnRefusalReason.OUT_OF_SCOPE,
            selected_capability=None,
        )

    if context.surface == "overview":
        # Lazy import avoids circular import with overview_graph → turns helpers.
        from app.agent.overview_graph import run_overview_graph

        return run_overview_graph(
            request,
            principal,
            model=model,
            allowed_capabilities=context.allowed_capabilities,
            facts=overview_facts,
            on_phase=on_phase,
            guardrails_phase_emitted=True,
            db=db,
        )

    _emit_phase(on_phase, "context")
    _emit_phase(on_phase, "route")
    chosen, route_failure = _choose_capability(
        model,
        context.allowed_capabilities,
        question=request.question,
    )
    _emit_phase(on_phase, "answer")
    ui_actions = [_action_card(cap) for cap in context.allowed_capabilities]

    if chosen is not None:
        evidence_refs: List[str] = [f"capability:{chosen}"]
    elif route_failure is not None:
        evidence_refs = [f"route:model_{route_failure}"]
    else:
        evidence_refs = ["route:cards_only"]

    record_access_event(
        actor_id=principal.actor_id,
        role=principal.active_role,
        action=f"agent_turn:{context.surface}",
        # Client resource_handle has not been resolved by a trusted loader yet.
        resource_handle=f"surface:{context.surface}",
        db=db,
    )

    _emit_phase(on_phase, "output_guard")
    return AgentTurnResponse(
        status=(TurnStatus.UNAVAILABLE if route_failure is not None else TurnStatus.OK),
        answer_vi=(
            _ANSWER_TEMPLATES_VI[chosen]
            if chosen is not None
            else (
                _MODEL_UNAVAILABLE_ANSWER_VI
                if route_failure is not None
                else _AVAILABLE_ACTIONS_ANSWER_VI
            )
        ),
        evidence_refs=evidence_refs,
        ui_actions=ui_actions,
        refusal_reason=None,
        selected_capability=chosen,
    )
