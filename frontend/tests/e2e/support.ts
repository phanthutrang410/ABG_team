import type { Page, Route } from "@playwright/test";

export const SESSION_KEY = "silentshield.session.v2";

export type DemoRole = "ban_quan_ly" | "gvcn";

export async function useDemoSession(
  page: Page,
  accountId: "quanly" | "gvcn" | "demo",
  activeRole: DemoRole | null,
) {
  await page.addInitScript(
    ({ key, value }) => localStorage.setItem(key, JSON.stringify(value)),
    { key: SESSION_KEY, value: { accountId, activeRole } },
  );
}

export const reviewCase = {
  case_id: "case_pseudo_001",
  student_ref: "stu_pseudo_001",
  case_state: "pending_review",
  review_priority_band: "can_ra_soat",
  contributing_factors: [
    { code: "grade_trend_declining", evidence_refs: ["term_avg:20242", "term_avg:20251"] },
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
} as const;

export const caseListOk = {
  items: [reviewCase],
  state: "ok",
  problem: null,
};

export const reviewOverviewSummaryOk = {
  state: "ok",
  scope: "organization",
  source_id: "v59-empty-program-students",
  dataset_version: "epu-v59-empty:deadbeef:schema-1",
  source_extracted_at: "2026-07-18T03:00:00Z",
  generated_at: "2026-07-18T04:00:00Z",
  total_students: 460,
  review_case_count: 1,
  review_student_count: 1,
  limited_student_count: 460,
  limited_review_case_count: 1,
  priority_band_counts: { uu_tien_som: 0, can_ra_soat: 1 },
  case_state_counts: {
    new_signal: 0,
    pending_review: 1,
    approved_for_follow_up: 0,
    dismissed: 0,
    assigned: 0,
    follow_up_in_progress: 0,
    resolved: 0,
    monitoring: 0,
  },
  student_coverage_counts: { ok: 0, partial: 460, insufficient: 0 },
  review_data_state_counts: { ok: 0, partial: 1, insufficient_data: 0 },
  comparison_status: "unavailable",
  new_since_previous_snapshot: null,
  problem: null,
};

export function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

export async function mockCaseList(page: Page, body: unknown = caseListOk) {
  await page.route(/\/review-cases(?:\?.*)?$/, (route) => json(route, body));
}

export async function mockReviewOverviewSummary(
  page: Page,
  body: unknown = reviewOverviewSummaryOk,
) {
  await page.route(/\/review-cases\/summary$/, (route) => json(route, body));
}

export async function mockCaseDetail(page: Page, body: unknown, caseId = "case_pseudo_001") {
  await page.route(new RegExp(`/review-cases/${caseId}$`), (route) => json(route, body));
}
