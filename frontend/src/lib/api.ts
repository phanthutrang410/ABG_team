import type { CaseDetailResponse, CaseListResponse } from "@/lib/types";

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
