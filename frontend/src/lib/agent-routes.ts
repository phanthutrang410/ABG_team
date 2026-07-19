/**
 * FE allowlist for Global Agent ``ui_actions[].route_key`` (overview slice).
 * Backend issues keys; FE must reject anything outside this map — never trust
 * model-invented URLs.
 */

import type { AgentRouteKey } from "@/lib/types";

/** Query that OverviewHeader watches to open ReportModal after navigate. */
export const OVERVIEW_REPORT_QUERY = "report";
export const OVERVIEW_REPORT_VALUE = "1";

const ROUTE_KEY_HREFS: Record<AgentRouteKey, string> = {
  "overview.report": `/overview?${OVERVIEW_REPORT_QUERY}=${OVERVIEW_REPORT_VALUE}`,
  "analysis.reviews": "/analysis?tab=reviews",
  notify: "/notify",
};

/** Capabilities that auto-navigate when selected for a turn. */
export const NAV_CAPABILITIES: ReadonlySet<string> = new Set([
  "open_overview_report",
  "open_review_list",
  "open_advisor_drafts",
]);

const CAPABILITY_TO_ROUTE_KEY: Record<string, AgentRouteKey> = {
  open_overview_report: "overview.report",
  open_review_list: "analysis.reviews",
  open_advisor_drafts: "notify",
};

export function isAgentRouteKey(value: string): value is AgentRouteKey {
  return Object.prototype.hasOwnProperty.call(ROUTE_KEY_HREFS, value);
}

/** Resolve href for an allowlisted route_key; null if unknown (reject). */
export function hrefForAgentRouteKey(routeKey: string): string | null {
  if (!isAgentRouteKey(routeKey)) return null;
  return ROUTE_KEY_HREFS[routeKey];
}

type RouterPush = { push: (href: string) => void };

/**
 * Navigate via allowlist only. Returns false when the key is unknown —
 * caller must not invent a fallback URL.
 */
export function navigateAgentRouteKey(router: RouterPush, routeKey: string): boolean {
  const href = hrefForAgentRouteKey(routeKey);
  if (!href) return false;
  router.push(href);
  return true;
}

/** Map selected_capability → allowlisted route_key when it is a nav tool. */
export function routeKeyForCapability(capability: string | null | undefined): AgentRouteKey | null {
  if (!capability || !NAV_CAPABILITIES.has(capability)) return null;
  return CAPABILITY_TO_ROUTE_KEY[capability] ?? null;
}

/** Page → surface for POST /agent/turns (deny-by-default server registry). */
export function surfaceFromPathname(pathname: string): string {
  if (pathname.startsWith("/notify")) return "advisor_drafts";
  if (pathname.startsWith("/analysis/") || pathname.startsWith("/cases/")) return "case_analysis";
  if (pathname.startsWith("/advisor")) return "case_analysis";
  if (pathname === "/overview" || pathname.startsWith("/overview")) return "overview";
  if (pathname.startsWith("/analysis")) return "overview";
  return "overview";
}

export function resourceHandleFromPathname(pathname: string): string | null {
  const analysisMatch = pathname.match(/^\/analysis\/([^/]+)$/);
  if (analysisMatch) return analysisMatch[1];
  const casesMatch = pathname.match(/^\/cases\/([^/]+)$/);
  if (casesMatch) return casesMatch[1];
  return null;
}
