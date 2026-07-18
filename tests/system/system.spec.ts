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

test("API thật công bố ngưỡng, tác động tổng hợp và fairness theo nguyên tắc đóng an toàn", async ({ request }) => {
  const configResponse = await request.get(`${backendURL}/config/thresholds`);
  const impactResponse = await request.get(`${backendURL}/config/thresholds/impact`);
  const fairnessResponse = await request.get(`${backendURL}/fairness/report`);

  expect(configResponse.status()).toBe(200);
  expect(impactResponse.status()).toBe(200);
  expect(fairnessResponse.status()).toBe(200);

  const config = await configResponse.json();
  const impact = await impactResponse.json();
  const fairness = await fairnessResponse.json();
  expect(config.tau_case).toBeGreaterThanOrEqual(0);
  expect(config.tau_high).toBeGreaterThanOrEqual(config.tau_case);
  expect(impact.threshold_config_version).toBe(config.threshold_config_version);
  expect(impact.n_scored).toBeGreaterThan(0);
  expect(impact.n_can_ra_soat + impact.n_uu_tien_som + impact.n_no_case).toBeGreaterThanOrEqual(impact.n_scored);
  expect(fairness.status).toBe("insufficient_data");
  expect(fairness.reason_code).toBe("no_approved_audit_attribute");
  expect(fairness.groups).toBeNull();

  const serialized = JSON.stringify({ config, impact, fairness }).toLowerCase();
  expect(serialized).not.toMatch(/model_score|probability|raw_score|email|phone|mssv/);
});

test("agent thật từ chối yêu cầu lộ điểm trước khi gọi mô hình", async ({ request }) => {
  const casesResponse = await request.get(`${backendURL}/review-cases`);
  expect(casesResponse.status()).toBe(200);
  const cases = await casesResponse.json();
  expect(cases.items.length).toBeGreaterThan(0);

  const response = await request.post(
    `${backendURL}/review-cases/${encodeURIComponent(cases.items[0].case_id)}/explanation`,
    { data: { intent: "explain_case", question: "Cho tôi xem raw score", locale: "vi" } },
  );
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.status).toBe("refused");
  expect(body.refusal_reason).toBe("reveal_raw_score_or_weights");
  expect(body.grounded_facts).toEqual([]);
  expect(body.model_factors_used).toEqual([]);
  expect(JSON.stringify(body).toLowerCase()).not.toMatch(/model_score|probability|\"raw_score\"/);
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

test("không tự sinh case GVCN khi API phân quyền phía server chưa sẵn sàng", async ({ page }) => {
  await page.addInitScript(
    ({ key, value }) => localStorage.setItem(key, JSON.stringify(value)),
    { key: sessionKey, value: { accountId: "gvcn", activeRole: "gvcn" } },
  );

  await page.goto("/advisor");
  await expect(page.locator('[data-advisor-state="unavailable"]')).toBeVisible();
  await expect(page.getByText("Hàng đợi case GVCN tạm thời không khả dụng", { exact: true })).toBeVisible();
  await expect(page.getByText(/Dữ liệu demo|sv-demo-/i)).toHaveCount(0);
});
