"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { DemoAccount, Role } from "@/lib/types";

/**
 * Phiên DEMO (không phải auth thật — RBAC production ngoài scope, PRD §9).
 * Mô phỏng: đăng nhập tài khoản/mật khẩu fixture → vai → guard route client-side.
 * Mật khẩu là fixture công khai hiển thị ngay trên màn login.
 */

export const DEMO_ACCOUNTS: DemoAccount[] = [
  { id: "quanly", name: "TS. Nam | Giám sát học tập", password: "demo123", roles: ["ban_quan_ly"] },
  { id: "gvcn", name: "CVHT Lan | K66-CNTT-A", password: "demo123", roles: ["gvcn"] },
  { id: "demo", name: "ThS. Minh Anh | Quản lý học tập", password: "demo123", roles: ["ban_quan_ly", "gvcn"] },
];

type SessionState = { accountId: string | null; activeRole: Role | null };

type SessionCtx = SessionState & {
  account: DemoAccount | null;
  ready: boolean;
  login: (accountId: string) => DemoAccount | null;
  chooseRole: (role: Role) => void;
  logout: () => void;
};

const KEY = "silentshield.session.v2";
const Ctx = createContext<SessionCtx | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<SessionState>({ accountId: null, activeRole: null });
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) setState(JSON.parse(raw) as SessionState);
    } catch {
      /* ignore */
    }
    setReady(true);
  }, []);

  function persist(next: SessionState) {
    setState(next);
    try {
      if (next.accountId) localStorage.setItem(KEY, JSON.stringify(next));
      else localStorage.removeItem(KEY);
    } catch {
      /* ignore */
    }
  }

  const account = DEMO_ACCOUNTS.find((a) => a.id === state.accountId) ?? null;

  const value: SessionCtx = {
    ...state,
    account,
    ready,
    login: (accountId) => {
      const acc = DEMO_ACCOUNTS.find((a) => a.id === accountId) ?? null;
      persist({ accountId: acc?.id ?? null, activeRole: acc && acc.roles.length === 1 ? acc.roles[0] : null });
      return acc;
    },
    chooseRole: (role) => persist({ ...state, activeRole: role }),
    logout: () => persist({ accountId: null, activeRole: null }),
  };

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSession(): SessionCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}

export function roleHome(role: Role): string {
  return role === "gvcn" ? "/analysis" : "/overview";
}

/**
 * Tách tên hiển thị "TS. Nam | Giám sát học tập" thành {name, subtitle}.
 * Dùng cho avatar/hero: dòng tên ngắn + dòng vai. Không có "|" → subtitle rỗng.
 */
export function splitAccountName(fullName: string): { name: string; subtitle: string } {
  const idx = fullName.indexOf("|");
  if (idx === -1) return { name: fullName.trim(), subtitle: "" };
  return { name: fullName.slice(0, idx).trim(), subtitle: fullName.slice(idx + 1).trim() };
}

/** Chữ cái đầu của từ cuối trong tên ngắn (placeholder avatar demo). */
export function initialsFromName(shortName: string): string {
  const words = shortName.replace(/[.]/g, "").trim().split(/\s+/).filter(Boolean);
  return words.length ? words[words.length - 1][0].toUpperCase() : "?";
}
