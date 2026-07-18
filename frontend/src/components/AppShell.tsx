"use client";

import { Suspense, useEffect, type CSSProperties, type ReactNode } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { roleHome, useSession } from "@/lib/session";
import { ROLE_ICON, ROLE_LABEL, type Role } from "@/lib/types";

/**
 * Khung trang + guard theo vai (demo, client-side — không phải bảo mật production).
 * Layout sidebar trái theo mockup 18/7: nav theo vai; dashboard tabs điều hướng
 * qua /dashboard?tab=… . Vào sai vai → đưa về màn đúng phạm vi của vai đang chọn.
 */

type NavItem = { label: string; icon: string; href: string; tab?: string };

/** Chỉ trang/tab đã có thật — không vẽ mục chết (Báo cáo/Cấu hình… chờ API). */
const NAV_BY_ROLE: Record<Role, NavItem[]> = {
  ban_quan_ly: [
    { label: "Tổng quan", icon: "🏠", href: "/dashboard?tab=overview", tab: "overview" },
    { label: "Tín hiệu", icon: "🛡️", href: "/dashboard?tab=signals", tab: "signals" },
    { label: "Sinh viên", icon: "👥", href: "/dashboard?tab=students", tab: "students" },
    { label: "Fairness", icon: "⚖️", href: "/dashboard?tab=fairness", tab: "fairness" },
    { label: "Ngưỡng", icon: "🎚️", href: "/dashboard?tab=threshold", tab: "threshold" },
  ],
  gvcn: [{ label: "Case của tôi", icon: "📋", href: "/my-class" }],
};

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
    <div style={{ display: "flex", minHeight: "100vh", background: "#f6f7f9", alignItems: "stretch" }}>
      <aside style={sidebar}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "0 14px", marginBottom: 18 }}>
          <span aria-hidden style={{ fontSize: 20 }}>🛡️</span>
          <span style={{ fontWeight: 700, fontSize: 16.5, color: "#2a78d6" }}>Silent Shield</span>
        </div>
        <Suspense fallback={null}>
          <SideNav items={NAV_BY_ROLE[role]} />
        </Suspense>
        <div style={{ marginTop: "auto", padding: "12px 14px", fontSize: 11.5, color: "#94a3b8", lineHeight: 1.5 }}>
          Dữ liệu pseudonymized · con người duyệt trước mọi bàn giao
        </div>
      </aside>

      <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
        <header style={topbar}>
          <div style={{ minWidth: 0 }}>
            <p style={{ margin: 0, color: "#94a3b8", fontSize: 12 }}>{ROLE_LABEL[role]}</p>
            <h1 style={{ margin: "0.1rem 0 0", fontSize: 19, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{title}</h1>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13, flexShrink: 0 }}>
            <span style={{ color: "#64748b" }}>{account.name}</span>
            {multi ? (
              <select
                value={role}
                onChange={(e) => {
                  const next = e.target.value as Role;
                  chooseRole(next);
                  router.push(roleHome(next));
                }}
                style={roleChipSelect}
                title="Đổi vai (trình diễn)"
              >
                {account.roles.map((r) => (
                  <option key={r} value={r}>
                    {ROLE_ICON[r]} {ROLE_LABEL[r]}
                  </option>
                ))}
              </select>
            ) : (
              <span style={roleChip}>
                {ROLE_ICON[role]} {ROLE_LABEL[role]}
              </span>
            )}
            <button
              onClick={() => {
                logout();
                router.push("/login");
              }}
              style={logoutBtn}
            >
              Đăng xuất
            </button>
          </div>
        </header>

        <main style={{ flex: 1, padding: "1.25rem 1.5rem 2rem", maxWidth: 1200, width: "100%", margin: "0 auto", boxSizing: "border-box" }}>
          {subtitle && <p style={{ margin: "0 0 1rem", color: "#475569", fontSize: 13.5 }}>{subtitle}</p>}
          {children}
        </main>
      </div>
    </div>
  );
}

/** Nav sidebar — active theo pathname + ?tab= (tách riêng vì useSearchParams cần Suspense). */
function SideNav({ items }: { items: NavItem[] }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const currentTab = searchParams.get("tab") ?? "overview";

  return (
    <nav style={{ display: "grid", gap: 2, padding: "0 8px" }} aria-label="Điều hướng chính">
      {items.map((item) => {
        const base = item.href.split("?")[0];
        const active = pathname === base && (item.tab === undefined || item.tab === currentTab);
        return (
          <Link key={item.href} href={item.href} style={{ ...navLink, ...(active ? navLinkActive : {}) }}>
            <span aria-hidden style={{ width: 20, textAlign: "center" }}>{item.icon}</span>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

const sidebar: CSSProperties = {
  width: 210,
  flexShrink: 0,
  background: "#fff",
  borderRight: "1px solid #e2e8f0",
  padding: "16px 0 12px",
  display: "flex",
  flexDirection: "column",
  position: "sticky",
  top: 0,
  alignSelf: "flex-start",
  minHeight: "100vh",
};
const topbar: CSSProperties = {
  background: "#fff",
  borderBottom: "1px solid #e2e8f0",
  padding: "10px 24px",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
  flexWrap: "wrap",
};
const navLink: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 9,
  padding: "9px 12px",
  borderRadius: 8,
  fontSize: 13.5,
  color: "#475569",
  textDecoration: "none",
};
const navLinkActive: CSSProperties = { background: "#eaf2fc", color: "#2a78d6", fontWeight: 600 };
const roleChip: CSSProperties = { padding: "3px 10px", borderRadius: 999, background: "#eef2ff", color: "#3730a3", fontWeight: 600 };
const roleChipSelect: CSSProperties = { padding: "3px 8px", borderRadius: 999, border: "1px solid #cbd5e1", background: "#eef2ff", fontWeight: 600, color: "#3730a3" };
const logoutBtn: CSSProperties = { padding: "3px 10px", borderRadius: 6, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", color: "#475569" };
