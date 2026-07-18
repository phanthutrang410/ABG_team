import type { CaseDetailResponse, CaseListResponse } from "@/lib/types";

/**
 * G05 — validated fixtures, mirrored verbatim from
 * backend/tests/fixtures/integration/*.json (H11a §5). Values are NOT invented;
 * this file must stay byte-identical in content to the backend JSON it mirrors.
 * G02 replaces this module with a live fetch to GET /review-cases; component
 * code should not need to change when that happens.
 */

export const CASE_LIST_OK: CaseListResponse = {
  items: [
    {
      case_id: "case_pseudo_001",
      student_ref: "stu_pseudo_001",
      case_state: "pending_review",
      review_priority_band: "can_ra_soat",
      contributing_factors: [
        {
          code: "grade_trend_negative",
          evidence_refs: ["term_avg:20242", "term_avg:20251"],
        },
      ],
      coverage: {
        n_valid_terms: 2,
        n_courses: 8,
        n_attendance_events: 0,
        last_term_code: "20251",
        last_attendance_at: null,
        status: "partial",
        reason_codes: ["attendance_source_unapproved"],
      },
      data_state: "partial",
      limitations: ["attendance_source_unapproved", "copy.partial_term_only"],
      dataset_version: "epu-v59-empty:deadbeef:schema-1",
      model_version: "ew-term-0.1-uncalibrated",
      threshold_config_version: "thr-epu-0.1-uncalibrated",
      calculated_at: "2026-07-18T04:00:00Z",
    },
  ],
  state: "ok",
  problem: null,
};

export const CASE_LIST_EMPTY: CaseListResponse = {
  items: [],
  state: "empty",
  problem: { code: "empty", reason_codes: [], message_key: null },
};

export const CASE_LIST_STALE: CaseListResponse = {
  items: [
    {
      case_id: "case_pseudo_001",
      student_ref: "stu_pseudo_001",
      case_state: "pending_review",
      review_priority_band: "can_ra_soat",
      contributing_factors: [
        {
          code: "grade_trend_negative",
          evidence_refs: ["term_avg:20242", "term_avg:20251"],
        },
      ],
      coverage: {
        n_valid_terms: 2,
        n_courses: 8,
        n_attendance_events: 0,
        last_term_code: "20251",
        last_attendance_at: null,
        status: "partial",
        reason_codes: ["attendance_source_unapproved"],
      },
      data_state: "partial",
      limitations: ["attendance_source_unapproved", "copy.partial_term_only"],
      dataset_version: "epu-v59-empty:deadbeef:schema-1",
      model_version: "ew-term-0.1-uncalibrated",
      threshold_config_version: "thr-epu-0.1-uncalibrated",
      calculated_at: "2026-07-17T04:00:00Z",
    },
  ],
  state: "stale",
  problem: { code: "stale_snapshot", reason_codes: ["stale_snapshot"], message_key: null },
};

export const CASE_LIST_ERROR: CaseListResponse = {
  items: [],
  state: "error",
  problem: { code: "upstream_unavailable", reason_codes: [], message_key: null },
};

export const CASE_DETAIL_OK: CaseDetailResponse = {
  case: CASE_LIST_OK.items[0],
  state: "ok",
  freshness: "fresh",
  problem: null,
};

export const CASE_DETAIL_STALE: CaseDetailResponse = {
  case: CASE_LIST_STALE.items[0],
  state: "stale",
  freshness: "stale",
  problem: { code: "stale_snapshot", reason_codes: ["stale_snapshot"], message_key: null },
};

export const CASE_DETAIL_INSUFFICIENT: CaseDetailResponse = {
  case: {
    case_id: "case_pseudo_insuf_001",
    student_ref: "stu_pseudo_002",
    case_state: "new_signal",
    review_priority_band: null,
    contributing_factors: [],
    coverage: {
      n_valid_terms: 0,
      n_courses: 0,
      n_attendance_events: 0,
      last_term_code: null,
      last_attendance_at: null,
      status: "insufficient",
      reason_codes: ["grade_coverage_insufficient", "attendance_source_unapproved"],
    },
    data_state: "insufficient_data",
    limitations: ["grade_coverage_insufficient", "attendance_source_unapproved"],
    dataset_version: "epu-v59-empty:deadbeef:schema-1",
    model_version: "ew-term-0.1-uncalibrated",
    threshold_config_version: "thr-epu-0.1-uncalibrated",
    calculated_at: "2026-07-18T04:00:00Z",
  },
  state: "insufficient_data",
  freshness: "fresh",
  problem: {
    code: "insufficient_data",
    reason_codes: ["grade_coverage_insufficient", "attendance_source_unapproved"],
    message_key: null,
  },
};

export const CASE_DETAIL_EMPTY: CaseDetailResponse = {
  case: null,
  state: "empty",
  freshness: "fresh",
  problem: { code: "not_found", reason_codes: ["student_not_found"], message_key: null },
};

export const CASE_DETAIL_ERROR: CaseDetailResponse = {
  case: null,
  state: "error",
  freshness: "fresh",
  problem: { code: "upstream_unavailable", reason_codes: [], message_key: null },
};

/** case_id → detail fixture, for the demo detail route. */
export const CASE_DETAIL_BY_ID: Record<string, CaseDetailResponse> = {
  case_pseudo_001: CASE_DETAIL_OK,
  case_pseudo_insuf_001: CASE_DETAIL_INSUFFICIENT,
};
