"""Canonical VI catalog + context-bound structured-plan validation (H25).

The LLM only picks allowlisted template / draft keys and factor/limitation
refs. Backend renders Vietnamese copy from this catalog — prose is never
accepted from the model.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List, Literal, Optional, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.agent.model import ModelUnavailable
from app.agent.schemas import DraftMessage
from app.contracts.integration import AgentIntent
from app.contracts.review_case import ReviewCase

DraftChannel = Literal["copy", "mailto"]

TEMPLATE_ALLOWLIST: Dict[AgentIntent, FrozenSet[str]] = {
    "explain_case": frozenset({"explain_review_priority"}),
    "neutral_draft": frozenset({"neutral_draft_ready"}),
}

DRAFT_VARIANT_ALLOWLIST: FrozenSet[str] = frozenset({"warm_checkin"})

_FACTOR_LABELS_VI = {
    "grade_trend_declining": "xu hướng điểm trung bình theo học kỳ giảm",
    "grade_volatility_high": "điểm dao động mạnh giữa các học kỳ",
}

_BAND_LABELS_VI = {
    "uu_tien_som": "ưu tiên xem xét sớm",
    "can_ra_soat": "cần rà soát",
}

_LIMITATION_COPY_VI = {
    "attendance_source_unapproved": (
        "Chưa có nguồn điểm danh đã được phê duyệt. Hệ thống không kết luận về chuyên cần."
    ),
    "copy.partial_term_only": (
        "Chỉ có tín hiệu điểm theo học kỳ; nhánh chuyên cần chưa sẵn sàng."
    ),
    "grade_coverage_insufficient": (
        "Chưa đủ học kỳ hợp lệ để tính xu hướng điểm."
    ),
    "single_term": "Mới có một học kỳ hợp lệ nên chưa tính được xu hướng.",
}

_DRAFT_BODIES_VI = {
    "warm_checkin": (
        "Chào em, thời gian gần đây thầy/cô thấy việc học của em có một vài thay đổi. "
        "Không có gì nghiêm trọng cả — thầy/cô chỉ muốn hỏi thăm xem em có đang gặp "
        "khó khăn gì cần hỗ trợ không. Nếu tiện, mình sắp xếp một buổi trao đổi ngắn nhé."
    ),
}


class StructuredPlan(BaseModel):
    """Provider output shape — keys only; no free-form prose."""

    model_config = ConfigDict(extra="forbid")

    template_key: str = Field(min_length=1)
    used_factor_codes: List[str] = Field(default_factory=list)
    limitation_keys: List[str] = Field(default_factory=list)
    draft_variant_key: Optional[str] = None

    @field_validator("used_factor_codes", "limitation_keys")
    @classmethod
    def _no_blank_items(cls, value: List[str]) -> List[str]:
        if any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError("plan list items must be non-empty strings")
        return value


def parse_structured_plan(raw: str) -> StructuredPlan:
    try:
        return StructuredPlan.model_validate_json(raw)
    except Exception as exc:  # noqa: BLE001 — map all parse/shape errors
        raise ModelUnavailable("model output is not a valid structured plan") from exc


def validate_plan_against_context(
    plan: StructuredPlan,
    *,
    intent: AgentIntent,
    case: ReviewCase,
) -> StructuredPlan:
    allowed_templates = TEMPLATE_ALLOWLIST.get(intent, frozenset())
    if plan.template_key not in allowed_templates:
        raise ModelUnavailable("template_key is not allowlisted for intent")

    allowed_factors: Set[str] = {factor.code for factor in case.contributing_factors}
    if not set(plan.used_factor_codes).issubset(allowed_factors):
        raise ModelUnavailable("used_factor_codes not subset of context factors")

    allowed_limits = set(case.limitations)
    if not set(plan.limitation_keys).issubset(allowed_limits):
        raise ModelUnavailable("limitation_keys not subset of context limitations")

    if intent == "explain_case":
        if plan.draft_variant_key is not None:
            raise ModelUnavailable("draft_variant_key must be null for explain_case")
    else:
        if plan.draft_variant_key is None:
            raise ModelUnavailable("neutral_draft requires draft_variant_key")
        if plan.draft_variant_key not in DRAFT_VARIANT_ALLOWLIST:
            raise ModelUnavailable("draft_variant_key is not allowlisted")

    return plan


def _factor_phrase(codes: List[str], case: ReviewCase) -> str:
    selected = codes or [factor.code for factor in case.contributing_factors]
    labels = [
        _FACTOR_LABELS_VI.get(code, f"tín hiệu {code}") for code in selected
    ]
    return "; ".join(labels) if labels else "các thay đổi trong dữ liệu học vụ"


def render_answer_vi(plan: StructuredPlan, case: ReviewCase) -> str:
    band_label = _BAND_LABELS_VI.get(case.review_priority_band or "", "chưa xếp mức")
    reasons = _factor_phrase(plan.used_factor_codes, case)

    if plan.template_key == "explain_review_priority":
        return (
            f"Case này được đưa vào danh sách rà soát vì: {reasons}. "
            f"Mức ưu tiên hiện tại: {band_label}. Đây là tín hiệu để con người xem xét, "
            "không phải kết luận về sinh viên."
        )
    if plan.template_key == "neutral_draft_ready":
        return (
            "Tôi không thể tự gửi — việc liên hệ do con người quyết định và thực hiện. "
            "Dưới đây là bản nháp hỏi thăm trung lập để anh/chị xem lại, chỉnh sửa và "
            "tự gửi nếu thấy phù hợp."
        )
    raise ModelUnavailable("unknown template_key for render")


def render_draft_message(
    plan: StructuredPlan,
    *,
    channel: str = "copy",
) -> Optional[DraftMessage]:
    if plan.draft_variant_key is None:
        return None
    if channel not in ("copy", "mailto"):
        raise ModelUnavailable("draft channel must be copy or mailto")
    body = _DRAFT_BODIES_VI.get(plan.draft_variant_key)
    if body is None:
        raise ModelUnavailable("draft_variant_key has no catalog body")
    safe_channel: DraftChannel = "mailto" if channel == "mailto" else "copy"
    return DraftMessage(
        body_vi=body,
        requires_human_approval=True,
        channel=safe_channel,
    )


def limitation_text(keys: List[str]) -> str:
    parts = [_LIMITATION_COPY_VI[k] for k in keys if k in _LIMITATION_COPY_VI]
    parts.append("Hệ thống không suy ra nguyên nhân cá nhân từ các tín hiệu này.")
    return " ".join(parts)
