/**
 * Runtime privacy/care copy — Data-ML §6 (H12a).
 * Export is reusable for UI and later agent grounding (T02).
 * Do not invent H12a keys here; amend Data-ML §6 first.
 *
 * H12b banner/asset keys below are separate from reason-code copy.
 */

export const COPY = {
  "copy.attendance_source_unapproved":
    "Chưa có nguồn điểm danh đã được phê duyệt. Hệ thống không kết luận về chuyên cần.",
  "copy.fairness_no_approved_audit_attribute":
    "Chưa có thuộc tính kiểm toán công bằng đã được phê duyệt. Không công bố metric theo nhóm.",
  "copy.fairness_insufficient_group_data":
    "Cỡ mẫu nhóm chưa đủ để công bố metric công bằng.",
  "copy.partial_term_only":
    "Chỉ có tín hiệu điểm theo học kỳ; nhánh chuyên cần chưa sẵn sàng.",
} as const;

export type CopyKey = keyof typeof COPY;

/** Machine reason_code → copy key (Data-ML §§3, 6). */
export const REASON_CODE_TO_COPY_KEY = {
  attendance_source_unapproved: "copy.attendance_source_unapproved",
  no_approved_audit_attribute: "copy.fairness_no_approved_audit_attribute",
  insufficient_group_data: "copy.fairness_insufficient_group_data",
  /** Term-only evidence / attendance branch not ready (Data-ML §6). */
  partial_term_only: "copy.partial_term_only",
} as const satisfies Record<string, CopyKey>;

export type ReasonCodeWithCopy = keyof typeof REASON_CODE_TO_COPY_KEY;

export function getCopy(key: CopyKey): string {
  return COPY[key];
}

/** Resolve VI copy for a known reason_code; undefined if unmapped. */
export function copyForReasonCode(reasonCode: string): string | undefined {
  const key = REASON_CODE_TO_COPY_KEY[reasonCode as ReasonCodeWithCopy];
  return key ? COPY[key] : undefined;
}

/** Deduped VI strings for a list of reason_codes (order preserved). */
export function copyForReasonCodes(reasonCodes: readonly string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const code of reasonCodes) {
    const text = copyForReasonCode(code);
    if (text && !seen.has(text)) {
      seen.add(text);
      out.push(text);
    }
  }
  return out;
}

/**
 * H12b — Scope banner + asset claim strings (PRD §§2,4,9; Ethics §4).
 * Attendance-over-time = MVP; forecast/fusion = research/blocked.
 * Not Data-ML §6 reason keys — do not map via reason_code.
 */
export const BANNER_COPY = {
  "banner.mvp_scope_title": "Phạm vi MVP",
  "banner.mvp_scope_body":
    "Silent Shield tạo tín hiệu cần rà soát từ điểm theo học kỳ và điểm danh theo thời gian (khi có nguồn đã duyệt). Con người duyệt trước mọi bàn giao. Forecasting / gated fusion điểm danh là hướng nghiên cứu bị chặn — chưa ship trong MVP.",
  "banner.attendance_mvp":
    "Điểm danh theo thời gian thuộc MVP. Thiếu nguồn đã duyệt → insufficient_data trên nhánh chuyên cần; không đẩy ra Post-MVP và không tạo chuỗi giả.",
  "banner.forecast_research_blocked":
    "Forecasting và fusion điểm danh (hybrid) = research / blocked tới sau submission — không tuyên bố đã triển khai.",
} as const;

export type BannerCopyKey = keyof typeof BANNER_COPY;

export function getBannerCopy(key: BannerCopyKey): string {
  return BANNER_COPY[key];
}

/** Short claim lines for slides / mô tả (Hạ Giang D1). Allowed = true. */
export const ASSET_CLAIMS = [
  {
    id: "mvp-signals",
    allowed: true,
    claim:
      "MVP: tín hiệu từ điểm theo học kỳ + điểm danh theo thời gian (nguồn đã duyệt/pseudonymize).",
  },
  {
    id: "human-review",
    allowed: true,
    claim:
      "Con người phê duyệt / loại / hoãn trước khi bàn giao; không kỷ luật tự động.",
  },
  {
    id: "attendance-mvp-insufficient",
    allowed: true,
    claim:
      "Điểm danh theo thời gian = MVP; thiếu nguồn H15 → insufficient_data (không gọi là Post-MVP).",
  },
  {
    id: "fairness-fail-closed",
    allowed: true,
    claim:
      "Fairness chỉ công bố metric khi có thuộc tính audit đã duyệt + cỡ mẫu đủ; nếu không → insufficient_data.",
  },
  {
    id: "agent-grounded",
    allowed: true,
    claim:
      "Agent chỉ giải thích đầu ra model/API đã có; không tự tính điểm hay suy đoán nguyên nhân.",
  },
  {
    id: "forecast-hybrid-shipped",
    allowed: false,
    claim:
      "Cấm: claim forecasting / gated fusion / hybrid đã ship hoặc nằm trong demo MVP.",
  },
  {
    id: "attendance-post-mvp",
    allowed: false,
    claim:
      "Cấm: gọi điểm danh theo thời gian là Post-MVP / ngoài phạm vi khi thiếu nguồn.",
  },
  {
    id: "raw-risk-label",
    allowed: false,
    claim:
      "Cấm: “Điểm rủi ro”, high-risk student, chẩn đoán bỏ học / sức khỏe tâm thần.",
  },
] as const;
