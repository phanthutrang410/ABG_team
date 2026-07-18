"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { roleHome, useSession } from "@/lib/session";
import { ROLE_ICON, ROLE_LABEL, type Role } from "@/lib/types";

/**
 * Khung trang + guard theo vai (demo, client-side — không phải bảo mật production).
 * Vào sai vai → đưa về màn đúng phạm vi của vai đang chọn.
 */
export function AppShell({ role, title, subtitle, children }: { role: Role; title: string; subtitle?: string; children: ReactNode }) {
  const { account, activeRole, ready, chooseRole, logout } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (!ready) return;
    if (!account) router.replace("/login");
    else if (!activeRole) router.replace("/select-role");
    else if (activeRole !== role) router.replace(roleHome(activeRole));
  }, [ready, account, activeRole, role, router]);

  if (!ready || !account || activeRole !== role) {
    return <div style={{ padding: "3rem", textAlign: "center", color: "#94a3b8" }}>Đang tải…</div>;
  }

  const multi = account.roles.length > 1;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "1.25rem 1.5rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap", marginBottom: "1rem" }}>
        <div>
          <p style={{ margin: 0, color: "#64748b", fontSize: 13 }}>Silent Shield · {ROLE_LABEL[role]}</p>
          <h1 style={{ margin: "0.15rem 0 0", fontSize: 24 }}>{title}</h1>
          {subtitle && <p style={{ margin: "0.35rem 0 0", color: "#475569", fontSize: 14 }}>{subtitle}</p>}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13 }}>
          <span style={{ color: "#64748b" }}>{account.name}</span>
          {multi ? (
            <select
              value={role}
              onChange={(e) => {
                const next = e.target.value as Role;
                chooseRole(next);
                router.push(roleHome(next));
              }}
              style={{ padding: "3px 8px", borderRadius: 999, border: "1px solid #cbd5e1", background: "#eef2ff", fontWeight: 600, color: "#3730a3" }}
              title="Đổi vai (trình diễn)"
            >
              {account.roles.map((r) => (
                <option key={r} value={r}>
                  {ROLE_ICON[r]} {ROLE_LABEL[r]}
                </option>
              ))}
            </select>
          ) : (
            <span style={{ padding: "3px 10px", borderRadius: 999, background: "#eef2ff", color: "#3730a3", fontWeight: 600 }}>
              {ROLE_ICON[role]} {ROLE_LABEL[role]}
            </span>
          )}
          <button
            onClick={() => {
              logout();
              router.push("/login");
            }}
            style={{ padding: "3px 10px", borderRadius: 6, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", color: "#475569" }}
          >
            Đăng xuất
          </button>
        </div>
      </div>
      {children}
    </div>
  );
}
