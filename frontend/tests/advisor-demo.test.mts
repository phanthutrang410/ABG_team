import assert from "node:assert/strict";
import test from "node:test";

import {
  allowedAdvisorDemoActions,
  buildAdvisorFollowUps,
  generateAdvisorDemoCases,
  generateAdvisorDemoClasses,
  transitionAdvisorDemoCase,
} from "../src/lib/advisor-demo.ts";

const NOW = new Date("2026-07-18T08:00:00.000Z");

test("generator is deterministic, pseudonymous and T3-safe", () => {
  const first = generateAdvisorDemoCases("gvcn", 2, NOW);
  const second = generateAdvisorDemoCases("gvcn", 2, NOW);

  assert.deepEqual(first, second);
  assert.equal(first.length, 8);
  assert.ok(first.every((item) => item.student_ref.startsWith("sv-demo-")));
  assert.ok(first.every((item) => item.review_priority_band === null));
  assert.ok(first.every((item) => item.coverage.n_attendance_events === 0));
  assert.ok(first.every((item) => ["assigned", "follow_up_in_progress", "monitoring", "resolved"].includes(item.case_state)));
  assert.doesNotMatch(JSON.stringify(first), /@|email|phone|risk_score|model_score/i);
});

test("a different variant creates a different scoped demo set", () => {
  const first = generateAdvisorDemoCases("gvcn", 0, NOW);
  const second = generateAdvisorDemoCases("gvcn", 1, NOW);

  assert.notDeepEqual(first.map((item) => item.student_ref), second.map((item) => item.student_ref));
});

test("advisor actions follow Process section 4 transitions", () => {
  const [assigned] = generateAdvisorDemoCases("gvcn", 0, NOW);
  assert.deepEqual(allowedAdvisorDemoActions(assigned.case_state), ["accept"]);

  const accepted = transitionAdvisorDemoCase(assigned, "accept", NOW);
  assert.equal(accepted.case_state, "follow_up_in_progress");

  const monitoringUntil = "2026-07-30T00:00:00.000Z";
  const monitored = transitionAdvisorDemoCase(accepted, "monitor", NOW, monitoringUntil);
  assert.equal(monitored.case_state, "monitoring");
  assert.equal(monitored.monitoring_until, monitoringUntil);

  const resolved = transitionAdvisorDemoCase(monitored, "resolve", NOW);
  assert.equal(resolved.case_state, "resolved");
  assert.equal(resolved.monitoring_until, null);
});

test("forbidden and incomplete transitions fail closed", () => {
  const [assigned] = generateAdvisorDemoCases("gvcn", 0, NOW);
  assert.throws(() => transitionAdvisorDemoCase(assigned, "resolve", NOW), /forbidden_transition/);

  const accepted = transitionAdvisorDemoCase(assigned, "accept", NOW);
  assert.throws(() => transitionAdvisorDemoCase(accepted, "monitor", NOW), /missing_monitoring_until/);
});

test("class roster is deterministic, pseudonymous and links every handed-off case once", () => {
  const cases = generateAdvisorDemoCases("gvcn", 3, NOW);
  const first = generateAdvisorDemoClasses("gvcn", 3, cases);
  const second = generateAdvisorDemoClasses("gvcn", 3, cases);
  const students = first.flatMap((item) => item.students);

  assert.deepEqual(first, second);
  assert.equal(first.length, 2);
  assert.ok(first.every((item) => item.students.length === 12));
  assert.ok(students.every((item) => item.student_ref.startsWith("sv-")));
  assert.equal(students.filter((item) => item.case_id !== null).length, cases.length);
  assert.deepEqual(
    students.filter((item) => item.case_id).map((item) => item.case_id).sort(),
    cases.map((item) => item.case_id).sort(),
  );
  assert.doesNotMatch(JSON.stringify(first), /@|email|phone|risk_score|model_score|full_name/i);
});

test("follow-up list excludes resolved cases and is ordered by due time", () => {
  const cases = generateAdvisorDemoCases("gvcn", 0, NOW);
  const items = buildAdvisorFollowUps(cases);

  assert.ok(items.length > 0);
  assert.ok(items.every((item) => item.case_state !== "resolved"));
  assert.deepEqual(
    items.map((item) => item.due_at),
    [...items].map((item) => item.due_at).sort(),
  );
  assert.ok(items.some((item) => item.kind === "accept_handoff"));
  assert.ok(items.some((item) => item.kind === "monitoring_check"));
});
