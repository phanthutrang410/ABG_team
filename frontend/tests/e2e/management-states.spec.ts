import { expect, test } from "@playwright/test";
import {
  caseListOk,
  json,
  mockCaseDetail,
  mockCaseList,
  mockReviewOverviewSummary,
  reviewCase,
  useDemoSession,
} from "./support";

test.beforeEach(async ({ page }) => {
  await useDemoSession(page, "quanly", "ban_quan_ly");
});

test("tổng quan tách đúng 460 sinh viên khỏi hàng case và không diễn giải số 0 tuần", async ({ page }) => {
  await mockCaseList(page);
  await mockReviewOverviewSummary(page);
  await page.route(/\/weekly-reports\/latest\?.*$/, (route) =>
    json(route, {
      status: "empty",
      aggregates: { new: 0, ongoing: 0, changed: 0, total_active: 0 },
      message_vi: "Chưa có tín hiệu nào trong báo cáo tuần này.",
    }),
  );
  await page.route(/\/weekly-briefings\/latest\?.*$/, (route) =>
    json(route, { status: "empty", message_vi: "Chưa có bản tin tuần." }),
  );

  await page.goto("/overview");

  await expect(page.getByText("460 sinh viên", { exact: true }).first()).toBeVisible();
  await expect(page.getByText(/Hệ thống đưa.*1 case.*1 sinh viên.*danh sách rà soát/)).toBeVisible();
  await expect(page.getByText(/Chưa có bản tin tuần vì workflow so sánh chưa tạo dữ liệu/)).toBeVisible();
  await expect(page.getByText(/^new: 0$/)).toHaveCount(0);
  await expect(page.getByText(/^total_active: 0$/)).toHaveCount(0);
  await expect(page.getByText(/phát hiện mới/i)).toHaveCount(0);
});

test("hiển thị danh sách bằng mã bảo vệ và không lộ trường nội bộ", async ({ page }) => {
  await mockCaseList(page);
  await page.goto("/analysis?tab=signals");

  await expect(page.getByRole("heading", { name: "Danh sách rà soát" })).toBeVisible();
  await expect(page.getByText("stu_pseudo_001", { exact: true })).toBeVisible();
  await expect(page.getByRole("table").getByText("Cần rà soát", { exact: true })).toBeVisible();
  await expect(page.getByText(/raw score|probability|trọng số/i)).toHaveCount(0);
});

test("mở chi tiết case trong popup và giữ nguyên danh sách phía sau", async ({ page }) => {
  await mockCaseList(page);
  await mockCaseDetail(page, { case: reviewCase, state: "ok", freshness: "fresh", problem: null });
  await page.goto("/analysis?tab=signals");

  await page.getByRole("row", { name: "Mở chi tiết case case_pseudo_001 của stu_pseudo_001" }).click();

  const dialog = page.getByRole("dialog", { name: "Chi tiết case" });
  await expect(dialog).toBeVisible();
  await expect(page).toHaveURL(/\/analysis\?tab=signals$/);
  await expect(dialog.getByText("stu_pseudo_001", { exact: true })).toBeVisible();
  await expect(dialog.getByLabel("Tiến trình rà soát")).toHaveAttribute("data-orientation", "horizontal");

  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Danh sách rà soát" })).toBeVisible();
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
  await page.getByRole("button", { name: "Mở danh sách rà soát" }).click();
  await expect(page.getByText("stu_pseudo_001", { exact: true }).first()).toBeVisible();
});

test("link fairness cũ đóng an toàn về Dashboard thay vì render số liệu ngoài navigation", async ({ page }) => {
  await mockCaseList(page);
  await page.goto("/analysis?tab=fairness");

  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByRole("heading", { name: /^FPR theo nhóm/ })).toHaveCount(0);
});

test("tìm sinh viên dùng dữ liệu đã trả về, không tự sinh bản ghi", async ({ page }) => {
  await mockCaseList(page, {
    ...caseListOk,
    items: [reviewCase, { ...reviewCase, case_id: "case_pseudo_002", student_ref: "stu_pseudo_002" }],
  });
  await page.goto("/analysis?tab=students");

  await page.getByLabel("Tìm trong danh sách rà soát").fill("002");
  await expect(page.getByText("stu_pseudo_002", { exact: true })).toBeVisible();
  await expect(page.getByText("stu_pseudo_001", { exact: true })).toHaveCount(0);
  await expect(page.getByText("1 case", { exact: true })).toBeVisible();
});
