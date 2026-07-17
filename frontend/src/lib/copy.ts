/**
 * Runtime privacy/care copy — Data-ML §6 (H12a).
 * Export is reusable for UI and later agent grounding (T02).
 * Do not invent keys here; amend Data-ML §6 first.
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
