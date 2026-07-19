"""Deterministic explanation-agent stub (T01) — no LLM, fixtures only.

Answers are assembled purely from the H11a ``AgentContextResponse`` the stub
was handed: factor codes, coverage counts and case fields. Nothing else exists
for it to draw on, so it cannot invent scores, causes or attendance data.

T02 replaces the answer assembly with a grounded LLM call (FPT API) but keeps
the same flow: guardrail classification first, context-status mapping second,
grounded assembly last. Final on-screen copy is H12a's concern; the stub emits
neutral Vietnamese that follows the same vocabulary.
"""

from __future__ import annotations

from typing import List, Optional

from app.agent.guardrails import (
    REFUSAL_ANSWERS_VI,
    REFUSAL_LIMITATIONS_VI,
    classify_question,
)
from app.agent.schemas import (
    AgentExplanation,
    AgentExplanationRequest,
    DraftMessage,
    ExplanationStatus,
    GroundedFact,
    RefusalReason,
)
from app.contracts.review_case import ReviewCase

#: Neutral VI labels for known factor codes (Data-ML §4 features). Unknown
#: codes fall back to the raw code — never to an invented explanation.
_FACTOR_LABELS_VI = {
    "grade_trend_declining": "điểm trung bình giữa hai kỳ giảm",
    "grade_volatility_high": "điểm dao động mạnh giữa các học kỳ",
    "grade_volatility_elevated": "độ phân tán điểm học phần cao",
    "gpa_below_target": "điểm trung bình kỳ gần nhất thấp hơn ngưỡng hỗ trợ",
    "failed_credits_elevated": "tín chỉ môn không đạt ở mức cao",
}

_BAND_LABELS_VI = {
    "uu_tien_som": "ưu tiên xem xét sớm",
    "can_ra_soat": "cần rà soát",
}

#: H12a copy keys (Data-ML §6) the stub can render for limitations.
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

_DRAFT_BODY_VI = (
    "Chào em, thời gian gần đây thầy/cô thấy việc học của em có một vài thay đổi. "
    "Không có gì nghiêm trọng cả — thầy/cô chỉ muốn hỏi thăm xem em có đang gặp "
    "khó khăn gì cần hỗ trợ không. Nếu tiện, mình sắp xếp một buổi trao đổi ngắn nhé."
)


def _refusal(reason: RefusalReason, model_version: Optional[str]) -> AgentExplanation:
    return AgentExplanation(
        status=ExplanationStatus.REFUSED,
        answer_vi=REFUSAL_ANSWERS_VI[reason],
        limitations_vi=REFUSAL_LIMITATIONS_VI[reason],
        refusal_reason=reason,
        model_version=model_version,
    )


def _limitation_text(keys: List[str]) -> str:
    parts = [_LIMITATION_COPY_VI[k] for k in keys if k in _LIMITATION_COPY_VI]
    parts.append("Hệ thống không suy ra nguyên nhân cá nhân từ các tín hiệu này.")
    return " ".join(parts)


def _grounded_facts(case: ReviewCase) -> List[GroundedFact]:
    facts: List[GroundedFact] = [
        GroundedFact(
            statement_vi=f"Model ghi nhận: {_FACTOR_LABELS_VI.get(f.code, f'tín hiệu {f.code}')}.",
            source="model_factor",
            ref=f.code,
        )
        for f in case.contributing_factors
    ]
    facts.append(
        GroundedFact(
            statement_vi=(
                f"Dữ liệu có {case.coverage.n_valid_terms} học kỳ hợp lệ "
                f"trên {case.coverage.n_courses} học phần."
            ),
            source="coverage",
            ref=None,
        )
    )
    facts.append(
        GroundedFact(
            statement_vi=f"Case đang ở trạng thái {case.case_state}.",
            source="case_field",
            ref="case_state",
        )
    )
    return facts


def _explain_ready(request: AgentExplanationRequest, case: ReviewCase) -> AgentExplanation:
    factor_labels = [
        _FACTOR_LABELS_VI.get(f.code, f"tín hiệu {f.code}") for f in case.contributing_factors
    ]
    band_label = _BAND_LABELS_VI.get(case.review_priority_band or "", "chưa xếp mức")

    if request.intent == "neutral_draft":
        answer = (
            "Tôi không thể tự gửi — việc liên hệ do con người quyết định và thực hiện. "
            "Dưới đây là bản nháp hỏi thăm trung lập để anh/chị xem lại, chỉnh sửa và "
            "tự gửi nếu thấy phù hợp."
        )
        draft: Optional[DraftMessage] = DraftMessage(body_vi=_DRAFT_BODY_VI)
    else:
        reasons = "; ".join(factor_labels) if factor_labels else "các thay đổi trong dữ liệu học vụ"
        answer = (
            f"Case này được đưa vào danh sách rà soát vì: {reasons}. "
            f"Mức ưu tiên hiện tại: {band_label}. Đây là tín hiệu để con người xem xét, "
            "không phải kết luận về sinh viên."
        )
        draft = None

    return AgentExplanation(
        status=ExplanationStatus.OK,
        answer_vi=answer,
        grounded_facts=_grounded_facts(case),
        model_factors_used=[f.code for f in case.contributing_factors],
        limitation_keys=list(case.limitations),
        limitations_vi=_limitation_text(list(case.limitations)),
        draft_message=draft,
        model_version=case.model_version,
    )


def _explain_insufficient(case: Optional[ReviewCase]) -> AgentExplanation:
    keys = list(case.limitations) if case else []
    facts: List[GroundedFact] = []
    if case is not None:
        facts.append(
            GroundedFact(
                statement_vi=(
                    f"Chỉ có {case.coverage.n_valid_terms} học kỳ hợp lệ; mức ưu tiên "
                    "được để trống thay vì suy đoán."
                ),
                source="coverage",
                ref=None,
            )
        )
    return AgentExplanation(
        status=ExplanationStatus.INSUFFICIENT_DATA,
        answer_vi=(
            "Chưa đủ dữ liệu để giải thích case này. Hệ thống chọn im lặng có giải thích "
            "thay vì đưa ra nhận định thiếu căn cứ — thiếu dữ liệu không có nghĩa là mọi "
            "việc bình thường, chỉ là chưa đủ căn cứ để nói."
        ),
        grounded_facts=facts,
        limitation_keys=keys,
        limitations_vi=_limitation_text(keys),
        model_version=case.model_version if case else None,
    )


_UNAVAILABLE = AgentExplanation(
    status=ExplanationStatus.UNAVAILABLE,
    answer_vi=(
        "Hệ thống tạm thời không truy cập được dữ liệu case (nguồn không phản hồi). "
        "Tôi không thể giải thích hay suy đoán khi chưa có dữ liệu — anh/chị vui lòng "
        "thử lại sau. Các thao tác rà soát của con người vẫn dùng được bình thường."
    ),
    limitations_vi="Lỗi upstream/timeout — không phải kết luận về dữ liệu hay về sinh viên.",
)

_EMPTY = AgentExplanation(
    status=ExplanationStatus.REFUSED,
    answer_vi=(
        "Không có case nào trong phạm vi truy cập của anh/chị — yêu cầu này nằm "
        "ngoài phạm vi dữ liệu tôi được cấp."
    ),
    limitations_vi="Agent chỉ trả lời trong phạm vi case đã được RBAC cấp (Ethics §3).",
    refusal_reason=RefusalReason.OUT_OF_SCOPE_DATA,
)


def explain(request: AgentExplanationRequest) -> AgentExplanation:
    """Produce a contract-valid AgentExplanation without any model call."""
    # 1. Guardrails first — a forbidden ask is refused regardless of data state.
    case = request.context.case
    model_version = case.model_version if case else None
    reason = classify_question(request.question)
    if reason is not None:
        return _refusal(reason, model_version)

    # 2. Fail-closed mapping of the upstream context status (doc 08 §2.3).
    status = request.context.status
    if status == "unavailable":
        return _UNAVAILABLE
    if status == "empty":
        return _EMPTY
    if status == "refused":
        problem = request.context.problem
        upstream = set(problem.reason_codes) if problem else set()
        mapped = (
            RefusalReason.REVEAL_RAW_SCORE
            if "score_request" in upstream
            else RefusalReason.OUT_OF_SCOPE_DATA
        )
        return _refusal(mapped, model_version)
    if status == "insufficient_data" or case is None:
        return _explain_insufficient(case)

    # 3. Grounded assembly from the safe case only.
    return _explain_ready(request, case)
