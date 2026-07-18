"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import {
  fetchAuthMe,
  postAuthActiveRole,
  postAuthLogin,
  postAuthLogout,
} from "@/lib/api";
import { isAdvisorLocalDemoEnabled } from "@/lib/advisor-routing";
import type { AuthMeResponse, DemoAccount, Role, SessionAccount } from "@/lib/types";

/**
 * G07 — session prefers server cookie auth (H39 `/auth/*`, ``ss_session``).
 * Local demo fixtures + localStorage remain only when
 * ``NEXT_PUBLIC_ADVISOR_LOCAL_DEMO=1`` in non-production (fail-closed otherwise).
 */

export const DEMO_ACCOUNTS: DemoAccount[] = [
  { id: "quanly", name: "TS. Nam | Giám sát học tập", password: "demo123", roles: ["ban_quan_ly"] },
  { id: "gvcn", name: "CVHT Lan | K66-CNTT-A", password: "demo123", roles: ["gvcn"] },
  { id: "demo", name: "ThS. Minh Anh | Quản lý học tập", password: "demo123", roles: ["ban_quan_ly", "gvcn"] },
];

type AuthSource = "server" | "demo";

type SessionState = {
  account: SessionAccount | null;
  activeRole: Role | null;
  source: AuthSource | null;
};

export type LoginResult =
  | { ok: true; account: SessionAccount; activeRole: Role | null }
  | { ok: false; message: string };

type SessionCtx = SessionState & {
  ready: boolean;
  login: (username: string, password: string) => Promise<LoginResult>;
  chooseRole: (role: Role) => Promise<boolean>;
  logout: () => Promise<void>;
};

const DEMO_KEY = "silentshield.session.v2";
const Ctx = createContext<SessionCtx | null>(null);

const VALID_ROLES: ReadonlySet<string> = new Set(["ban_quan_ly", "gvcn"]);

function asRole(value: string | null | undefined): Role | null {
  if (value === "ban_quan_ly" || value === "gvcn") return value;
  return null;
}

function rolesFromMe(roles: string[]): Role[] {
  return roles.filter((r): r is Role => VALID_ROLES.has(r));
}

function accountFromMe(me: AuthMeResponse): SessionAccount | null {
  const roles = rolesFromMe(me.roles);
  if (!roles.length) return null;
  return {
    id: me.account_id,
    name: me.display_name,
    roles,
  };
}

function readDemoStorage(): SessionState | null {
  try {
    const raw = localStorage.getItem(DEMO_KEY);
    if (!raw) return null;
    const stored = JSON.parse(raw) as { accountId?: string; activeRole?: Role | null };
    const demo = DEMO_ACCOUNTS.find((item) => item.id === stored.accountId) ?? null;
    if (!demo) return null;
    const validRole =
      stored.activeRole && demo.roles.includes(stored.activeRole) ? stored.activeRole : null;
    return {
      account: { id: demo.id, name: demo.name, roles: demo.roles },
      activeRole: validRole,
      source: "demo",
    };
  } catch {
    return null;
  }
}

function writeDemoStorage(accountId: string | null, activeRole: Role | null) {
  try {
    if (accountId) localStorage.setItem(DEMO_KEY, JSON.stringify({ accountId, activeRole }));
    else localStorage.removeItem(DEMO_KEY);
  } catch {
    /* ignore */
  }
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<SessionState>({
    account: null,
    activeRole: null,
    source: null,
  });
  const [ready, setReady] = useState(false);
  const stateRef = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const me = await fetchAuthMe();
      if (cancelled) return;
      if (me) {
        const account = accountFromMe(me);
        if (account) {
          setState({
            account,
            activeRole: asRole(me.active_role),
            source: "server",
          });
          setReady(true);
          return;
        }
      }
      if (isAdvisorLocalDemoEnabled()) {
        const demo = readDemoStorage();
        if (demo) setState(demo);
      }
      setReady(true);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (username: string, password: string): Promise<LoginResult> => {
    const result = await postAuthLogin(username.trim(), password);
    if (result.ok) {
      const account = accountFromMe(result.data);
      if (!account) {
        return { ok: false, message: "Tài khoản không có vai trò hợp lệ." };
      }
      const activeRole = asRole(result.data.active_role);
      writeDemoStorage(null, null);
      setState({ account, activeRole, source: "server" });
      return { ok: true, account, activeRole };
    }

    if (isAdvisorLocalDemoEnabled()) {
      const acc =
        DEMO_ACCOUNTS.find((a) => a.id === username.trim().toLowerCase()) ?? null;
      if (acc && acc.password === password) {
        const activeRole = acc.roles.length === 1 ? acc.roles[0] : null;
        writeDemoStorage(acc.id, activeRole);
        const account: SessionAccount = { id: acc.id, name: acc.name, roles: acc.roles };
        setState({ account, activeRole, source: "demo" });
        return { ok: true, account, activeRole };
      }
    }

    const code = result.error.code;
    if (code === "invalid_credentials" || result.error.status === 401) {
      return { ok: false, message: "Tài khoản hoặc mật khẩu không đúng." };
    }
    if (code === "account_disabled") {
      return { ok: false, message: "Tài khoản đã bị vô hiệu hóa." };
    }
    if (code === "upstream_unavailable" || result.error.status === 0) {
      return {
        ok: false,
        message: "Không kết nối được máy chủ xác thực. Vui lòng thử lại.",
      };
    }
    return { ok: false, message: "Đăng nhập không thành công. Vui lòng thử lại." };
  }, []);

  const chooseRole = useCallback(async (role: Role): Promise<boolean> => {
    const current = stateRef.current;
    if (!current.account?.roles.includes(role)) return false;

    if (current.source === "server") {
      const result = await postAuthActiveRole(role);
      if (!result.ok) return false;
      const account = accountFromMe(result.data);
      if (!account) return false;
      setState({
        account,
        activeRole: asRole(result.data.active_role) ?? role,
        source: "server",
      });
      return true;
    }

    if (current.source === "demo" && isAdvisorLocalDemoEnabled()) {
      writeDemoStorage(current.account.id, role);
      setState({ ...current, activeRole: role });
      return true;
    }

    return false;
  }, []);

  const logout = useCallback(async () => {
    if (stateRef.current.source === "server") {
      await postAuthLogout();
    }
    writeDemoStorage(null, null);
    setState({ account: null, activeRole: null, source: null });
  }, []);

  const value: SessionCtx = {
    ...state,
    ready,
    login,
    chooseRole,
    logout,
  };

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSession(): SessionCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}

export function roleHome(role: Role): string {
  return role === "gvcn" ? "/advisor" : "/overview";
}

/**
 * Tách tên hiển thị thành {name, subtitle}.
 * Hỗ trợ "|" (demo) và "—" / " - " (seed H39).
 */
export function splitAccountName(fullName: string): { name: string; subtitle: string } {
  for (const sep of ["|", "—", " - "]) {
    const idx = fullName.indexOf(sep);
    if (idx !== -1) {
      return { name: fullName.slice(0, idx).trim(), subtitle: fullName.slice(idx + sep.length).trim() };
    }
  }
  return { name: fullName.trim(), subtitle: "" };
}

/** Chữ cái đầu của từ cuối trong tên ngắn (placeholder avatar). */
export function initialsFromName(shortName: string): string {
  const words = shortName.replace(/[.]/g, "").trim().split(/\s+/).filter(Boolean);
  return words.length ? words[words.length - 1][0].toUpperCase() : "?";
}
