"""Overview surface — in-house bounded tool-routing DAG (no LangGraph).

Nodes (code-enforced): input_guardrails → build_context_packet → route_node →
answer|tool|clarify → output_guard. Caps: ≤1 model call, ≤1 tool decision.
``ui_actions`` are always backend-issued capability cards; the model never
emits URLs or raw tool payloads.

This is intentionally not an open-ended ReAct loop: there is no re-plan after
an observation, and user-facing prose is rendered deterministically by the
backend after the single structured route decision.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Mapping, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from app.agent.model import ModelUnavailable, TextModel
from app.agent.tracing import (
    redact_turn_inputs,
    redact_turn_outputs,
    trace_agent_run,
)
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

MAX_MODEL_CALLS = 1
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

_UNAVAILABLE_ANSWER_VI = (
    "Trợ lý tạm thời không kết nối được mô hình. Anh/chị vẫn có thể dùng các thẻ "
    "điều hướng bên dưới để mở báo cáo tổng quan, danh sách rà soát hoặc bản nháp thông báo."
)

_CLARIFY_ANSWER_VI = (
    "Anh/chị muốn xem báo cáo tổng quan, mở danh sách rà soát, hay soạn bản nháp "
    "thông báo cho GVCN? Tôi chỉ điều hướng trong các lựa chọn đã cho phép."
)

_GREETING_ANSWER_VI = (
    "Xin chào! Em là trợ lý EduSignal trên màn Overview — giúp anh/chị mở báo cáo "
    "tổng quan, danh sách rà soát, hoặc bản nháp thông báo cho GVCN. "
    "Anh/chị muốn xem phần nào?"
)

_OUT_OF_SCOPE_TOPIC_ANSWER_VI = (
    "Em không tra cứu thông tin cá nhân, quê quán hay tiểu sử của người cụ thể — "
    "ngoài phạm vi trợ lý Overview. Em chỉ hỗ trợ mở báo cáo tổng quan, danh sách "
    "rà soát, hoặc bản nháp thông báo GVCN. Anh/chị muốn xem phần nào?"
)

_SAFE_OUTPUT_FALLBACK_VI = (
    "Tôi chỉ có thể giải thích nội dung Overview đã được server cấp và điều hướng "
    "trong phạm vi cho phép — không trả URL/SQL hay nội dung ngoài phạm vi."
)

# Playful wake-up / hello / *assistant* identity — not third-party people.
_CHITCHAT_CORE = re.compile(
    r"(?is)("
    r"chào(\s+bạn)?|chao(\s+ban)?|xin\s+chào|xin\s+chao|\bhello\b|\bhi\b|\bhey\b|"
    r"thức\s*dậy|thuc\s*day|dậy\s*đi|day\s*di|"
    r"(^|[\s,;])(bạn|ban|mày|may|cậu|cau|em)\s+(là\s+|la\s+)?(ai|thằng\s+nào|thang\s+nao|cái\s+gì|cai\s+gi)|"
    r"giới\s+thiệu|gioi\s+thieu|"
    r"who\s+are\s+you"
    r")"
)
_TOOLISH_HINT = re.compile(
    r"(?is)(báo\s*cáo|rà\s*soát|ra\s*soat|mail|email|gvcn|danh\s*sách|danh\s*sach|"
    r"xuất|xuat|thông\s*báo|thong\s*bao|tóm\s*tắt|tom\s*tat|tín\s*hiệu|tin\s*hieu|"
    r"overview|dashboard|ngưỡng|nguong)"
)

# Third-party person / hometown / gossip — code-enforced before the model.
_OUT_OF_SCOPE_TOPIC = re.compile(
    r"(?is)("
    r"quê(\s+ quán)?|que(\s+quan)?|quê\s+quán|quê\s+ở|quê\s+o|"
    r"hải\s*phòng|hai\s*phong|"
    r"(thằng|thang|đứa|dua|ông|ong|cô|chi|chị|anh)\s+"
    r"[A-Za-zÀ-ỹĐđ]{2,}\s+(là\s+|la\s+)?(ai|thằng\s+nào|thang\s+nao|người\s+nào|nguoi\s+nao)|"
    r"(thằng|thang|đứa|dua)\s+nào\s+(quê|que)|"
    r"(ai|người\s+nào|nguoi\s+nao)\s+(quê|que)|"
    r"(tiểu\s*sử|tieu\s*su|profile\s+cá\s*nhân|thong\s*tin\s*cá\s*nhân|thông\s*tin\s*cá\s*nhân)|"
    r"(sđt|so\s*dien\s*thoai|số\s*điện\s*thoại|email\s+của|mssv\s+của)"
    r")"
)

_MACHINE_KEY_LEAK_PATTERN = re.compile(
    r"(?i)\b("
    r"comparison_status|aggregate_only|no_client_case_payload|"
    r"weekly_comparison_unavailable|server_packet_v1|context\s*packet|"
    r"summary_state|thread_summary|resource_handle|"
    r"insufficient_data|freshness"
    r")\b"
    r"|comparison_status\s*=\s*\w+"
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
    }
    if facts:
        for key, value in facts.items():
            if key == "thread_summary":
                continue
            packet[key] = value
    return packet


def input_guardrails(state: AgentGraphState) -> AgentGraphState:
    refusal = (
        _scan_forbidden(state.request.question)
        or _scan_forbidden(state.request.resource_handle)
    )
    if refusal is not None:
        state.refusal = refusal
        state.status = TurnStatus.REFUSED
        state.answer_vi = _REFUSAL_ANSWERS_VI[refusal]
        state.ui_actions = []
        state.selected_capability = None
        state.evidence_refs = []
    return state


def _is_chitchat(question: Optional[str]) -> bool:
    if not question:
        return False
    q = question.strip()
    if not q or len(q) > 160:
        return False
    if _is_out_of_scope_topic(q):
        return False
    if _TOOLISH_HINT.search(q):
        return False
    return _CHITCHAT_CORE.search(q) is not None


def _is_out_of_scope_topic(question: Optional[str]) -> bool:
    """Personal/third-party lookup is outside Overview navigation scope."""
    if not question:
        return False
    q = question.strip()
    if not q:
        return False
    return _OUT_OF_SCOPE_TOPIC.search(q) is not None


def _apply_out_of_scope_topic(state: AgentGraphState) -> AgentGraphState:
    state.route = "answer"
    state.refusal = TurnRefusalReason.SENSITIVE_DATA
    state.status = TurnStatus.REFUSED
    state.answer_vi = _OUT_OF_SCOPE_TOPIC_ANSWER_VI
    state.ui_actions = []
    state.selected_capability = None
    state.evidence_refs = []
    state.capability = None
    return state


def _user_facing_facts(facts: Mapping[str, Any]) -> Dict[str, Any]:
    """Projection for the model — human labels only, no machine codes."""
    review_count = facts.get("review_case_count")
    total = facts.get("total_students")
    out: Dict[str, Any] = {
        "has_counts": isinstance(review_count, int) and isinstance(total, int),
        "review_case_count": review_count if isinstance(review_count, int) else None,
        "total_students": total if isinstance(total, int) else None,
        "new_signal_count": facts.get("new_signal_count")
        if isinstance(facts.get("new_signal_count"), int)
        else None,
        "weekly_comparison_ready": facts.get("comparison_status") == "ready",
        "summary_ok": facts.get("summary_state") == "ok",
    }
    return out


def route_node(state: AgentGraphState, model: Optional[TextModel]) -> AgentGraphState:
    """One structured route call → answer | tool | clarify."""
    if state.refusal is not None:
        return state

    if _is_out_of_scope_topic(state.request.question):
        return _apply_out_of_scope_topic(state)

    if not (state.request.question or "").strip():
        state.route = "clarify"
        state.answer_vi = _CLARIFY_ANSWER_VI
        state.ui_actions = [_action_card(cap) for cap in state.allowed_capabilities]
        state.selected_capability = None
        state.evidence_refs = ["route:cards_only"]
        return state

    if _is_chitchat(state.request.question):
        state.route = "answer"
        state.answer_vi = _GREETING_ANSWER_VI
        state.ui_actions = [_action_card(cap) for cap in state.allowed_capabilities]
        state.selected_capability = None
        state.evidence_refs = ["route:chitchat"]
        return state

    user_payload = {
        "question": state.request.question,
        "allowed_capabilities": list(state.allowed_capabilities),
        "facts": _user_facing_facts(state.facts),
        "locale": state.request.locale,
    }
    system = (
        _OVERVIEW_SYSTEM_PROMPT
        + "\n\n## Route turn\n"
        "Trả đúng một JSON object theo schema: "
        '{"intent":"answer|tool|clarify","capability_key":string|null,"missing_fields":string[]}. '
        "Chỉ chọn capability_key ∈ allowed_capabilities khi intent=tool. "
        "Chào hỏi / hỏi danh tính trợ lý → intent=answer. "
        "Hỏi người cụ thể / quê quán / tiểu sử → không bịa; backend đã chặn "
        "(nếu lọt tới đây thì intent=clarify, missing_fields=[]). "
        "Không bịa số ngoài facts. Không lộ tên field máy. "
        "missing_fields chỉ là mã ngắn (vd. which_destination), không viết câu dài."
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
        if model is None or fail_kind in ("unavailable", "invalid"):
            state.status = TurnStatus.UNAVAILABLE
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
        state.status = TurnStatus.UNAVAILABLE
        state.answer_vi = _UNAVAILABLE_ANSWER_VI
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
            state.status = TurnStatus.UNAVAILABLE
            state.capability = None
            state.answer_vi = _UNAVAILABLE_ANSWER_VI
            state.ui_actions = [_action_card(cap) for cap in state.allowed_capabilities]
            state.selected_capability = None
            state.evidence_refs = ["route:invalid_capability"]
            return state
    elif intent == "clarify":
        # Never echo model missing_fields prose (can leak internal reasoning).
        state.answer_vi = _CLARIFY_ANSWER_VI
    return state


def answer_node(state: AgentGraphState, model: Optional[TextModel]) -> AgentGraphState:
    if state.refusal is not None or state.route != "answer":
        return state

    # Chitchat already filled a fixed answer — skip the grounded summary.
    if state.evidence_refs == ["route:chitchat"] and state.answer_vi:
        state.ui_actions = [_action_card(cap) for cap in state.allowed_capabilities]
        state.selected_capability = None
        return state

    grounded = _grounded_answer_from_facts(state.facts)
    # The model only routes. Backend-rendered prose prevents a second call from
    # adding unsupported numbers, diagnoses, machine keys, or personal causes.
    _ = model
    state.answer_vi = grounded
    state.ui_actions = [_action_card(cap) for cap in state.allowed_capabilities]
    state.selected_capability = None
    state.evidence_refs = ["route:answer"]
    evidence_ref = state.facts.get("evidence_ref")
    if isinstance(evidence_ref, str) and evidence_ref:
        state.evidence_refs.append(evidence_ref)
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
    _ = model
    state.answer_vi = template
    state.ui_actions = [_action_card(cap) for cap in state.allowed_capabilities]
    state.selected_capability = capability
    state.evidence_refs = [f"capability:{capability}"]
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
        or _MACHINE_KEY_LEAK_PATTERN.search(answer)
    ):
        # Prefer friendly grounded copy over leaking internal field names.
        if state.evidence_refs in (["route:chitchat"], ["route:out_of_scope_topic"]):
            state.answer_vi = (
                _GREETING_ANSWER_VI
                if state.evidence_refs == ["route:chitchat"]
                else _OUT_OF_SCOPE_TOPIC_ANSWER_VI
            )
        else:
            state.answer_vi = _grounded_answer_from_facts(state.facts)
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
    """User-facing VI only — never echo machine field names or limitation codes."""
    parts: List[str] = []
    review_count = facts.get("review_case_count")
    total = facts.get("total_students")
    if isinstance(review_count, int) and isinstance(total, int):
        parts.append(
            f"Trên Overview hiện có {review_count} case trong danh sách tổng quan "
            f"(trên {total} sinh viên trong phạm vi được cấp)."
        )
    elif isinstance(review_count, int):
        parts.append(f"Báo cáo tổng quan hiện có {review_count} case đang mở trong phạm vi được cấp.")
    else:
        parts.append(
            "Em đang hỗ trợ trên màn Overview. Các con số chi tiết (tổng sinh viên, "
            "số case trong danh sách tổng quan) sẽ hiện khi dữ liệu tổng hợp đã sẵn sàng — "
            "em không tự bịa số."
        )

    if facts.get("comparison_status") == "unavailable":
        parts.append("So sánh với tuần trước hiện chưa sẵn sàng.")

    summary_state = facts.get("summary_state")
    if summary_state == "stale":
        parts.append("Dữ liệu tổng quan đang cũ hơn kỳ mong đợi; chưa kết luận là ổn định.")
    elif summary_state == "empty":
        parts.append("Chưa có tín hiệu tổng quan để tóm tắt.")
    elif summary_state == "error":
        parts.append("Tổng quan tạm thời không tải được; anh/chị thử lại hoặc mở thẻ bên dưới.")

    parts.append(
        "Anh/chị có thể mở báo cáo tổng quan, danh sách rà soát, hoặc bản nháp "
        "thông báo GVCN bằng các thẻ bên dưới."
    )
    return " ".join(parts)


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


def _emit_phase(on_phase: Optional[Callable[[str], None]], phase: str) -> None:
    if on_phase is not None:
        on_phase(phase)


@trace_agent_run(
    "overview_agent_graph",
    process_inputs=redact_turn_inputs,
    process_outputs=redact_turn_outputs,
)
def run_overview_graph(
    request: AgentTurnRequest,
    principal: Principal,
    *,
    model: Optional[TextModel] = None,
    allowed_capabilities: Sequence[str],
    facts: Optional[Mapping[str, Any]] = None,
    on_phase: Optional[Callable[[str], None]] = None,
    guardrails_phase_emitted: bool = False,
    db: Optional[Session] = None,
) -> AgentTurnResponse:
    """Execute the overview AgentGraph and return an AgentTurnResponse."""
    state = AgentGraphState(
        principal=principal,
        request=request,
        allowed_capabilities=tuple(allowed_capabilities),
    )

    if not guardrails_phase_emitted:
        _emit_phase(on_phase, "guardrails")
    # Always re-run the pure guard for direct callers and defense in depth;
    # the flag suppresses only a duplicate SSE phase, never the safety check.
    input_guardrails(state)
    if state.refusal is not None:
        record_access_event(
            actor_id=principal.actor_id,
            role=principal.active_role,
            action=f"agent_turn_refused:{state.refusal.value}",
            resource_handle=f"surface:{request.surface}",
            decision="denied",
            db=db,
        )
        return _to_response(state)

    _emit_phase(on_phase, "context")
    state.facts = build_context_packet(request, facts=facts)
    _emit_phase(on_phase, "route")
    route_node(state, model)

    if state.route == "answer":
        _emit_phase(on_phase, "answer")
        answer_node(state, model)
    elif state.route == "tool":
        _emit_phase(on_phase, "tool")
        tool_node(state, model)
    else:
        _emit_phase(on_phase, "clarify")
        clarify_node(state)

    _emit_phase(on_phase, "output_guard")
    output_guard(state)

    if state.status is TurnStatus.REFUSED:
        refusal = state.refusal or TurnRefusalReason.OUT_OF_SCOPE
        record_access_event(
            actor_id=principal.actor_id,
            role=principal.active_role,
            action=f"agent_turn_refused:{refusal.value}",
            resource_handle="surface:overview",
            decision="denied",
            db=db,
        )
    else:
        record_access_event(
            actor_id=principal.actor_id,
            role=principal.active_role,
            action="agent_turn:overview",
            # Client resource_handle is not evidence until a trusted loader resolves it.
            resource_handle="surface:overview",
            db=db,
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
