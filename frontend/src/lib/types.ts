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

/* ---------- Care workflow (H03) — POST /cases/{id}/transitions ---------- */

/** Process §4.2 action codes — mirror backend app/cases/domain.py CaseAction. */
export type CaseAction =
  | "queue_for_review"
  | "approve"
  | "dismiss"
  | "defer"
  | "assign"
  | "accept"
  | "resolve"
  | "monitor";

/** Narrow care-surface response (NOT public ReviewCase) — mirror TransitionResponse. */
export type TransitionResponse = {
  case_id: string;
  state: CaseState;
  advisor_ref: string | null;
  review_at: string | null;
  reason_code: string | null;
  monitoring_until: string | null;
  mapping_repair_queued: boolean;
  updated_at: string | null;
};

/** mirror TransitionErrorBody (wrapped in FastAPI {detail: ...}). */
export type TransitionErrorBody = {
  detail: string;
  code: string;
  case_id: string;
  state: string;
  mapping_repair_queued: boolean;
};

export type TransitionResult =
  | { ok: true; data: TransitionResponse }
  | { ok: false; error: TransitionErrorBody | null };

/* ---------- H04: threshold public + fairness (mirror backend contracts) ---------- */

/** mirror app/contracts/threshold_public.py PublicThresholdConfig. */
export type PublicThresholdConfig = {
  threshold_config_version: string;
  tau_case: number;
  tau_high: number;
  model_version: string;
};

/** mirror ThresholdImpactResponse — aggregate counts only, never per-student scores. */
export type ThresholdImpactResponse = {
  threshold_config_version: string;
  tau_case: number;
  tau_high: number;
  model_version: string;
  n_scored: number;
  n_can_ra_soat: number;
  n_uu_tien_som: number;
  n_no_case: number;
};

/** mirror app/contracts/fairness.py — MVP path: status=insufficient_data, no group metrics. */
export type FairnessGroupMetrics = {
  group_type: "socioeconomic" | "ethnicity";
  group: string;
  n_total: number;
  n_label_neg: number;
  n_label_pos: number;
  n_excluded_insufficient: number;
  fpr: number | null;
  tpr: number | null;
  selection_rate: number | null;
  status: "ok" | "insufficient_group_data";
};

export type FairnessReport = {
  dataset_version: string;
  model_version: string;
  threshold_config_version: string;
  label_rule_version: string;
  computed_at: string;
  status: "insufficient_data" | "ok";
  reason_code: "no_approved_audit_attribute" | "insufficient_group_data" | null;
  audit_attribute: string | null;
  small_n_min_denominator: number | null;
  groups: FairnessGroupMetrics[] | null;
  delta_fpr_by_group_type?: Record<string, { status: "ok" | "insufficient"; value: number | null; reason: string | null }> | null;
  fairness_flag?: { flagged: boolean; delta_fpr_threshold: number; triggered_group_types: string[] } | null;
};

/* ---------- Phiên demo (không phải auth thật — PRD §9) ---------- */

export type Role = "ban_quan_ly" | "gvcn";

export type DemoAccount = {
  id: string;
  name: string;
  /** Mật khẩu fixture công khai cho demo — không phải secret. */
  password: string;
  roles: Role[];
};

export const ROLE_LABEL: Record<Role, string> = {
  ban_quan_ly: "Ban quản lý — giám sát học tập",
  gvcn: "Giảng viên chủ nhiệm",
};

export const ROLE_ICON: Record<Role, string> = {
  ban_quan_ly: "👔",
  gvcn: "🧑‍🏫",
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

/* ---------- Agent explanation (H24) — mirror backend app/agent/schemas.py ---------- */

export type AgentIntent = "explain_case" | "neutral_draft";

export type ExplanationStatus = "ok" | "insufficient_data" | "refused" | "unavailable";

/** mirror RefusalReason enum — agent-side guardrail codes (PRD §5.4, Ethics §8). */
export type RefusalReason =
  | "invent_or_compute_score"
  | "diagnose_mental_health"
  | "speculate_protected_or_personal_cause"
  | "decide_contact_discipline_or_status"
  | "auto_send_or_notify"
  | "access_data_out_of_scope"
  | "reveal_raw_score_or_weights";

export type GroundedFact = {
  statement_vi: string;
  source: "model_factor" | "coverage" | "case_field";
  ref: string | null;
};

/** Draft nháp trung lập — agent KHÔNG bao giờ tự gửi; luôn requires_human_approval. */
export type DraftMessage = {
  body_vi: string;
  requires_human_approval: boolean;
  channel: string | null;
};

export type AgentExplanation = {
  status: ExplanationStatus;
  answer_vi: string;
  grounded_facts: GroundedFact[];
  model_factors_used: string[];
  limitation_keys: string[];
  limitations_vi: string;
  refusal_reason: RefusalReason | null;
  draft_message: DraftMessage | null;
  model_version: string | null;
  disclaimer_vi: string;
};
