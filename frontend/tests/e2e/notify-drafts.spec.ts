import { expect, test } from "@playwright/test";
import { json, useDemoSession } from "./support";

const draftResponse = {
  state: "ok",
  bundles: [
    {
      advisor_ref: "advisor_pseudo_001",
      case_count: 1,
      cases: [
        {
          case_id: "case_pseudo_001",
          student_ref: "stu_pseudo_001",
          review_priority_band: "can_ra_soat",
          contributing_factor_codes: ["grade_trend_declining"],
          coverage_status: "partial",
          coverage_reason_codes: ["attendance_source_unapproved"],
          case_state: "assigned",
          class_code: "K66-CNTT-A",
        },
      ],
      draft: {
        subject: "Bản nháp bàn giao trường hợp cần theo dõi",
        body: "Thầy/cô vui lòng rà soát trường hợp stu_pseudo_001 và lựa chọn cách hỗ trợ phù hợp.",
        requires_human_approval: true,
      },
      limitations: ["attendance_source_unapproved"],
    },
  ],
  mapping_repair: { case_count: 0, cases: [], limitations: [] },
  problem: null,
};

test.beforeEach(async ({ page }) => {
  await useDemoSession(page, "quanly", "ban_quan_ly");
});

test("bản nháp yêu cầu con người duyệt và không có thao tác gửi", async ({ page }) => {
  await page.route(/\/advisor-handoff-drafts$/, (route) => json(route, draftResponse));
  await page.goto("/notify");

  await expect(page.getByRole("heading", { name: "Soạn mail cho giảng viên phụ trách" })).toBeVisible();
  await expect(page.locator("section").getByText("advisor_pseudo_001", { exact: true })).toBeVisible();
  await expect(page.getByText(/Cần Ban quản lý duyệt trước khi gửi/)).toBeVisible();
  await expect(page.getByText(draftResponse.bundles[0].draft.body, { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /^Gửi$/ })).toHaveCount(0);

  const mailLink = page.getByRole("link", { name: "Mở trong mail" });
  await expect(mailLink).toHaveAttribute("href", /^mailto:\?subject=/);
  await expect(mailLink).not.toHaveAttribute("href", /^mailto:[^?]+/);
});

test("lỗi API hiển thị trạng thái đóng an toàn và cho phép thử lại", async ({ page }) => {
  await page.route(/\/advisor-handoff-drafts$/, (route) =>
    json(route, {
      state: "error",
      bundles: [],
      mapping_repair: { case_count: 0, cases: [], limitations: [] },
      problem: { code: "upstream_unavailable", reason_codes: [], message_key: null },
    }),
  );
  await page.goto("/notify");

  await expect(page.getByRole("heading", { name: "Không tải được danh sách bàn giao" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Thử lại/ })).toBeVisible();
  await expect(page.getByText(/đã gửi/i)).toHaveCount(0);
});
