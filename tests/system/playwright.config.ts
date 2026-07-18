import { defineConfig, devices } from "@playwright/test";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const systemDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(systemDir, "../..");
const frontendDir = resolve(repoRoot, "frontend");
const backendDir = resolve(repoRoot, "backend");

const frontendPort = Number(process.env.SYSTEM_TEST_FRONTEND_PORT ?? 3200);
const backendPort = Number(process.env.SYSTEM_TEST_BACKEND_PORT ?? 8100);
const frontendURL = `http://127.0.0.1:${frontendPort}`;
const backendURL = `http://127.0.0.1:${backendPort}`;
const python = process.env.SYSTEM_TEST_PYTHON;
const externalServers = process.env.SYSTEM_TEST_EXTERNAL_SERVERS === "1";

if (!externalServers && !python) {
  throw new Error("SYSTEM_TEST_PYTHON chưa được đặt. Hãy chạy tests/system/run.ps1.");
}
if (!process.env.DATABASE_URL) {
  throw new Error("DATABASE_URL chưa được đặt. Hãy chạy tests/system/run.ps1.");
}

const quote = (value: string) => `"${value.replaceAll('"', '\\"')}"`;

export default defineConfig({
  testDir: ".",
  testMatch: "system.spec.ts",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  timeout: 45_000,
  expect: { timeout: 10_000 },
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report" }],
  ],
  outputDir: "test-results",
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
      name: "chromium-system",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: externalServers ? undefined : [
    {
      command: `${quote(python!)} -m uvicorn app.main:app --app-dir ${quote(backendDir)} --host 127.0.0.1 --port ${backendPort}`,
      url: `${backendURL}/health`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        ...process.env,
        APP_ENV: "test",
        CORS_ORIGINS: frontendURL,
      },
    },
    {
      command: `npm run dev --prefix ${quote(frontendDir)} -- --hostname 127.0.0.1 --port ${frontendPort}`,
      url: frontendURL,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        ...process.env,
        NEXT_PUBLIC_API_BASE: backendURL,
        NEXT_PUBLIC_ADVISOR_LOCAL_DEMO: "0",
      },
    },
  ],
});
