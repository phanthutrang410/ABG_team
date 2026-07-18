import { expect, test } from "@playwright/test";

const backendURL = `http://127.0.0.1:${Number(process.env.SYSTEM_TEST_BACKEND_PORT ?? 8100)}`;
const sessionKey = "silentshield.session.v2";

test("backend kết nối PostgreSQL thật và báo trạng thái sẵn sàng", async ({ request }) => {
  const response = await request.get(`${backendURL}/health`);

  expect(response.status()).toBe(200);
  await expect(response.json()).resolves.toEqual({
    status: "ok",
    service: "silent-shield",
    database: true,
  });
});

test("API thật trả envelope danh sách an toàn từ dữ liệu đã import", async ({ request }) => {
  const response = await request.get(`${backendURL}/review-cases`);
  expect(response.status()).toBe(200);

  const body = await response.json();
  expect(["ok", "empty", "stale"]).toContain(body.state);
  expect(Array.isArray(body.items)).toBe(true);
  expect(body.state).not.toBe("error");

  const serialized = JSON.stringify(body).toLowerCase();
  expect(serialized).not.toMatch(/model_score|probability|raw_score|email|phone|mssv/);
});

test("đăng nhập trên trình duyệt và tải dữ liệu qua backend thật", async ({ page }) => {
  await page.addInitScript(() => {
    Math.random = () => 0;
  });
  await page.goto("/login");

  await page.getByLabel("Tài khoản").fill("demo");
  await page.getByLabel("Mật khẩu").fill("demo123");
  await page.getByPlaceholder("Nhập mã trong ảnh").fill("AAAAA");
  await page.getByRole("button", { name: /^Đăng nhập/ }).click();
  await expect(page.getByRole("heading", { name: "Chọn không gian làm việc" })).toBeVisible();
  await page.getByRole("button", { name: /Ban quản lý học tập/ }).click();

  await expect.poll(() =>
    page.evaluate((key) => JSON.parse(localStorage.getItem(key) ?? "null")?.activeRole, sessionKey),
  ).toBe("ban_quan_ly");
  // Auth/routing đã có browser test riêng ở frontend. System test chuyển thẳng
  // tới workspace sau khi xác nhận session để tập trung kiểm tra kết nối thật.
  await page.goto("/overview");
  await expect(page.getByText(/Chào ThS\. Minh Anh/)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Không tải được dữ liệu" })).toHaveCount(0);
});

test("màn phân tích hiển thị đúng response nhận qua HTTP thật", async ({ page }) => {
  await page.addInitScript(
    ({ key, value }) => localStorage.setItem(key, JSON.stringify(value)),
    { key: sessionKey, value: { accountId: "quanly", activeRole: "ban_quan_ly" } },
  );

  const responsePromise = page.waitForResponse(
    (response) => response.url().startsWith(`${backendURL}/review-cases`) && response.request().method() === "GET",
  );
  await page.goto("/analysis?tab=signals");
  const apiResponse = await responsePromise;
  const body = await apiResponse.json();

  expect(apiResponse.status()).toBe(200);
  expect(body.state).not.toBe("error");
  await expect(page.getByRole("heading", { name: "Không tải được danh sách tín hiệu" })).toHaveCount(0);

  if (body.items.length > 0) {
    await expect(page.getByText(body.items[0].student_ref, { exact: true })).toBeVisible();
  } else {
    await expect(page.getByText("Chưa có tín hiệu mới trong kỳ dữ liệu này.")).toBeVisible();
  }
});
