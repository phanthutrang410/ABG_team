import type { CSSProperties } from "react";
import { BAND_LABEL, CASE_STATE_LABEL, type CaseState, type ReviewPriorityBand } from "@/lib/types";

const pill: CSSProperties = {
  display: "inline-block",
  padding: "2px 10px",
  borderRadius: 999,
  fontSize: 12,
  fontWeight: 600,
  whiteSpace: "nowrap",
};

/** Only two public bands (Data-ML §4) — no numeric severity implied by color alone. */
const BAND_COLOR: Record<ReviewPriorityBand, { bg: string; fg: string }> = {
  uu_tien_som: { bg: "#fee2e2", fg: "#991b1b" }, // Ưu tiên sớm — đỏ (khẩn hơn)
  can_ra_soat: { bg: "#fef3c7", fg: "#92400e" }, // Cần rà soát — vàng
};

export function BandBadge({ band }: { band: ReviewPriorityBand | null }) {
  if (band === null) {
    return (
      <span style={{ ...pill, background: "#f1f5f9", color: "#475569", fontStyle: "italic" }}>
        Chưa đủ dữ liệu
      </span>
    );
  }
  const { bg, fg } = BAND_COLOR[band];
  return <span style={{ ...pill, background: bg, color: fg }}>{BAND_LABEL[band]}</span>;
}

const STATE_COLOR: Partial<Record<CaseState, { bg: string; fg: string }>> = {
  pending_review: { bg: "#fef9c3", fg: "#854d0e" },
  approved_for_follow_up: { bg: "#dbeafe", fg: "#1e40af" },
  assigned: { bg: "#dcfce7", fg: "#166534" },
  follow_up_in_progress: { bg: "#dcfce7", fg: "#166534" },
  monitoring: { bg: "#e0f2fe", fg: "#075985" },
  dismissed: { bg: "#f1f5f9", fg: "#64748b" },
  resolved: { bg: "#dcfce7", fg: "#166534" },
};

export function CaseStateBadge({ state }: { state: CaseState }) {
  const { bg, fg } = STATE_COLOR[state] ?? { bg: "#f1f5f9", fg: "#334155" };
  return <span style={{ ...pill, background: bg, color: fg, fontWeight: 500 }}>{CASE_STATE_LABEL[state]}</span>;
}
