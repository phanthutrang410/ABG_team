import assert from "node:assert/strict";
import test from "node:test";

import {
  isAdvisorLocalDemoEnabled,
  resolveAdvisorAccess,
  resolveAnalysisGate,
} from "../src/lib/advisor-routing.ts";
import type { SessionAccount } from "../src/lib/types.ts";

const GVCN: SessionAccount = {
  id: "gvcn",
  name: "CVHT Lan",
  roles: ["gvcn"],
};

const LEADER: SessionAccount = {
  id: "quanly",
  name: "TS. Nam",
  roles: ["ban_quan_ly"],
};

test("/analysis gate redirects GVCN and never selects management for that role", () => {
  assert.equal(resolveAnalysisGate(false, null), "loading");
  assert.equal(resolveAnalysisGate(false, "gvcn"), "loading");
  assert.equal(resolveAnalysisGate(true, "gvcn"), "gvcn_redirect");
  assert.equal(resolveAnalysisGate(true, "ban_quan_ly"), "management");
  assert.equal(resolveAnalysisGate(true, null), "management");
  assert.notEqual(resolveAnalysisGate(true, "gvcn"), "management");
});

test("/advisor access guards unauthenticated and wrong-role sessions", () => {
  assert.equal(resolveAdvisorAccess(false, null, null), "loading");
  assert.equal(resolveAdvisorAccess(true, null, null), "unauthenticated");
  assert.equal(resolveAdvisorAccess(true, GVCN, null), "unauthenticated");
  assert.equal(resolveAdvisorAccess(true, LEADER, "ban_quan_ly"), "wrong_role");
  assert.equal(resolveAdvisorAccess(true, GVCN, "gvcn"), "ok");
});

test("advisor local demo flag is off by default and never on in production", () => {
  const previousFlag = process.env.NEXT_PUBLIC_ADVISOR_LOCAL_DEMO;
  const previousNodeEnv = process.env.NODE_ENV;

  try {
    delete process.env.NEXT_PUBLIC_ADVISOR_LOCAL_DEMO;
    process.env.NODE_ENV = "development";
    assert.equal(isAdvisorLocalDemoEnabled(), false);

    process.env.NEXT_PUBLIC_ADVISOR_LOCAL_DEMO = "1";
    process.env.NODE_ENV = "development";
    assert.equal(isAdvisorLocalDemoEnabled(), true);

    process.env.NEXT_PUBLIC_ADVISOR_LOCAL_DEMO = "1";
    process.env.NODE_ENV = "production";
    assert.equal(isAdvisorLocalDemoEnabled(), false);
  } finally {
    if (previousFlag === undefined) delete process.env.NEXT_PUBLIC_ADVISOR_LOCAL_DEMO;
    else process.env.NEXT_PUBLIC_ADVISOR_LOCAL_DEMO = previousFlag;
    process.env.NODE_ENV = previousNodeEnv;
  }
});
