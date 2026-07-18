import type { DemoAccount, Role } from "@/lib/types";

/** Render mode for legacy `/analysis` — never flash Ban quản lý UI for GVCN. */
export type AnalysisGate = "loading" | "gvcn_redirect" | "management";

export function resolveAnalysisGate(
  ready: boolean,
  activeRole: Role | null | undefined,
): AnalysisGate {
  if (!ready) return "loading";
  if (activeRole === "gvcn") return "gvcn_redirect";
  return "management";
}

/**
 * Client-side advisor route access (demo session only — not production RBAC).
 * Mirrors AppShell role guard outcomes for unit tests.
 */
export type AdvisorAccess = "loading" | "unauthenticated" | "wrong_role" | "ok";

export function resolveAdvisorAccess(
  ready: boolean,
  account: DemoAccount | null | undefined,
  activeRole: Role | null | undefined,
  requiredRole: Role = "gvcn",
): AdvisorAccess {
  if (!ready) return "loading";
  if (!account || !activeRole) return "unauthenticated";
  if (activeRole !== requiredRole) return "wrong_role";
  return "ok";
}

/**
 * Local/dev-only advisor UI fixtures. Always false in production builds so
 * localStorage generators never ship as the default Live URL path (H36 / G07).
 */
export function isAdvisorLocalDemoEnabled(): boolean {
  if (process.env.NODE_ENV === "production") return false;
  return process.env.NEXT_PUBLIC_ADVISOR_LOCAL_DEMO === "1";
}
