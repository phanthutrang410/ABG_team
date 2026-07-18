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

export function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

export async function mockCaseList(page: Page, body: unknown = caseListOk) {
  await page.route(/\/review-cases(?:\?.*)?$/, (route) => json(route, body));
}

export async function mockCaseDetail(page: Page, body: unknown, caseId = "case_pseudo_001") {
  await page.route(new RegExp(`/review-cases/${caseId}$`), (route) => json(route, body));
}
