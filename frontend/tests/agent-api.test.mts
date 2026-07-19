import assert from "node:assert/strict";
import test from "node:test";

import { isAgentTurnResponse, postAgentTurnStream } from "../src/lib/api.ts";
import { isSupportedAgentAction } from "../src/lib/agent-routes.ts";

const VALID_OK = {
  status: "ok",
  answer_vi: "Mở báo cáo tổng quan.",
  evidence_refs: ["route:answer"],
  ui_actions: [
    {
      key: "open_overview_report",
      label_vi: "Xem báo cáo tổng quan",
      route_key: "overview.report",
    },
  ],
  refusal_reason: null,
  selected_capability: "open_overview_report",
};

test("Agent response validator enforces status invariants and selected card", () => {
  assert.equal(isAgentTurnResponse(VALID_OK), true);
  assert.equal(
    isAgentTurnResponse({ ...VALID_OK, status: "unavailable", selected_capability: null }),
    true,
  );
  assert.equal(isAgentTurnResponse({ ...VALID_OK, evidence_refs: undefined }), false);
  assert.equal(isAgentTurnResponse({ ...VALID_OK, ui_actions: [] }), false);
  assert.equal(
    isAgentTurnResponse({
      ...VALID_OK,
      status: "refused",
      refusal_reason: "sensitive_data_requested",
      selected_capability: null,
    }),
    false,
  );
});

test("shipped action registry rejects dead or relabelled cards", () => {
  assert.equal(isSupportedAgentAction(VALID_OK.ui_actions[0]), true);
  assert.equal(
    isSupportedAgentAction({
      key: "open_case_analysis",
      label_vi: "Xem phân tích case",
      route_key: "reports.weekly.case",
    }),
    false,
  );
  assert.equal(
    isSupportedAgentAction({ ...VALID_OK.ui_actions[0], label_vi: "Mở link khác" }),
    false,
  );
});

test("SSE error is terminal across CRLF frames", async () => {
  const originalFetch = globalThis.fetch;
  const encoder = new TextEncoder();
  const streamBody = [
    'event: error\r\ndata: {"message_vi":"Tạm thời lỗi"}\r\n\r\n',
    `event: done\r\ndata: ${JSON.stringify(VALID_OK)}\r\n\r\n`,
  ].join("");
  globalThis.fetch = async () =>
    new Response(
      new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(streamBody));
          controller.close();
        },
      }),
      { status: 200, headers: { "Content-Type": "text/event-stream" } },
    );

  try {
    let errors = 0;
    let dones = 0;
    const completed = await postAgentTurnStream(
      { surface: "overview", question: "Tóm tắt" },
      {
        onError: () => {
          errors += 1;
        },
        onDone: () => {
          dones += 1;
        },
      },
    );
    assert.equal(completed, false);
    assert.equal(errors, 1);
    assert.equal(dones, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
