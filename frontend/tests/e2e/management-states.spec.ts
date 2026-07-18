import { expect, test } from "@playwright/test";
import { caseListOk, json, mockCaseList, reviewCase, useDemoSession } from "./support";

test.beforeEach(async ({ page }) => {
  await useDemoSession(page, "quanly", "ban_quan_ly");
});

test("hiển thị danh sách bằng mã bảo vệ và không lộ trường nội bộ", async ({ page }) => {
  await mockCaseList(page);
  await page.goto("/analysis?tab=signals");

  await expect(page.getByRole("heading", { name: "Danh sách tín hiệu" })).toBeVisible();
  await expect(page.getByText("stu_pseudo_001", { exact: true })).toBeVisible();
  await expect(page.getByText("Cần rà soát", { exact: true })).toBeVisible();
  await expect(page.getByText(/raw score|probability|trọng số/i)).toHaveCount(0);
});

test("cảnh báo rõ khi snapshot đã cũ nhưng vẫn giữ dữ liệu để rà soát", async ({ page }) => {
  await mockCaseList(page, {
    ...caseListOk,
    state: "stale",
    problem: { code: "stale_snapshot", reason_codes: ["stale_snapshot"], message_key: null },
  });
  await page.goto("/analysis?tab=signals");

  await expect(page.getByText(/Dữ liệu có thể đã cũ/)).toBeVisible();
  await expect(page.getByText("stu_pseudo_001", { exact: true })).toBeVisible();
  await expect(page.getByText(/ổn định/i)).toHaveCount(0);
});

test("tải lại sau lỗi và phục hồi bằng dữ liệu API", async ({ page }) => {
  let serveError = true;
  await page.route(/\/review-cases(?:\?.*)?$/, (route) => {
    return json(
      route,
      serveError
        ? { items: [], state: "error", problem: { code: "upstream_unavailable", reason_codes: [], message_key: null } }
        : caseListOk,
    );
  });
  await page.goto("/analysis");

  await expect(page.getByRole("heading", { name: "Không tải được dữ liệu" })).toBeVisible();
  serveError = false;
  await page.getByRole("button", { name: /Tải lại dữ liệu/ }).first().click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByText("stu_pseudo_001", { exact: true }).first()).toBeVisible();
});

test("fairness đóng an toàn khi chưa đủ điều kiện công bố", async ({ page }) => {
  await mockCaseList(page);
  await page.route(/\/fairness\/report$/, (route) =>
    json(route, {
      dataset_version: "epu-v59-empty:deadbeef:schema-1",
      model_version: "ew-term-0.1-uncalibrated",
      threshold_config_version: "thr-epu-0.1-uncalibrated",
      label_rule_version: "label-v1",
      computed_at: "2026-07-18T04:00:00Z",
      status: "insufficient_data",
      reason_code: "no_approved_audit_attribute",
      audit_attribute: null,
      small_n_min_denominator: 10,
      groups: null,
    }),
  );
  await page.goto("/analysis?tab=fairness");

  await expect(page.getByRole("heading", { name: /Chưa đủ điều kiện công bố/ })).toBeVisible();
  await expect(page.getByText(/Thuộc tính kiểm toán được.*phê duyệt/)).toBeVisible();
  await expect(page.getByRole("heading", { name: /^FPR theo nhóm/ })).toHaveCount(0);
});

test("tìm sinh viên dùng dữ liệu đã trả về, không tự sinh bản ghi", async ({ page }) => {
  await mockCaseList(page, {
    ...caseListOk,
    items: [reviewCase, { ...reviewCase, case_id: "case_pseudo_002", student_ref: "stu_pseudo_002" }],
  });
  await page.goto("/analysis?tab=students");

  await page.getByLabel("Tìm kiếm sinh viên").fill("002");
  await expect(page.getByText("stu_pseudo_002", { exact: true })).toBeVisible();
  await expect(page.getByText("stu_pseudo_001", { exact: true })).toHaveCount(0);
  await expect(page.getByText("1 sinh viên", { exact: true })).toBeVisible();
});
