/**
 * G05 — types mirror H11a integration envelopes + H06a ReviewCase exactly.
 * Source of truth: backend/app/contracts/{integration,review_case,coverage}.py.
 * Do NOT widen this set — public/agent field allowlist is closed (H11a §2).
 */

export type CaseState =
  | "new_signal"
  | "pending_review"
  | "approved_for_follow_up"
  | "dismissed"
  | "assigned"
  | "follow_up_in_progress"
  | "resolved"
  | "monitoring";

/** Data-ML §4 band — public. No raw score anywhere in this app. */
export type ReviewPriorityBand = "uu_tien_som" | "can_ra_soat";

export type DataState = "ok" | "partial" | "insufficient_data";

export type CoverageStatus = "ok" | "partial" | "insufficient";

/** Machine reason codes — Coverage.reason_codes (Data-ML §3). Do not invent outside this set. */
export type ReasonCode =
  | "source_unapproved"
  | "attendance_source_unapproved"
  | "single_term"
  | "grade_coverage_insufficient"
  | "attendance_coverage_insufficient"
  | "status_unknown"
  | "no_approved_audit_attribute"
  | "insufficient_group_data";

export type Coverage = {
  n_valid_terms: number;
  n_courses: number;
  n_attendance_events: number;
  last_term_code: string | null;
  last_attendance_at: string | null;
  status: CoverageStatus;
  reason_codes: ReasonCode[];
};

export type ContributingFactor = {
  code: string;
  evidence_refs: string[];
};

export type ReviewCase = {
  case_id: string;
  student_ref: string;
  case_state: CaseState;
  review_priority_band: ReviewPriorityBand | null;
  contributing_factors: ContributingFactor[];
  coverage: Coverage;
  data_state: DataState;
  limitations: string[];
  dataset_version: string;
  model_version: string;
  threshold_config_version: string;
  calculated_at: string;
};

export type ProblemCode =
  | "not_found"
  | "unauthorized"
  | "validation_error"
  | "upstream_unavailable"
  | "stale_snapshot"
  | "insufficient_data"
  | "empty"
  | "refused";

export type IntegrationProblem = {
  code: ProblemCode;
  reason_codes: string[];
  message_key: string | null;
};

export type ListState = "ok" | "empty" | "stale" | "error";
export type DetailState = "ok" | "empty" | "stale" | "insufficient_data" | "error";
export type Freshness = "fresh" | "stale";

export type CaseListResponse = {
  items: ReviewCase[];
  state: ListState;
  problem: IntegrationProblem | null;
};

export type CaseDetailResponse = {
  case: ReviewCase | null;
  state: DetailState;
  freshness: Freshness;
  problem: IntegrationProblem | null;
};

/* ---------- Nhãn hiển thị (đã dùng nhất quán trong docs/prototype trước) ---------- */

export const BAND_LABEL: Record<ReviewPriorityBand, string> = {
  uu_tien_som: "Ưu tiên sớm",
  can_ra_soat: "Cần rà soát",
};

export const CASE_STATE_LABEL: Record<CaseState, string> = {
  new_signal: "Tín hiệu mới",
  pending_review: "Chờ duyệt",
  approved_for_follow_up: "Đã duyệt",
  dismissed: "Đã loại",
  assigned: "Đã bàn giao",
  follow_up_in_progress: "Đang hỗ trợ",
  resolved: "Đã xử lý",
  monitoring: "Đang theo dõi",
};
