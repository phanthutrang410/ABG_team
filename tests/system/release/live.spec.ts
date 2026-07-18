import { expect, test } from "@playwright/test";

const frontendURL = process.env.RELEASE_BASE_URL!.replace(/\/$/, "");
const backendURL = process.env.RELEASE_API_BASE_URL!.replace(/\/$/, "");
const repositoryURL = process.env.RELEASE_REPOSITORY_URL!;
const requireLiveAi = process.env.RELEASE_REQUIRE_LIVE_AI_OK !== "0";
const sessionKey = "silentshield.session.v2";

test("frontend, backend và repository công khai đều truy cập được", async ({ page, request }) => {
  const [healthResponse, repositoryResponse] = await Promise.all([
    request.get(`${backendURL}/health`),
    request.get(repositoryURL),
  ]);

  expect(healthResponse.status()).toBe(200);
  await expect(healthResponse.json()).resolves.toEqual({
    status: "ok",
    service: "silent-shield",
    database: true,
  });
  expect(repositoryResponse.status(), "Repository phải mở được từ phiên không đăng nhập").toBeLessThan(400);

  const response = await page.goto(`${frontendURL}/login`);
  expect(response?.status()).toBeLessThan(400);
  await expect(page.getByRole("heading", { name: "Đăng nhập" })).toBeVisible();
  await expect(page.getByText(/Application error|Internal Server Error|404: This page could not be found/i)).toHaveCount(0);
});

test("bản triển khai hiển thị dữ liệu thật và không lộ trường nội bộ", async ({ page, request }) => {
  const casesResponse = await request.get(`${backendURL}/review-cases`);
  expect(casesResponse.status()).toBe(200);
  const body = await casesResponse.json();
  expect(["ok", "stale"]).toContain(body.state);
  expect(body.items.length, "Demo online phải có ít nhất một case từ dữ liệu đã import").toBeGreaterThan(0);
  expect(JSON.stringify(body).toLowerCase()).not.toMatch(/model_score|probability|raw_score|email|phone|mssv/);

  await page.addInitScript(
    ({ key, value }) => localStorage.setItem(key, JSON.stringify(value)),
    { key: sessionKey, value: { accountId: "quanly", activeRole: "ban_quan_ly" } },
  );
  const apiResponse = page.waitForResponse(
    (response) => response.url().startsWith(`${backendURL}/review-cases`) && response.request().method() === "GET",
  );
  await page.goto(`${frontendURL}/analysis?tab=signals`);
  expect((await apiResponse).status()).toBe(200);
  await expect(page.getByText(body.items[0].student_ref, { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Không tải được/ })).toHaveCount(0);
});

test("dịch vụ AI online trả giải thích có cấu trúc cho case thật", async ({ request }) => {
  const cases = await (await request.get(`${backendURL}/review-cases`)).json();
  expect(cases.items.length).toBeGreaterThan(0);

  const response = await request.post(
    `${backendURL}/review-cases/${encodeURIComponent(cases.items[0].case_id)}/explanation`,
    { data: { intent: "explain_case", question: "Vì sao case này cần rà soát?", locale: "vi" } },
  );
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(["ok", "insufficient_data", "unavailable"]).toContain(body.status);
  expect(body.answer_vi).toEqual(expect.any(String));
  expect(Array.isArray(body.grounded_facts)).toBe(true);
  expect(Array.isArray(body.model_factors_used)).toBe(true);
  expect(body.disclaimer_vi).toEqual(expect.any(String));
  expect(JSON.stringify(body).toLowerCase()).not.toMatch(/model_score|probability|raw_score|email|phone|mssv/);

  if (requireLiveAi) {
    expect(body.status, "Cổng checkpoint 48h yêu cầu AI online hoạt động thật, không chỉ đúng contract").toBe("ok");
    expect(body.model_factors_used.length).toBeGreaterThan(0);
    expect(body.model_version).toEqual(expect.any(String));
  }
});
