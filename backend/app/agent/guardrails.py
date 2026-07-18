"""Rule-based guardrail classifier for the explanation agent (T01/T02).

Classifies a reviewer question against the seven refusal categories
(PRD §5.4, Ethics §8) BEFORE any model call. Deterministic on purpose:
- T01 uses it as the whole "mock model" for the stub;
- T02 keeps it as a pre-LLM safety gate (defence in depth — a live model
  never even sees a question we already know must be refused).

Matching is lowercase-substring over Vietnamese keywords. Order matters:
the first matching category wins (e.g. "tự tính lại điểm rủi ro" must hit
INVENT_SCORE before the generic score words hit REVEAL_RAW_SCORE).
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence, Tuple

from app.agent.schemas import RefusalReason

#: (reason, keywords) — evaluated in order; first hit wins.
_RULES: Sequence[Tuple[RefusalReason, Tuple[str, ...]]] = (
    (
        RefusalReason.DIAGNOSE_HEALTH,
        ("trầm cảm", "tự tử", "khủng hoảng tâm lý", "bệnh tâm lý", "chẩn đoán"),
    ),
    (
        RefusalReason.INVENT_SCORE,
        ("tự tính", "tính lại điểm", "tính điểm rủi ro", "tạo điểm"),
    ),
    (
        RefusalReason.REVEAL_RAW_SCORE,
        ("phần trăm", "%", "xác suất", "điểm rủi ro", "raw score", "model score", "trọng số"),
    ),
    (
        RefusalReason.SPECULATE_CAUSE,
        ("nhà nghèo", "nghèo", "dân tộc", "hoàn cảnh gia đình", "vì gia đình", "bố mẹ"),
    ),
    (
        RefusalReason.AUTO_SEND,
        ("gửi email", "gửi tin", "gửi cho", "gửi hộ", "gửi luôn", "nhắn cho em ấy hộ", "gửi giúp"),
    ),
    (
        RefusalReason.DECIDE_ACTION,
        ("kỷ luật", "quyết định luôn", "chuyển em này lên", "đổi trạng thái", "đình chỉ"),
    ),
    (
        RefusalReason.OUT_OF_SCOPE_DATA,
        ("mssv", "số điện thoại", "sđt", "địa chỉ nhà", "phụ huynh", "email của", "ngày sinh"),
    ),
)

#: Neutral Vietnamese refusal answers — no diagnosis, no numbers, no blame.
#: Each names the boundary AND points at the correct path (care, not punish).
REFUSAL_ANSWERS_VI: Dict[RefusalReason, str] = {
    RefusalReason.DIAGNOSE_HEALTH: (
        "Tôi không thể chẩn đoán tình trạng tâm lý của sinh viên. Tôi chỉ giải thích "
        "các tín hiệu học vụ có sẵn và mức ưu tiên rà soát do model cung cấp. Việc tìm "
        "hiểu nguyên nhân và hỗ trợ là do con người thực hiện qua tiếp xúc trực tiếp."
    ),
    RefusalReason.INVENT_SCORE: (
        "Tôi không tính điểm hay tạo mức ưu tiên — việc đó thuộc về model đã được "
        "kiểm định, không thuộc phạm vi của trợ lý giải thích. Tôi chỉ có thể diễn "
        "giải các yếu tố mà model/API đã trả về cho case này."
    ),
    RefusalReason.REVEAL_RAW_SCORE: (
        "Tôi không thể cung cấp con số thô hay ước lượng khả năng bỏ học của một "
        "sinh viên. Hệ thống chỉ công bố mức ưu tiên rà soát cùng các yếu tố đóng "
        "góp — đây là tín hiệu hỗ trợ con người, không phải kết luận."
    ),
    RefusalReason.SPECULATE_CAUSE: (
        "Tôi không suy đoán về hoàn cảnh kinh tế, dân tộc, gia đình hay nguyên nhân "
        "cá nhân — các thông tin này không có trong dữ liệu được cấp và việc suy đoán "
        "có thể gây thiên lệch. Tôi chỉ nêu tín hiệu học vụ có thể kiểm chứng."
    ),
    RefusalReason.AUTO_SEND: (
        "Tôi không thể tự gửi email hay tin nhắn cho sinh viên — mọi liên hệ phải do "
        "con người quyết định và thực hiện. Nếu cần, tôi có thể soạn một bản nháp "
        "hỏi thăm trung lập để anh/chị xem lại và tự gửi."
    ),
    RefusalReason.DECIDE_ACTION: (
        "Tôi không thể quyết định việc liên hệ, bàn giao hay bất kỳ hình thức xử lý "
        "nào — con người quyết định toàn bộ các bước này. Hệ thống được thiết kế để "
        "hỗ trợ sự quan tâm, không phải để xử phạt."
    ),
    RefusalReason.OUT_OF_SCOPE_DATA: (
        "Thông tin này nằm ngoài phạm vi dữ liệu tôi được cấp — tôi chỉ nhìn thấy mã "
        "định danh ẩn danh và các tín hiệu học vụ tổng hợp, không có thông tin danh "
        "tính hay liên hệ cá nhân."
    ),
}

#: Refusal-side limitation notes (giới hạn) per category.
REFUSAL_LIMITATIONS_VI: Dict[RefusalReason, str] = {
    RefusalReason.DIAGNOSE_HEALTH: "Chẩn đoán sức khỏe tâm thần nằm ngoài phạm vi cho phép (Ethics §8).",
    RefusalReason.INVENT_SCORE: "LLM không nằm trong đường tính điểm (FR-04).",
    RefusalReason.REVEAL_RAW_SCORE: "Raw score/xác suất không thuộc public surface (Data-ML §4).",
    RefusalReason.SPECULATE_CAUSE: "Thuộc tính nhóm/hoàn cảnh không có trong agent context (Data-ML §6).",
    RefusalReason.AUTO_SEND: "Agent chỉ soạn nháp; con người duyệt và gửi (Ethics §4).",
    RefusalReason.DECIDE_ACTION: "Agent không được transition case (H06b).",
    RefusalReason.OUT_OF_SCOPE_DATA: "PII/danh tính thuộc FORBIDDEN_PUBLIC_FIELDS (H11a §2.1).",
}


def classify_question(question: str) -> Optional[RefusalReason]:
    """Return the refusal category a question falls into, or None if benign.

    First matching rule wins; matching is case-insensitive substring search.
    """
    lowered = question.lower()
    for reason, keywords in _RULES:
        if any(keyword in lowered for keyword in keywords):
            return reason
    return None
