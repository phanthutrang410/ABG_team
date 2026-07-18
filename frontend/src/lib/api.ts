import type {
  AgentExplanation,
  AgentIntent,
  CaseAction,
  CaseDetailResponse,
  CaseListResponse,
  FairnessReport,
  PublicThresholdConfig,
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

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000").replace(/\/+$/, "");

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

export async function fetchReviewCases(signal?: AbortSignal): Promise<CaseListResponse> {
  try {
    const res = await fetch(`${API_BASE}/review-cases`, { cache: "no-store", signal });
    if (!res.ok) return UPSTREAM_UNAVAILABLE_LIST;
    const body = (await res.json()) as CaseListResponse;
    if (!body || typeof body.state !== "string") return UPSTREAM_UNAVAILABLE_LIST;
    return body;
  } catch {
    return UPSTREAM_UNAVAILABLE_LIST;
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
    const res = await fetch(`${API_BASE}/config/thresholds`, { cache: "no-store", signal });
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
    const res = await fetch(`${API_BASE}/config/thresholds/impact?${qs}`, { cache: "no-store", signal });
    if (!res.ok) return null;
    return (await res.json()) as ThresholdImpactResponse;
  } catch {
    return null;
  }
}

/** G04 — GET /fairness/report (MVP: status=insufficient_data, fail-closed). */
export async function fetchFairnessReport(signal?: AbortSignal): Promise<FairnessReport | null> {
  try {
    const res = await fetch(`${API_BASE}/fairness/report`, { cache: "no-store", signal });
    if (!res.ok) return null;
    return (await res.json()) as FairnessReport;
  } catch {
    return null;
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

export async function fetchReviewCase(caseId: string, signal?: AbortSignal): Promise<CaseDetailResponse> {
  try {
    const res = await fetch(`${API_BASE}/review-cases/${encodeURIComponent(caseId)}`, {
      cache: "no-store",
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
