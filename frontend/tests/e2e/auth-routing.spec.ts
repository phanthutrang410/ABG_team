import { expect, test } from "@playwright/test";
import { json, mockCaseList, mockReviewOverviewSummary, useDemoSession } from "./support";

test.describe("Đăng nhập và điều hướng theo vai trò", () => {
  test.describe.configure({ mode: "serial" });

  test("khách chưa đăng nhập được chuyển về trang đăng nhập", async ({ page }) => {
    await page.goto("/overview");

    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole("heading", { name: "Đăng nhập" })).toBeVisible();
  });

  test("đăng nhập tài khoản nhiều vai và mở đúng không gian quản lý", async ({ page }) => {
    await page.addInitScript(() => {
      Math.random = () => 0;
    });
    await mockCaseList(page);
    await mockReviewOverviewSummary(page);
    await page.goto("/login");

    await page.getByLabel("Tài khoản").fill("demo");
    await page.getByLabel("Mật khẩu").fill("demo123");
    await page.getByPlaceholder("Nhập mã trong ảnh").fill("AAAAA");
    await page.getByRole("button", { name: /^Đăng nhập/ }).click();

    await expect(page.getByRole("heading", { name: "Chọn không gian làm việc" })).toBeVisible();
    await page.getByRole("button", { name: /Ban quản lý học tập/ }).click();

    await expect(page).toHaveURL(/\/overview$/);
    await expect(page.getByText(/Chào ThS\. Minh Anh/)).toBeVisible();
    await expect(page.getByRole("heading", { name: "Đăng nhập" })).toHaveCount(0);
  });

  test("giảng viên không mở được workspace quản lý", async ({ page }) => {
    await useDemoSession(page, "gvcn", "gvcn");
    await page.goto("/analysis");

    await expect(page).toHaveURL(/\/advisor(?:#cases)?$/);
    await expect(page.getByRole("heading", { name: "Case của tôi" })).toBeVisible();
  });

  test("tài khoản nhiều vai chuyển từ Ban quản lý sang GVCN và rời /analysis", async ({ page }) => {
    const managementSession = {
      account_id: "acct:demo",
      display_name: "Tài khoản trình diễn",
      roles: ["ban_quan_ly", "gvcn"],
      active_role: "ban_quan_ly",
    };
    await page.route(/\/auth\/me$/, (route) => json(route, managementSession));
    await page.route(/\/auth\/active-role$/, async (route) => {
      expect(route.request().postDataJSON()).toEqual({ role: "gvcn" });
      await json(route, { ...managementSession, active_role: "gvcn" });
    });
    await mockCaseList(page);
    await page.goto("/analysis");

    await page.locator('header button[aria-haspopup="menu"]').click();
    await page.locator('select[title="Chuyển vai trò"]').selectOption("gvcn");

    await expect(page).toHaveURL(/\/advisor(?:#cases)?$/);
    await expect(page.getByRole("heading", { name: "Case của tôi" })).toBeVisible();
  });

  test("thông tin tài khoản chỉ xuất hiện ở thanh trên cùng", async ({ page }) => {
    await useDemoSession(page, "quanly", "ban_quan_ly");
    await mockCaseList(page);
    await page.goto("/analysis");

    await expect(page.locator('header button[aria-haspopup="menu"]')).toHaveCount(1);
    await expect(page.locator('aside button[aria-haspopup="menu"]')).toHaveCount(0);
    await expect(page.locator("aside").getByText("TS. Nam", { exact: true })).toHaveCount(0);
  });
});
