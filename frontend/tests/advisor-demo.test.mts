import assert from "node:assert/strict";
import test from "node:test";

import {
  ADVISOR_QUEUE_PAGE_SIZE,
  HANDOFF_ACK_OVERDUE_DAYS,
  allowedAdvisorDemoActions,
  buildAdvisorFollowUps,
  countOverdueHandoffs,
  generateAdvisorDemoCases,
  generateAdvisorDemoClasses,
  handoffElapsedDays,
  isHandoffOverdue,
  markAdvisorDemoViewed,
  paginateAdvisorQueue,
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

test("queue pagination is 10 per page, clamps out-of-range pages and slices correctly", () => {
  assert.equal(ADVISOR_QUEUE_PAGE_SIZE, 10);

  const items = Array.from({ length: 23 }, (_, index) => index);

  const first = paginateAdvisorQueue(items, 1);
  assert.equal(first.totalPages, 3);
  assert.equal(first.pageItems.length, 10);
  assert.deepEqual([first.start, first.end], [0, 10]);

  const last = paginateAdvisorQueue(items, 3);
  assert.equal(last.pageItems.length, 3);
  assert.deepEqual([last.start, last.end], [20, 23]);

  // Out-of-range / invalid pages clamp into [1, totalPages] instead of stranding an empty view.
  assert.equal(paginateAdvisorQueue(items, 99).page, 3);
  assert.equal(paginateAdvisorQueue(items, 0).page, 1);

  // A short list (the demo's 8 handed-off cases) stays on a single page.
  const short = paginateAdvisorQueue([1, 2, 3, 4, 5, 6, 7, 8], 1);
  assert.equal(short.totalPages, 1);
  assert.equal(short.pageItems.length, 8);
  assert.deepEqual([short.start, short.end], [0, 8]);

  // Empty list never produces a negative slice or page-0.
  const empty = paginateAdvisorQueue([], 1);
  assert.deepEqual([empty.page, empty.totalPages, empty.pageItems.length, empty.start, empty.end], [1, 1, 0, 0, 0]);
});

test("viewed_at reflects whether GVCN has opened the handoff (assigned = chưa xem)", () => {
  const cases = generateAdvisorDemoCases("gvcn", 0, NOW);
  for (const item of cases) {
    if (item.case_state === "assigned") {
      assert.equal(item.viewed_at, null, "assigned case must start unseen");
    } else {
      assert.ok(item.viewed_at, "a case past assigned must carry a viewed_at");
    }
  }

  const [assigned] = cases.filter((item) => item.case_state === "assigned");
  const viewed = markAdvisorDemoViewed(assigned, NOW);
  assert.equal(viewed.viewed_at, NOW.toISOString());
  // Idempotent: a second open does not overwrite the first view time.
  const later = new Date("2026-08-01T00:00:00.000Z");
  assert.equal(markAdvisorDemoViewed(viewed, later).viewed_at, NOW.toISOString());
});

test("handoff overdue = still assigned past the ack threshold; accepted cases clear it", () => {
  assert.equal(HANDOFF_ACK_OVERDUE_DAYS, 3);

  const [assigned] = generateAdvisorDemoCases("gvcn", 0, NOW).filter((item) => item.case_state === "assigned");
  const assignedAt = new Date(assigned.assigned_at);
  const dayMs = 86_400_000;

  const twoDaysLater = new Date(assignedAt.getTime() + 2 * dayMs);
  const fourDaysLater = new Date(assignedAt.getTime() + 4 * dayMs);

  assert.equal(handoffElapsedDays(assigned, twoDaysLater), 2);
  assert.equal(isHandoffOverdue(assigned, twoDaysLater), false, "within threshold is not overdue");
  assert.equal(isHandoffOverdue(assigned, fourDaysLater), true, "past threshold is overdue");

  // Accepting (assigned → follow_up_in_progress) clears the overdue signal.
  const accepted = transitionAdvisorDemoCase(assigned, "accept", fourDaysLater);
  assert.equal(isHandoffOverdue(accepted, fourDaysLater), false);

  const overdueCount = countOverdueHandoffs([assigned, accepted], fourDaysLater);
  assert.equal(overdueCount, 1, "only the still-assigned case counts as overdue");
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
