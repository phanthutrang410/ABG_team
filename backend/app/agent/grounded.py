"""T02 grounded explanation runtime using the safe H11a context and FPT AI."""

from __future__ import annotations

import json
import re
from typing import Optional

from app.agent.fpt_client import ModelUnavailable, TextModel
from app.agent.schemas import AgentExplanation, AgentExplanationRequest, DraftMessage
from app.agent.stub import _UNAVAILABLE, explain as explain_stub
from app.contracts.integration import assert_no_forbidden_keys

_SYSTEM = """Bạn là trợ lý giải thích case rà soát bằng tiếng Việt trung lập.
Chỉ dùng đúng dữ kiện JSON được cấp. Không tính/đoán/tiết lộ điểm, xác suất hay trọng số;
không chẩn đoán hoặc suy đoán nguyên nhân cá nhân; không quyết định hay gửi liên hệ.
Trả duy nhất JSON: {\"answer_vi\": string, \"draft_body_vi\": string|null}.
Nếu intent explain_case thì draft_body_vi phải null. Nếu neutral_draft, bản nháp phải chờ con
người duyệt, không nhắc rủi ro/điểm/chẩn đoán."""

_FORBIDDEN_OUTPUT = re.compile(
    r"(?i)(\b\d+(?:[.,]\d+)?\s*%|điểm\s+rủi\s+ro|xác\s+suất|trọng\s+số|"
    r"trầm\s+cảm|tự\s+tử|dân\s+tộc|nhà\s+nghèo|đã\s+gửi|tôi\s+đã\s+gửi)"
)


def _model_payload(request: AgentExplanationRequest) -> str:
    case = request.context.case
    assert case is not None
    safe = {
        "intent": request.intent,
        "question": request.question,
        "review_priority_band": case.review_priority_band,
        "factor_codes": [factor.code for factor in case.contributing_factors],
        "coverage": {
            "n_valid_terms": case.coverage.n_valid_terms,
            "n_courses": case.coverage.n_courses,
            "status": case.coverage.status,
            "reason_codes": case.coverage.reason_codes,
        },
        "limitations": case.limitations,
    }
    assert_no_forbidden_keys(safe)
    return json.dumps(safe, ensure_ascii=False)


def _parse_model_json(raw: str, *, wants_draft: bool) -> tuple[str, Optional[str]]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ModelUnavailable("model output is not JSON") from exc
    if not isinstance(payload, dict) or set(payload) != {"answer_vi", "draft_body_vi"}:
        raise ModelUnavailable("model output shape is invalid")
    answer = payload["answer_vi"]
    draft = payload["draft_body_vi"]
    if not isinstance(answer, str) or not answer.strip():
        raise ModelUnavailable("model answer is empty")
    if wants_draft != isinstance(draft, str):
        raise ModelUnavailable("model draft does not match intent")
    if isinstance(draft, str) and not draft.strip():
        raise ModelUnavailable("model draft is empty")
    combined = f"{answer} {draft or ''}"
    if _FORBIDDEN_OUTPUT.search(combined):
        raise ModelUnavailable("model output violated grounding policy")
    return answer.strip(), draft.strip() if isinstance(draft, str) else None


def explain(request: AgentExplanationRequest, model: TextModel) -> AgentExplanation:
    """Run guardrails/fail-closed mapping, then ground the ready answer via FPT."""
    baseline = explain_stub(request)
    if baseline.status.value != "ok":
        return baseline

    try:
        raw = model.complete(system=_SYSTEM, user=_model_payload(request))
        answer, draft_body = _parse_model_json(
            raw, wants_draft=request.intent == "neutral_draft"
        )
    except ModelUnavailable:
        return _UNAVAILABLE

    # Facts, factor codes, limits and model version remain deterministic and
    # are never accepted from the LLM.
    return baseline.model_copy(
        update={
            "answer_vi": answer,
            "draft_message": (
                DraftMessage(body_vi=draft_body) if draft_body is not None else None
            ),
        }
    )
