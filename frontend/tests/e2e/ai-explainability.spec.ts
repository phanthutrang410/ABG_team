import { expect, test } from "@playwright/test";
import { caseListOk, json, mockCaseDetail, mockCaseList, reviewCase, useDemoSession } from "./support";

test.beforeEach(async ({ page }) => {
  await useDemoSession(page, "quanly", "ban_quan_ly");
});

test("hiển thị giải thích có căn cứ, giới hạn và quyền quyết định của con người", async ({ page }) => {
  await mockCaseDetail(page, { case: reviewCase, state: "ok", freshness: "fresh", problem: null });
  let requestBody: Record<string, unknown> | null = null;
  await page.route(/\/review-cases\/case_pseudo_001\/explanation$/, async (route) => {
    requestBody = route.request().postDataJSON();
    await json(route, {
      status: "ok",
      answer_vi: "Case cần được rà soát vì xu hướng kết quả học tập đang giảm.",
      grounded_facts: [
        { statement_vi: "Kết quả học tập giảm giữa hai kỳ gần nhất.", source: "model_factor", ref: "grade_trend_declining" },
      ],
      model_factors_used: ["grade_trend_declining"],
      limitation_keys: ["attendance_source_unapproved"],
      limitations_vi: "Nguồn dữ liệu điểm danh chưa được phê duyệt nên chưa được sử dụng.",
      refusal_reason: null,
      draft_message: null,
      model_version: "fpt-text-1",
      disclaimer_vi: "Người có thẩm quyền rà soát và quyết định bước tiếp theo.",
    });
  });

  await page.goto("/analysis/case_pseudo_001");
  await page.getByPlaceholder("Vì sao case này cần rà soát?").fill("Yếu tố nào tạo ra tín hiệu này?");
  await page.getByRole("button", { name: "Hỏi", exact: true }).click();

  await expect.poll(() => requestBody).toEqual({
    intent: "explain_case",
    question: "Yếu tố nào tạo ra tín hiệu này?",
    locale: "vi",
  });
  expect(requestBody).not.toHaveProperty("context");
  expect(requestBody).not.toHaveProperty("student_ref");
  await expect(page.getByText("Case cần được rà soát vì xu hướng kết quả học tập đang giảm.")).toBeVisible();
  const agentPanel = page.getByRole("heading", { name: "GIẢI THÍCH CỦA AI (căn cứ dữ liệu)" }).locator("..");
  await expect(agentPanel.getByText("grade_trend_declining", { exact: true })).toBeVisible();
  await expect(page.getByText(/Nguồn dữ liệu điểm danh chưa được phê duyệt/)).toBeVisible();
  await expect(page.getByText(/Con người quyết định/)).toBeVisible();
  await expect(page.getByText(/raw score|probability|điểm thô|trọng số/i)).toHaveCount(0);
});

test("ngưỡng chỉ hiển thị tác động tổng hợp và gửi đúng tham số minh họa", async ({ page }) => {
  await mockCaseList(page);
  await page.route(/\/config\/thresholds$/, (route) =>
    json(route, {
      threshold_config_version: "thr-epu-0.1-uncalibrated",
      tau_case: 0.5,
      tau_high: 0.75,
      model_version: "ew-term-0.1-uncalibrated",
    }),
  );

  const impactQueries: string[] = [];
  await page.route(/\/config\/thresholds\/impact\?.*$/, (route) => {
    const url = new URL(route.request().url());
    impactQueries.push(url.search);
    const tauCase = Number(url.searchParams.get("tau_case"));
    return json(route, {
      threshold_config_version: "thr-epu-0.1-uncalibrated",
      tau_case: tauCase,
      tau_high: Number(url.searchParams.get("tau_high")),
      model_version: "ew-term-0.1-uncalibrated",
      n_scored: 20,
      n_can_ra_soat: tauCase >= 0.6 ? 3 : 5,
      n_uu_tien_som: 2,
      n_no_case: tauCase >= 0.6 ? 15 : 13,
    });
  });

  await page.goto("/analysis?tab=threshold");
  await expect(page.getByRole("heading", { name: "Ngưỡng tạo tín hiệu rà soát" })).toBeVisible();
  await expect(page.getByText("thr-epu-0.1-uncalibrated", { exact: true })).toBeVisible();
  await expect(page.getByText("SV được chấm").locator("..").getByText("20", { exact: true })).toBeVisible();

  await page.getByLabel("Ngưỡng tạo case").fill("0.6");
  await expect.poll(() => impactQueries.some((query) => query.includes("tau_case=0.6"))).toBe(true);
  await expect(page.getByText("Cần rà soát").locator("..").getByText("3", { exact: true })).toBeVisible();
  await expect(page.getByText(/Hệ thống không hiển thị điểm của từng sinh viên/)).toBeVisible();
  await expect(page.getByText(/raw score|probability|điểm thô/i)).toHaveCount(0);
});

test("trợ lý điều hướng trả lời từ đúng dữ liệu đang hiển thị", async ({ page }) => {
  await mockCaseList(page, {
    ...caseListOk,
    items: [reviewCase, { ...reviewCase, case_id: "case_pseudo_002", student_ref: "stu_pseudo_002", review_priority_band: "uu_tien_som" }],
  });
  await page.goto("/overview");

  await page.getByLabel("Hỏi nhanh EduSignal AI").fill("Có bao nhiêu trường hợp ưu tiên?");
  await page.getByRole("button", { name: "Gửi câu hỏi" }).click();

  await expect(page.getByText("Hiện có 1 trường hợp ở mức Ưu tiên sớm (trên tổng 2 tín hiệu).", { exact: true })).toBeVisible();
  await expect(page.getByText("Trợ lý điều hướng trả lời dựa trên dữ liệu đang hiển thị.", { exact: true })).toBeVisible();
});
