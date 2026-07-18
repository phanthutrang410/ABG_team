import { defineConfig, devices } from "@playwright/test";

const frontendURL = process.env.RELEASE_BASE_URL?.replace(/\/$/, "");
const backendURL = process.env.RELEASE_API_BASE_URL?.replace(/\/$/, "");
const repositoryURL = process.env.RELEASE_REPOSITORY_URL;

if (!frontendURL || !backendURL || !repositoryURL) {
  throw new Error(
    "Thiếu RELEASE_BASE_URL, RELEASE_API_BASE_URL hoặc RELEASE_REPOSITORY_URL. " +
      "Hãy chạy tests/system/release/run.ps1 với đủ URL.",
  );
}

export default defineConfig({
  testDir: "./release",
  testMatch: "live.spec.ts",
  fullyParallel: false,
  forbidOnly: true,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "release-playwright-report" }],
  ],
  outputDir: "release-test-results",
  use: {
    baseURL: frontendURL,
    locale: "vi-VN",
    serviceWorkers: "block",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium-release",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  metadata: { frontendURL, backendURL, repositoryURL },
});
