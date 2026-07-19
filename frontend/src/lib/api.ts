import type {
  AdvisorHandoffDraftListResponse,
  AdvisorRosterResponse,
  AgentExplanation,
  AgentIntent,
  AgentTurnRequest,
  AgentTurnResponse,
  AgentTurnStreamHandlers,
  AuthMeResponse,
  CaseAction,
  CaseDetailResponse,
  CaseListResponse,
  FairnessReport,
  PublicThresholdConfig,
  ReviewOverviewSummary,
  ThresholdImpactResponse,
  TransitionErrorBody,
  TransitionResponse,
  TransitionResult,
} from "@/lib/types";

/**
 * G02 — real fetch client for GET /review-cases (H02, consumes H11a envelopes).
 * Network/parse failure maps to the SAME error envelope shape the backend itself
 * returns (see backend/app/cases/review_router.py _list_error/_detail_error) —
 * fail-closed, never fabricate items or a band (RULES / AGENTS §C.5).
 */

// Empty string = same-origin (Vercel rewrite → BACKEND_URL). Local default via
// next.config env / .env.local is http://localhost:8000.
const API_BASE = (process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);

const ADVISOR_HANDOFF_DRAFTS_URL =
  process.env.NEXT_PUBLIC_ADVISOR_HANDOFF_DRAFTS_URL?.trim() ||
  `${API_BASE}/advisor-handoff-drafts`;

const UPSTREAM_UNAVAILABLE_LIST: CaseListResponse = {
  items: [],
  state: "error",
  problem: { code: "upstream_unavailable", reason_codes: [], message_key: null },
};

const UPSTREAM_UNAVAILABLE_DETAIL: CaseDetailResponse = {
  case: null,
  state: "error",
  freshness: "fresh",
  problem: { code: "upstream_unavailable", reason_codes: [], message_key: null },
};

export function apiBase(): string {
  return API_BASE;
}

/** Cookie session fetches — must include credentials for ``ss_session``. */
const CREDENTIALS: RequestInit = { credentials: "include", cache: "no-store" };

export type AuthApiError = {
  status: number;
  code: string | null;
  message: string | null;
};

function authErrorFromResponse(status: number, body: unknown): AuthApiError {
  const detail =
    body && typeof body === "object" && "detail" in body
      ? (body as { detail: unknown }).detail
      : null;
  if (detail && typeof detail === "object" && detail !== null && "code" in detail) {
    const d = detail as { code?: unknown; message?: unknown };
    return {
      status,
      code: typeof d.code === "string" ? d.code : null,
      message: typeof d.message === "string" ? d.message : null,
    };
  }
  return { status, code: null, message: null };
}

/** POST /auth/login — sets HttpOnly ``ss_session`` cookie. */
export async function postAuthLogin(
  username: string,
  password: string,
): Promise<{ ok: true; data: AuthMeResponse } | { ok: false; error: AuthApiError }> {
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      ...CREDENTIALS,
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const body = await res.json().catch(() => null);
    if (res.ok && body && typeof body.account_id === "string") {
      return { ok: true, data: body as AuthMeResponse };
    }
    return { ok: false, error: authErrorFromResponse(res.status, body) };
  } catch {
    return { ok: false, error: { status: 0, code: "upstream_unavailable", message: null } };
  }
}

/** GET /auth/me — null when unauthenticated / transport failure. */
export async function fetchAuthMe(signal?: AbortSignal): Promise<AuthMeResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, { ...CREDENTIALS, signal });
    if (!res.ok) return null;
    const body = (await res.json()) as AuthMeResponse;
    if (!body || typeof body.account_id !== "string") return null;
    return body;
  } catch {
    return null;
  }
}

/** POST /auth/active-role — multi-role accounts must select before scoped APIs. */
export async function postAuthActiveRole(
  role: string,
): Promise<{ ok: true; data: AuthMeResponse } | { ok: false; error: AuthApiError }> {
  try {
    const res = await fetch(`${API_BASE}/auth/active-role`, {
      ...CREDENTIALS,
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role }),
    });
    const body = await res.json().catch(() => null);
    if (res.ok && body && typeof body.account_id === "string") {
      return { ok: true, data: body as AuthMeResponse };
    }
    return { ok: false, error: authErrorFromResponse(res.status, body) };
  } catch {
    return { ok: false, error: { status: 0, code: "upstream_unavailable", message: null } };
  }
}

/** POST /auth/logout — revokes session + clears cookie (204). */
export async function postAuthLogout(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/auth/logout`, {
      ...CREDENTIALS,
      method: "POST",
    });
    return res.status === 204 || res.ok;
  } catch {
    return false;
  }
}

/** G08 consumer — GET /weekly-reports/latest (auth required). */
export async function fetchWeeklyReportLatest(
  branch: "semester" | "attendance" = "semester",
  signal?: AbortSignal,
): Promise<unknown | null> {
  try {
    const qs = new URLSearchParams({ branch });
    const res = await fetch(`${API_BASE}/weekly-reports/latest?${qs}`, {
      ...CREDENTIALS,
      signal,
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/** G08 consumer — GET /weekly-briefings/latest (auth + active role). */
export async function fetchWeeklyBriefingLatest(
  branch: "semester" | "attendance" = "semester",
  signal?: AbortSignal,
): Promise<unknown | null> {
  try {
    const qs = new URLSearchParams({ branch });
    const res = await fetch(`${API_BASE}/weekly-briefings/latest?${qs}`, {
      ...CREDENTIALS,
      signal,
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchReviewCases(signal?: AbortSignal): Promise<CaseListResponse> {
  try {
    const res = await fetch(`${API_BASE}/review-cases`, { ...CREDENTIALS, signal });
    if (!res.ok) return UPSTREAM_UNAVAILABLE_LIST;
    const body = (await res.json()) as CaseListResponse;
    if (!body || typeof body.state !== "string") return UPSTREAM_UNAVAILABLE_LIST;
    return body;
  } catch {
    return UPSTREAM_UNAVAILABLE_LIST;
  }
}

/** GET /advisor/roster — server-scoped; fail-closed empty/error envelope. */
export async function fetchAdvisorRoster(
  signal?: AbortSignal,
): Promise<AdvisorRosterResponse> {
  const fail: AdvisorRosterResponse = {
    state: "error",
    classes: [],
    problem: { code: "upstream_unavailable" },
  };
  try {
    const res = await fetch(`${API_BASE}/advisor/roster`, { ...CREDENTIALS, signal });
    if (!res.ok) return fail;
    const body = (await res.json()) as AdvisorRosterResponse;
    if (!body || typeof body.state !== "string" || !Array.isArray(body.classes)) return fail;
    return body;
  } catch {
    return fail;
  }
}

/**
 * Organization aggregate for /overview. null is fail-closed: the caller must
 * not derive the roster denominator from the review-case list.
 */
export async function fetchReviewOverviewSummary(
  signal?: AbortSignal,
): Promise<ReviewOverviewSummary | null> {
  try {
    const res = await fetch(`${API_BASE}/review-cases/summary`, { ...CREDENTIALS, signal });
    if (!res.ok) return null;
    const body = (await res.json()) as ReviewOverviewSummary;
    if (
      !body ||
      typeof body.state !== "string" ||
      body.scope !== "organization" ||
      typeof body.source_id !== "string" ||
      typeof body.total_students !== "number" ||
      typeof body.review_case_count !== "number" ||
      typeof body.review_student_count !== "number" ||
      !body.priority_band_counts ||
      !body.case_state_counts ||
      !body.student_coverage_counts ||
      !body.review_data_state_counts
    ) {
      return null;
    }
    return body;
  } catch {
    return null;
  }
}

/**
 * G03 — POST /cases/{id}/transitions (H03 care workflow).
 * Server derives the trusted actor (app/cases/auth.py) — we do NOT send
 * actor/actor_kind, and never send advisor_ref (assign resolves via H08).
 */
export async function postCaseTransition(
  caseId: string,
  payload: {
    action: CaseAction;
    reason_code?: string;
    review_at?: string;
    monitoring_until?: string;
  },
): Promise<TransitionResult> {
  try {
    const res = await fetch(`${API_BASE}/cases/${encodeURIComponent(caseId)}/transitions`, {
      ...CREDENTIALS,
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await res.json().catch(() => null);
    if (res.ok && body && typeof body.state === "string") {
      return { ok: true, data: body as TransitionResponse };
    }
    // FastAPI wraps TransitionErrorBody in {detail: {...}}; plain {detail: "..."} for 404.
    const detail = body?.detail;
    if (detail && typeof detail === "object" && typeof detail.code === "string") {
      return { ok: false, error: detail as TransitionErrorBody };
    }
    return { ok: false, error: null };
  } catch {
    return { ok: false, error: null };
  }
}

/** G04 — GET /config/thresholds (H04). null = upstream unavailable (fail-closed hiển thị lỗi). */
export async function fetchThresholds(signal?: AbortSignal): Promise<PublicThresholdConfig | null> {
  try {
    const res = await fetch(`${API_BASE}/config/thresholds`, { ...CREDENTIALS, signal });
    if (!res.ok) return null;
    return (await res.json()) as PublicThresholdConfig;
  } catch {
    return null;
  }
}

/** G04 — GET /config/thresholds/impact (aggregate counts only). */
export async function fetchThresholdImpact(
  tauCase: number,
  tauHigh: number,
  signal?: AbortSignal,
): Promise<ThresholdImpactResponse | null> {
  try {
    const qs = new URLSearchParams({ tau_case: String(tauCase), tau_high: String(tauHigh) });
    const res = await fetch(`${API_BASE}/config/thresholds/impact?${qs}`, { ...CREDENTIALS, signal });
    if (!res.ok) return null;
    return (await res.json()) as ThresholdImpactResponse;
  } catch {
    return null;
  }
}

/** G04 — GET /fairness/report (MVP: status=insufficient_data, fail-closed). */
export async function fetchFairnessReport(signal?: AbortSignal): Promise<FairnessReport | null> {
  try {
    const res = await fetch(`${API_BASE}/fairness/report`, { ...CREDENTIALS, signal });
    if (!res.ok) return null;
    return (await res.json()) as FairnessReport;
  } catch {
    return null;
  }
}

/**
 * H37 — POST /agent/turns (Global Agent). Cookie session; browser only sends
 * surface / optional handle / current question — never raw case context/history.
 * null = transport/parse failure → UI fail-closed copy.
 */
export async function postAgentTurn(
  payload: Omit<AgentTurnRequest, "locale"> & { locale?: "vi" },
  signal?: AbortSignal,
): Promise<AgentTurnResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/agent/turns`, {
      ...CREDENTIALS,
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        surface: payload.surface,
        resource_handle: payload.resource_handle ?? null,
        question: payload.question ?? null,
        locale: payload.locale ?? "vi",
      } satisfies AgentTurnRequest),
      signal,
    });
    if (!res.ok) return null;
    const body = await res.json();
    return isAgentTurnResponse(body) ? body : null;
  } catch {
    return null;
  }
}

const AGENT_STREAM_FAIL_VI =
  "Máy chủ tạm thời không phản hồi. Chưa có câu trả lời từ trợ lý — vui lòng thử lại sau.";

const AGENT_REFUSAL_REASONS = new Set([
  "forbidden_tool_requested",
  "out_of_scope_surface",
  "prompt_injection_detected",
  "arbitrary_url_or_sql_requested",
  "sensitive_data_requested",
  "unsafe_inference_requested",
]);

export function isAgentTurnResponse(body: unknown): body is AgentTurnResponse {
  if (!body || typeof body !== "object") return false;
  const b = body as Record<string, unknown>;
  if (
    (b.status !== "ok" && b.status !== "refused" && b.status !== "unavailable")
    || typeof b.answer_vi !== "string"
    || b.answer_vi.trim().length === 0
    || !Array.isArray(b.evidence_refs)
    || !b.evidence_refs.every((ref) => typeof ref === "string")
    || !Array.isArray(b.ui_actions)
    || !b.ui_actions.every(
      (action) =>
        action !== null
        && typeof action === "object"
        && typeof (action as Record<string, unknown>).key === "string"
        && typeof (action as Record<string, unknown>).label_vi === "string"
        && typeof (action as Record<string, unknown>).route_key === "string",
    )
    || (b.selected_capability !== null && typeof b.selected_capability !== "string")
  ) {
    return false;
  }

  const actions = b.ui_actions as Array<Record<string, unknown>>;
  if (b.status === "refused") {
    return (
      typeof b.refusal_reason === "string"
      && AGENT_REFUSAL_REASONS.has(b.refusal_reason)
      && actions.length === 0
      && b.selected_capability === null
    );
  }
  if (b.refusal_reason !== null) return false;
  if (b.status === "unavailable" && b.selected_capability !== null) return false;
  if (
    typeof b.selected_capability === "string"
    && !actions.some((action) => action.key === b.selected_capability)
  ) {
    return false;
  }
  return true;
}

/**
 * H37 stream — POST /agent/turns/stream (SSE). Same request body as postAgentTurn.
 * Status phases → faux answer deltas (post-guard) → done. Uses fetch (not EventSource)
 * so cookies + POST body work.
 */
export async function postAgentTurnStream(
  payload: Omit<AgentTurnRequest, "locale"> & { locale?: "vi" },
  handlers: AgentTurnStreamHandlers,
  signal?: AbortSignal,
): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/agent/turns/stream`, {
      ...CREDENTIALS,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({
        surface: payload.surface,
        resource_handle: payload.resource_handle ?? null,
        question: payload.question ?? null,
        locale: payload.locale ?? "vi",
      } satisfies AgentTurnRequest),
      signal,
    });
    if (!res.ok || !res.body) {
      handlers.onError?.(AGENT_STREAM_FAIL_VI);
      return false;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let terminal: "done" | "error" | null = null;

    const dispatchBlock = (block: string) => {
      if (terminal !== null) return;
      const trimmed = block.trim();
      if (!trimmed) return;
      let eventName = "message";
      const dataLines: string[] = [];
      for (const line of trimmed.split(/\r?\n/)) {
        if (line.startsWith("event:")) {
          eventName = line.slice("event:".length).trim();
        } else if (line.startsWith("data:")) {
          dataLines.push(line.slice("data:".length).trim());
        }
      }
      if (dataLines.length === 0) return;
      let payloadJson: unknown;
      try {
        payloadJson = JSON.parse(dataLines.join("\n"));
      } catch {
        return;
      }
      if (eventName === "status") {
        const phase =
          payloadJson && typeof payloadJson === "object" && "phase" in payloadJson
            ? String((payloadJson as { phase: unknown }).phase)
            : "";
        if (phase) handlers.onStatus?.(phase);
        return;
      }
      if (eventName === "delta") {
        const text =
          payloadJson && typeof payloadJson === "object" && "text" in payloadJson
            ? String((payloadJson as { text: unknown }).text ?? "")
            : "";
        if (text) handlers.onDelta?.(text);
        return;
      }
      if (eventName === "done") {
        if (isAgentTurnResponse(payloadJson)) {
          terminal = "done";
          handlers.onDone?.(payloadJson);
        } else {
          terminal = "error";
          handlers.onError?.(AGENT_STREAM_FAIL_VI);
        }
        return;
      }
      if (eventName === "error") {
        const msg =
          payloadJson && typeof payloadJson === "object" && "message_vi" in payloadJson
            ? String((payloadJson as { message_vi: unknown }).message_vi || AGENT_STREAM_FAIL_VI)
            : AGENT_STREAM_FAIL_VI;
        terminal = "error";
        handlers.onError?.(msg);
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split(/\r?\n\r?\n/);
      buffer = parts.pop() ?? "";
      for (const part of parts) dispatchBlock(part);
    }
    buffer += decoder.decode();
    if (buffer.trim()) dispatchBlock(buffer);

    if (terminal !== "done") {
      if (terminal === "error") return false;
      handlers.onError?.(AGENT_STREAM_FAIL_VI);
      return false;
    }
    return true;
  } catch {
    if (signal?.aborted) return false;
    handlers.onError?.(AGENT_STREAM_FAIL_VI);
    return false;
  }
}

/**
 * H24 — POST /review-cases/{id}/explanation. Body = AgentCommand only
 * (intent/question/locale); context được server dựng, browser KHÔNG gửi.
 * null = transport failure → UI hiển thị cùng copy fail-closed "unavailable".
 */
export async function postAgentExplanation(
  caseId: string,
  payload: { intent: AgentIntent; question: string },
  signal?: AbortSignal,
): Promise<AgentExplanation | null> {
  try {
    const res = await fetch(`${API_BASE}/review-cases/${encodeURIComponent(caseId)}/explanation`, {
      ...CREDENTIALS,
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...payload, locale: "vi" }),
      signal,
    });
    if (!res.ok) return null;
    const body = (await res.json()) as AgentExplanation;
    if (!body || typeof body.status !== "string" || typeof body.answer_vi !== "string") return null;
    return body;
  } catch {
    return null;
  }
}

/**
 * F6 / G06 — GET /advisor-handoff-drafts (H22, FR-12). Draft-only: KHÔNG có
 * endpoint send. Lỗi transport → cùng error envelope fail-closed (không bịa
 * bundle/draft). advisor_ref chỉ hợp lệ trên envelope này (H11a exception).
 */
const UPSTREAM_UNAVAILABLE_HANDOFF: AdvisorHandoffDraftListResponse = {
  state: "error",
  bundles: [],
  mapping_repair: { case_count: 0, cases: [], limitations: [] },
  problem: { code: "upstream_unavailable", reason_codes: [], message_key: null },
};

export async function fetchAdvisorHandoffDrafts(
  signal?: AbortSignal,
): Promise<AdvisorHandoffDraftListResponse> {
  try {
    const res = await fetch(ADVISOR_HANDOFF_DRAFTS_URL, { ...CREDENTIALS, signal });
    if (!res.ok) return UPSTREAM_UNAVAILABLE_HANDOFF;
    const body = (await res.json()) as AdvisorHandoffDraftListResponse;
    if (!body || typeof body.state !== "string") return UPSTREAM_UNAVAILABLE_HANDOFF;
    return body;
  } catch {
    return UPSTREAM_UNAVAILABLE_HANDOFF;
  }
}

/**
 * GVCN advisor flow — GET /cases/{id} returns the narrow workflow surface
 * (state + viewed_at + updated_at), NOT the public ReviewCase. null is
 * fail-closed: 404/403/transport failure → caller shows no receipt/actions.
 */
export async function fetchCaseWorkflow(
  caseId: string,
  signal?: AbortSignal,
): Promise<TransitionResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/cases/${encodeURIComponent(caseId)}`, {
      ...CREDENTIALS,
      signal,
    });
    if (!res.ok) return null;
    const body = (await res.json()) as TransitionResponse;
    if (!body || typeof body.case_id !== "string" || typeof body.state !== "string") return null;
    return body;
  } catch {
    return null;
  }
}

/**
 * POST /cases/{id}/viewed — GVCN-only, idempotent "đã xem" receipt logged when the
 * advisor opens the secured detail. Distinct from acceptance (accept transition).
 * null when 403 (not gvcn) / 404 (out of scope) / transport failure — never a state change.
 */
export async function postCaseViewed(
  caseId: string,
  signal?: AbortSignal,
): Promise<TransitionResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/cases/${encodeURIComponent(caseId)}/viewed`, {
      ...CREDENTIALS,
      method: "POST",
      signal,
    });
    if (!res.ok) return null;
    const body = (await res.json()) as TransitionResponse;
    if (!body || typeof body.case_id !== "string" || typeof body.state !== "string") return null;
    return body;
  } catch {
    return null;
  }
}

export async function fetchReviewCase(caseId: string, signal?: AbortSignal): Promise<CaseDetailResponse> {
  try {
    const res = await fetch(`${API_BASE}/review-cases/${encodeURIComponent(caseId)}`, {
      ...CREDENTIALS,
      signal,
    });
    if (!res.ok) return UPSTREAM_UNAVAILABLE_DETAIL;
    const body = (await res.json()) as CaseDetailResponse;
    if (!body || typeof body.state !== "string") return UPSTREAM_UNAVAILABLE_DETAIL;
    return body;
  } catch {
    return UPSTREAM_UNAVAILABLE_DETAIL;
  }
}
