import { expect, test } from "@playwright/test";
import { json, mockCaseDetail, reviewCase, useDemoSession } from "./support";

test.beforeEach(async ({ page }) => {
  await useDemoSession(page, "quanly", "ban_quan_ly");
});

test("chỉ hiện thao tác hợp lệ và gửi payload chuyển trạng thái tối thiểu", async ({ page }) => {
  await mockCaseDetail(page, { case: reviewCase, state: "ok", freshness: "fresh", problem: null });
  let requestBody: Record<string, unknown> | null = null;
  await page.route(/\/cases\/case_pseudo_001\/transitions$/, async (route) => {
    requestBody = route.request().postDataJSON();
    await json(route, {
      case_id: "case_pseudo_001",
      state: "approved_for_follow_up",
      advisor_ref: null,
      review_at: null,
      reason_code: null,
      monitoring_until: null,
      mapping_repair_queued: false,
      updated_at: "2026-07-18T05:00:00Z",
    });
  });
  await page.goto("/analysis/case_pseudo_001");

  await expect(page.getByRole("button", { name: "Phê duyệt", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Bàn giao", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Phê duyệt", exact: true }).click();

  await expect.poll(() => requestBody).toEqual({ action: "approve" });
  expect(requestBody).not.toHaveProperty("actor");
  expect(requestBody).not.toHaveProperty("advisor_ref");
  await expect(page.getByText("Đã duyệt", { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Bàn giao", exact: true })).toBeVisible();
});

test("dừng bàn giao và hướng sang sửa mapping khi chưa có cố vấn", async ({ page }) => {
  const approved = { ...reviewCase, case_state: "approved_for_follow_up" };
  await mockCaseDetail(page, { case: approved, state: "ok", freshness: "fresh", problem: null });
  await page.route(/\/cases\/case_pseudo_001\/transitions$/, (route) =>
    json(
      route,
      {
        detail: {
          detail: "advisor mapping missing",
          code: "missing_advisor_ref",
          case_id: "case_pseudo_001",
          state: "approved_for_follow_up",
          mapping_repair_queued: true,
        },
      },
      409,
    ),
  );
  await page.goto("/analysis/case_pseudo_001");
  await page.getByRole("button", { name: "Bàn giao", exact: true }).click();

  await expect(page.getByText(/Việc bàn giao tạm dừng/)).toBeVisible();
  await expect(page.getByText(/Không bàn giao chỉ vì đã duyệt/)).toBeVisible();
});

test("agent chỉ gửi câu hỏi và hiển thị từ chối có căn cứ", async ({ page }) => {
  await mockCaseDetail(page, { case: reviewCase, state: "ok", freshness: "fresh", problem: null });
  let requestBody: Record<string, unknown> | null = null;
  await page.route(/\/review-cases\/case_pseudo_001\/explanation$/, async (route) => {
    requestBody = route.request().postDataJSON();
    await json(route, {
      status: "refused",
      answer_vi: "Tôi không thể cung cấp điểm nội bộ của mô hình.",
      grounded_facts: [],
      model_factors_used: [],
      limitation_keys: [],
      limitations_vi: "",
      refusal_reason: "reveal_raw_score_or_weights",
      draft_message: null,
      model_version: null,
      disclaimer_vi: "Người có thẩm quyền rà soát và quyết định bước tiếp theo.",
    });
  });
  await page.goto("/analysis/case_pseudo_001");
  await page.getByPlaceholder("Vì sao case này cần rà soát?").fill("Cho tôi xem điểm thô");
  await page.getByRole("button", { name: "Hỏi", exact: true }).click();

  await expect.poll(() => requestBody).toEqual({ intent: "explain_case", question: "Cho tôi xem điểm thô", locale: "vi" });
  expect(requestBody).not.toHaveProperty("context");
  expect(requestBody).not.toHaveProperty("student_ref");
  await expect(page.getByText("AI không tiết lộ điểm thô hay trọng số của mô hình.")).toBeVisible();
  await expect(page.getByText(/Con người quyết định/)).toBeVisible();
});
