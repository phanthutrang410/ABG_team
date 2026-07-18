"""H25 grounded explanation — structured plan + backend VI render (no raw question)."""

from __future__ import annotations

import json

from app.agent.model import ModelUnavailable, TextModel
from app.agent.schemas import AgentExplanation, AgentExplanationRequest, ExplanationStatus
from app.agent.stub import explain as explain_stub
from app.agent.vi_renderer import (
    parse_structured_plan,
    render_answer_vi,
    render_draft_message,
    validate_plan_against_context,
)
from app.contracts.integration import assert_no_forbidden_keys

_SYSTEM = """Bạn là trợ lý lập kế hoạch giải thích case rà soát.
Chỉ dùng đúng dữ kiện JSON được cấp. Không tính/đoán/tiết lộ điểm, xác suất hay trọng số;
không chẩn đoán hoặc suy đoán nguyên nhân cá nhân; không quyết định hay gửi liên hệ.
Trả duy nhất JSON với đúng các khóa:
{"template_key": string, "used_factor_codes": string[], "limitation_keys": string[],
 "draft_variant_key": string|null}.
template_key phải thuộc allowlist: explain_case→explain_review_priority;
neutral_draft→neutral_draft_ready.
used_factor_codes và limitation_keys chỉ được lấy từ JSON đã cấp (subset).
Với explain_case: draft_variant_key=null. Với neutral_draft: draft_variant_key=warm_checkin.
Không trả prose tiếng Việt — backend sẽ render."""

_MODEL_UNAVAILABLE = AgentExplanation(
    status=ExplanationStatus.UNAVAILABLE,
    answer_vi=(
        "Dịch vụ mô hình tạm thời không phản hồi hoặc trả kết quả không hợp lệ. "
        "Anh/chị vui lòng thử lại sau. Dữ liệu case vẫn dùng được cho thao tác rà soát "
        "của con người."
    ),
    limitations_vi=(
        "Lỗi nhà cung cấp mô hình — không phải kết luận về dữ liệu hay về sinh viên."
    ),
)


def _model_payload(request: AgentExplanationRequest) -> str:
    """Canonical provider payload — never includes raw question or identifiers."""
    case = request.context.case
    assert case is not None
    safe = {
        "intent": request.intent,
        "canonical_task": (
            "draft_neutral_checkin"
            if request.intent == "neutral_draft"
            else "explain_review_priority"
        ),
        "review_priority_band": case.review_priority_band,
        "factor_codes": [factor.code for factor in case.contributing_factors],
        "coverage": {
            "n_valid_terms": case.coverage.n_valid_terms,
            "n_courses": case.coverage.n_courses,
            "status": case.coverage.status,
            "reason_codes": case.coverage.reason_codes,
        },
        "limitations": case.limitations,
        "allowed_template_keys": (
            ["neutral_draft_ready"]
            if request.intent == "neutral_draft"
            else ["explain_review_priority"]
        ),
        "allowed_draft_variant_keys": (
            ["warm_checkin"] if request.intent == "neutral_draft" else []
        ),
    }
    assert_no_forbidden_keys(safe)
    assert "question" not in safe
    return json.dumps(safe, ensure_ascii=False)


def explain(request: AgentExplanationRequest, model: TextModel) -> AgentExplanation:
    """Run guardrails/fail-closed mapping, then ground via structured FPT plan."""
    baseline = explain_stub(request)
    if baseline.status.value != "ok":
        return baseline

    case = request.context.case
    assert case is not None

    try:
        raw = model.complete(system=_SYSTEM, user=_model_payload(request))
        plan = validate_plan_against_context(
            parse_structured_plan(raw),
            intent=request.intent,
            case=case,
        )
        answer = render_answer_vi(plan, case)
        draft = render_draft_message(plan, channel="copy")
        if request.intent == "neutral_draft" and draft is None:
            raise ModelUnavailable("neutral_draft produced no draft_message")
        if request.intent == "explain_case" and draft is not None:
            raise ModelUnavailable("explain_case must not produce draft_message")
    except ModelUnavailable:
        return _MODEL_UNAVAILABLE

    # Facts, factor codes, limits and model_version stay deterministic from case.
    return baseline.model_copy(
        update={
            "answer_vi": answer,
            "draft_message": draft,
        }
    )
