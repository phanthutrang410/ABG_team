"""Overview surface AgentGraph — in-house bounded ReAct (no LangGraph).

Nodes (code-enforced): input_guardrails → build_context_packet → route_node →
answer|tool|clarify → output_guard. Caps: ≤2 model calls, ≤1 tool decision.
``ui_actions`` are always backend-issued capability cards; the model never
emits URLs or raw tool payloads.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Mapping, Optional, Sequence, Tuple

from app.agent.model import ModelUnavailable, TextModel
from app.agent.turns import (
    CAPABILITY_REGISTRY,
    AgentTurnRequest,
    AgentTurnResponse,
    TurnRefusalReason,
    TurnStatus,
    UIAction,
    _ANSWER_TEMPLATES_VI,
    _LABELS_VI,
    _REFUSAL_ANSWERS_VI,
    _ROUTE_KEYS,
    _action_card,
    _scan_forbidden,
)
from app.auth.principal import Principal, record_access_event

RouteIntent = Literal["answer", "tool", "clarify"]

MAX_MODEL_CALLS = 2
MAX_TOOL_DECISIONS = 1

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
_OVERVIEW_SYSTEM_PROMPT = (_PROMPTS_DIR / "overview_system_v1.md").read_text(encoding="utf-8")

_ROUTE_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": ["answer", "tool", "clarify"]},
        "capability_key": {"type": ["string", "null"]},
        "missing_fields": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["intent", "capability_key", "missing_fields"],
    "additionalProperties": False,
}

_PHRASE_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "answer_vi": {"type": "string"},
    },
    "required": ["answer_vi"],
    "additionalProperties": False,
}

_UNAVAILABLE_ANSWER_VI = (
    "Trợ lý tạm thời không kết nối được mô hình. Anh/chị vẫn có thể dùng các thẻ "
    "điều hướng bên dưới để mở báo cáo tổng quan, danh sách rà soát hoặc bản nháp thông báo."
)

_CLARIFY_ANSWER_VI = (
    "Anh/chị muốn xem báo cáo tổng quan, mở danh sách rà soát, hay soạn bản nháp "
    "thông báo cho GVCN? Tôi chỉ điều hướng trong các lựa chọn đã cho phép."
)

_SAFE_OUTPUT_FALLBACK_VI = (
    "Tôi chỉ có thể giải thích nội dung Overview đã được server cấp và điều hướng "
    "trong phạm vi cho phép — không trả URL/SQL hay nội dung ngoài phạm vi."
)

_EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)
_PHONE_PATTERN = re.compile(r"(?:\+?\d[\d\-\s]{7,}\d)")
_URL_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9+.\-]*://")
_SQL_PATTERN = re.compile(
    r"(?i)\b(select|drop|delete|insert|update|union)\b[^\n]*\b(from|table|into|values)\b"
)


@dataclass
class AgentGraphState:
    principal: Principal
    request: AgentTurnRequest
    allowed_capabilities: Tuple[str, ...]
    refusal: Optional[TurnRefusalReason] = None
    route: Optional[RouteIntent] = None
    capability: Optional[str] = None
    facts: Dict[str, Any] = field(default_factory=dict)
    answer_vi: str = ""
    ui_actions: List[UIAction] = field(default_factory=list)
    selected_capability: Optional[str] = None
    evidence_refs: List[str] = field(default_factory=list)
    model_calls: int = 0
    tool_decisions: int = 0
    status: TurnStatus = TurnStatus.OK


def build_context_packet(
    request: AgentTurnRequest,
    *,
    facts: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Server-derived overview facts — never raw case rows from the client."""
    packet: Dict[str, Any] = {
        "surface": "overview",
        "summary_state": "ok",
        "total_students": None,
        "review_case_count": None,
        "comparison_status": "unavailable",
        "limitations": [
            "weekly_comparison_unavailable",
            "aggregate_only",
            "no_client_case_payload",
        ],
        "freshness": "server_packet_v1",
        "thread_summary": _sanitize_thread_summary(request.thread_summary),
    }
    if facts:
        for key, value in facts.items():
            if key == "thread_summary":
                continue
            packet[key] = value
    return packet


def _sanitize_thread_summary(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    text = raw.strip()
    if not text:
        return None
    text = _URL_PATTERN.sub("[redacted-url]", text)
    text = _EMAIL_PATTERN.sub("[redacted-email]", text)
    return text[:800]


def input_guardrails(state: AgentGraphState) -> AgentGraphState:
    refusal = (
        _scan_forbidden(state.request.question)
        or _scan_forbidden(state.request.resource_handle)
        or _scan_forbidden(state.request.thread_summary)
    )
    if refusal is not None:
        state.refusal = refusal
        state.status = TurnStatus.REFUSED
        state.answer_vi = _REFUSAL_ANSWERS_VI[refusal]
        state.ui_actions = []
        state.selected_capability = None
        state.evidence_refs = []
    return state


def route_node(state: AgentGraphState, model: Optional[TextModel]) -> AgentGraphState:
    """One structured route call → answer | tool | clarify."""
    if state.refusal is not None:
        return state

    user_payload = {
        "question": state.request.question,
        "allowed_capabilities": list(state.allowed_capabilities),
        "facts": state.facts,
        "locale": state.request.locale,
    }
    system = (
        _OVERVIEW_SYSTEM_PROMPT
        + "\n\n## Route turn\n"
        "Trả đúng một JSON object theo schema: "
        '{"intent":"answer|tool|clarify","capability_key":string|null,"missing_fields":string[]}. '
        "Chỉ chọn capability_key ∈ allowed_capabilities khi intent=tool. "
        "Không bịa số ngoài facts."
    )
    parsed, fail_kind = _call_model_json(
        state,
        model,
        system=system,
        user=json.dumps(user_payload, ensure_ascii=False),
        schema=_ROUTE_JSON_SCHEMA,
        name="overview_route",
    )
    if parsed is None:
        state.route = "clarify"
        if model is None or fail_kind == "unavailable":
            state.answer_vi = _UNAVAILABLE_ANSWER_VI
            state.evidence_refs = ["route:provider_unavailable"]
        else:
            state.answer_vi = _CLARIFY_ANSWER_VI
            state.evidence_refs = ["route:clarify_fail_closed"]
        state.ui_actions = [_action_card(cap) for cap in state.allowed_capabilities]
        state.selected_capability = None
        return state

    intent = parsed.get("intent")
    if intent not in ("answer", "tool", "clarify"):
        state.route = "clarify"
        state.answer_vi = _CLARIFY_ANSWER_VI
        state.ui_actions = [_action_card(cap) for cap in state.allowed_capabilities]
        state.selected_capability = None
        state.evidence_refs = ["route:invalid_intent"]
        return state

    state.route = intent  # type: ignore[assignment]
    if intent == "tool":
        choice = parsed.get("capability_key")
        if (
            isinstance(choice, str)
            and choice in state.allowed_capabilities
            and choice in CAPABILITY_REGISTRY
            and state.tool_decisions < MAX_TOOL_DECISIONS
        ):
            state.capability = choice
        else:
            state.route = "clarify"
            state.capability = None
            state.answer_vi = _CLARIFY_ANSWER_VI
            state.ui_actions = [_action_card(cap) for cap in state.allowed_capabilities]
            state.selected_capability = None
            state.evidence_refs = ["route:invalid_capability"]
            return state
    elif intent == "clarify":
        missing = parsed.get("missing_fields")
        if isinstance(missing, list) and missing:
            fields = ", ".join(str(x) for x in missing[:5] if isinstance(x, str))
            state.answer_vi = (
                f"Tôi cần thêm thông tin ({fields}) trước khi điều hướng. {_CLARIFY_ANSWER_VI}"
            )
        else:
            state.answer_vi = _CLARIFY_ANSWER_VI
    return state


def answer_node(state: AgentGraphState, model: Optional[TextModel]) -> AgentGraphState:
    if state.refusal is not None or state.route != "answer":
        return state

    grounded = _grounded_answer_from_facts(state.facts)
    phrased = _optional_phrase(state, model, grounded, purpose="answer")
    state.answer_vi = phrased or grounded
    state.ui_actions = [_action_card(cap) for cap in state.allowed_capabilities]
    state.selected_capability = None
    state.evidence_refs = ["route:answer", "facts:overview_packet"]
    handle = (state.request.resource_handle or "").strip()
    if handle:
        state.evidence_refs.append(f"resource:{handle}")
    return state


def tool_node(state: AgentGraphState, model: Optional[TextModel]) -> AgentGraphState:
    if state.refusal is not None or state.route != "tool" or not state.capability:
        return state
    if state.tool_decisions >= MAX_TOOL_DECISIONS:
        state.route = "clarify"
        state.answer_vi = _CLARIFY_ANSWER_VI
        state.ui_actions = [_action_card(cap) for cap in state.allowed_capabilities]
        state.selected_capability = None
        return state

    state.tool_decisions += 1
    capability = state.capability
    template = _ANSWER_TEMPLATES_VI[capability]
    phrased = _optional_phrase(state, model, template, purpose="tool")
    state.answer_vi = phrased or template
    state.ui_actions = [_action_card(cap) for cap in state.allowed_capabilities]
    state.selected_capability = capability
    state.evidence_refs = [f"capability:{capability}"]
    handle = (state.request.resource_handle or "").strip()
    if handle:
        state.evidence_refs.append(f"resource:{handle}")
    assert all(a.route_key == _ROUTE_KEYS[a.key] for a in state.ui_actions)
    assert all(a.label_vi == _LABELS_VI[a.key] for a in state.ui_actions)
    return state


def clarify_node(state: AgentGraphState) -> AgentGraphState:
    if state.refusal is not None or state.route != "clarify":
        return state
    if not state.answer_vi:
        state.answer_vi = _CLARIFY_ANSWER_VI
    state.ui_actions = [_action_card(cap) for cap in state.allowed_capabilities]
    state.selected_capability = None
    if not state.evidence_refs:
        state.evidence_refs = ["route:clarify"]
    return state


def output_guard(state: AgentGraphState) -> AgentGraphState:
    if state.status is TurnStatus.REFUSED:
        state.ui_actions = []
        state.selected_capability = None
        return state

    answer = state.answer_vi or _SAFE_OUTPUT_FALLBACK_VI
    if (
        _URL_PATTERN.search(answer)
        or _SQL_PATTERN.search(answer)
        or _EMAIL_PATTERN.search(answer)
        or _PHONE_PATTERN.search(answer)
    ):
        state.answer_vi = _SAFE_OUTPUT_FALLBACK_VI
    else:
        state.answer_vi = answer

    cleaned: List[UIAction] = []
    for action in state.ui_actions:
        if action.key in state.allowed_capabilities and action.key in CAPABILITY_REGISTRY:
            cleaned.append(_action_card(action.key))
    state.ui_actions = cleaned

    if state.selected_capability is not None:
        if (
            state.selected_capability not in state.allowed_capabilities
            or state.selected_capability not in CAPABILITY_REGISTRY
        ):
            state.selected_capability = None
    return state


def _grounded_answer_from_facts(facts: Mapping[str, Any]) -> str:
    parts: List[str] = []
    review_count = facts.get("review_case_count")
    total = facts.get("total_students")
    if isinstance(review_count, int) and isinstance(total, int):
        parts.append(
            f"Trên Overview hiện có {review_count} case trong hàng đợi rà soát "
            f"(trên {total} sinh viên trong phạm vi so sánh được)."
        )
    else:
        parts.append(
            "Trên Overview, trợ lý chỉ giải thích tín hiệu tổng hợp server đã cấp — "
            "không bịa số liệu ngoài context packet."
        )

    if facts.get("comparison_status") == "unavailable":
        parts.append(
            "So sánh với snapshot tuần trước chưa sẵn sàng (comparison_status=unavailable)."
        )

    limitations = facts.get("limitations") or []
    if isinstance(limitations, (list, tuple)) and limitations:
        joined = ", ".join(str(x) for x in limitations[:8])
        parts.append(f"Giới hạn dữ liệu: {joined}.")

    summary_state = facts.get("summary_state")
    if summary_state in ("stale", "empty", "error"):
        parts.append(
            f"Trạng thái tổng quan hiện là {summary_state}; "
            'không suy diễn thành "ổn định" khi thiếu hoặc cũ dữ liệu.'
        )
    else:
        parts.append(
            "Dữ liệu thiếu hoặc cũ được đánh dấu insufficient_data/stale, "
            'không suy diễn thành "ổn định".'
        )
    return " ".join(parts)


def _optional_phrase(
    state: AgentGraphState,
    model: Optional[TextModel],
    grounded: str,
    *,
    purpose: str,
) -> Optional[str]:
    if model is None or state.model_calls >= MAX_MODEL_CALLS:
        return None
    system = (
        _OVERVIEW_SYSTEM_PROMPT
        + "\n\n## Phrase turn\n"
        "Viết lại ngắn gọn bằng tiếng Việt trung lập từ grounded_draft và facts. "
        "Không thêm số liệu/URL/PII ngoài facts. Trả JSON "
        '{"answer_vi":"..."}.'
    )
    user = json.dumps(
        {
            "purpose": purpose,
            "grounded_draft": grounded,
            "facts": state.facts,
            "capability": state.capability,
        },
        ensure_ascii=False,
    )
    parsed, _fail_kind = _call_model_json(
        state,
        model,
        system=system,
        user=user,
        schema=_PHRASE_JSON_SCHEMA,
        name="overview_phrase",
    )
    if not parsed:
        return None
    text = parsed.get("answer_vi")
    if not isinstance(text, str) or not text.strip():
        return None
    return text.strip()


def _call_model_json(
    state: AgentGraphState,
    model: Optional[TextModel],
    *,
    system: str,
    user: str,
    schema: Dict[str, Any],
    name: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Return ``(payload, fail_kind)`` where fail_kind is unavailable|invalid|None."""
    if model is None or state.model_calls >= MAX_MODEL_CALLS:
        return None, "unavailable" if model is None else None
    state.model_calls += 1
    try:
        complete_json = getattr(model, "complete_json", None)
        if callable(complete_json):
            payload = complete_json(system=system, user=user, schema=schema, name=name)
        else:
            raw = model.complete(system=system, user=user)
            payload = json.loads(raw)
    except ModelUnavailable:
        return None, "unavailable"
    except (ValueError, TypeError, json.JSONDecodeError):
        return None, "invalid"
    if not isinstance(payload, dict):
        return None, "invalid"
    return payload, None


def run_overview_graph(
    request: AgentTurnRequest,
    principal: Principal,
    *,
    model: Optional[TextModel] = None,
    allowed_capabilities: Sequence[str],
    facts: Optional[Mapping[str, Any]] = None,
) -> AgentTurnResponse:
    """Execute the overview AgentGraph and return an AgentTurnResponse."""
    state = AgentGraphState(
        principal=principal,
        request=request,
        allowed_capabilities=tuple(allowed_capabilities),
    )

    input_guardrails(state)
    if state.refusal is not None:
        record_access_event(
            actor_id=principal.actor_id,
            role=principal.active_role,
            action=f"agent_turn_refused:{state.refusal.value}",
            resource_handle=f"surface:{request.surface}",
        )
        return _to_response(state)

    state.facts = build_context_packet(request, facts=facts)
    route_node(state, model)

    if state.route == "answer":
        answer_node(state, model)
    elif state.route == "tool":
        tool_node(state, model)
    else:
        clarify_node(state)

    output_guard(state)

    record_access_event(
        actor_id=principal.actor_id,
        role=principal.active_role,
        action="agent_turn:overview",
        resource_handle=(request.resource_handle or "").strip() or "surface:overview",
    )
    return _to_response(state)


def _to_response(state: AgentGraphState) -> AgentTurnResponse:
    return AgentTurnResponse(
        status=state.status,
        answer_vi=state.answer_vi or _SAFE_OUTPUT_FALLBACK_VI,
        evidence_refs=list(state.evidence_refs),
        ui_actions=list(state.ui_actions),
        refusal_reason=state.refusal,
        selected_capability=state.selected_capability,
    )
