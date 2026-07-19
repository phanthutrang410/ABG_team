import assert from "node:assert/strict";
import test from "node:test";

test("local defaults keep auth same-origin and proxy to Uvicorn", async () => {
  delete process.env.VERCEL;
  delete process.env.NEXT_PUBLIC_API_BASE;
  delete process.env.BACKEND_URL;
  process.env.NODE_ENV = "development";

  const { default: config } = await import("../next.config.mjs?local-default-test");
  assert.equal(config.env.NEXT_PUBLIC_API_BASE, "");
  assert.equal(config.distDir, ".next-dev");

  const rewrites = await config.rewrites();
  assert.ok(
    rewrites.some(
      (rule: { source: string; destination: string }) =>
        rule.source === "/auth/:path*" &&
        rule.destination === "http://localhost:8000/auth/:path*",
    ),
  );
});
