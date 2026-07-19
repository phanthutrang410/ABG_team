"use client";

import {
  Suspense,
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AgentDrawer } from "@/components/AgentDrawer";
import { AgentFab } from "@/components/AgentFab";
import { initialsFromName, roleHome, splitAccountName, useSession } from "@/lib/session";
import { ROLE_LABEL, type Role, type SessionAccount } from "@/lib/types";

/**
 * Khung trang + guard theo vai (client shell).
 * Identity/role production: cookie session H39 via SessionProvider — không tin
 * client-declared role cho API; redirect khi chưa đăng nhập hoặc sai vai.
 */

/* ---------- TopbarInfo: trang con bơm dữ liệu thật lên topbar của shell ---------- */

type TopbarInfo = { updatedAt: string | null; alertCount: number };
const TopbarInfoSetter = createContext<((info: TopbarInfo | null) => void) | null>(null);

/** Gọi trong trang con để hiển thị "Cập nhật …" + badge chuông. Tự dọn khi rời trang. */
export function useSetTopbarInfo(updatedAt: string | null, alertCount: number) {
  const setInfo = useContext(TopbarInfoSetter);
  useEffect(() => {
    setInfo?.({ updatedAt, alertCount });
    return () => setInfo?.(null);
  }, [alertCount, setInfo, updatedAt]);
}

/* ---------- Nav ---------- */

type NavKey = "home" | "dashboard" | "signal" | "students" | "fairness" | "threshold" | "calendar" | "notify";
type NavItem = { label: string; icon: NavKey; href: string; tab?: string; exact?: boolean };

/** Chỉ trang/tab đã có thật — không vẽ mục chết (Báo cáo/Cấu hình… chờ API). */
const NAV_BY_ROLE: Record<Role, NavItem[]> = {
  ban_quan_ly: [
    { label: "Tổng quan", icon: "home", href: "/overview" },
    { label: "Phân tích", icon: "dashboard", href: "/analysis" },
    { label: "Thông báo", icon: "notify", href: "/notify" },
  ],
  gvcn: [
    { label: "Case của tôi", icon: "home", href: "/advisor", exact: true },
    { label: "Lớp & sinh viên", icon: "students", href: "/advisor/classes" },
    { label: "Lịch theo dõi", icon: "calendar", href: "/advisor/follow-ups" },
  ],
};

export function AppShell({ role, title, subtitle, children }: { role: Role; title?: string; subtitle?: string; children: ReactNode }) {
  const { account, activeRole, ready, chooseRole, logout } = useSession();
  const router = useRouter();
  const [topInfo, setTopInfo] = useState<TopbarInfo | null>(null);

  useEffect(() => {
    if (!ready) return;
    if (!account) router.replace("/login");
    else if (!activeRole) router.replace("/login");
    else if (activeRole !== role) router.replace(roleHome(activeRole));
  }, [ready, account, activeRole, role, router]);

  if (!ready || !account || activeRole !== role) {
    return <div style={{ padding: "3rem", textAlign: "center", color: "#94a3b8" }}>Đang tải…</div>;
  }

  const multi = account.roles.length > 1;
  const onChooseRole = async (next: Role) => {
    // Only update the authenticated session here. The current route guard owns
    // the single redirect after activeRole changes; issuing another push here
    // races with that replace and can leave /analysis stuck on its loading UI.
    await chooseRole(next);
  };
  const onLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <TopbarInfoSetter.Provider value={setTopInfo}>
      <div style={{ display: "flex", minHeight: "100vh", background: "#f6f7f9", alignItems: "stretch" }}>
        <aside style={sidebar} data-app-sidebar>
          {/* Logo EduSignal — dùng asset có sẵn, crop bằng background để bỏ nền trắng thừa. */}
          <div style={logoBox} aria-label="EduSignal" role="img" />

          <Suspense fallback={null}>
            <SideNav items={NAV_BY_ROLE[role]} />
          </Suspense>

          <div style={{ marginTop: "auto", display: "grid", gap: 12, padding: "0 12px" }}>
            <div style={shieldCard}>
              <span style={shieldCardIcon} aria-hidden><ShieldHeartIcon /></span>
              <div style={{ minWidth: 0 }}>
                <p style={{ margin: 0, fontWeight: 700, fontSize: 13.5, color: "#dc2626" }}>Silent Shield</p>
                <p style={{ margin: "2px 0 0", fontSize: 11.5, color: "#64748b", lineHeight: 1.35 }}>Hỗ trợ quan tâm sinh viên</p>
              </div>
            </div>
          </div>
        </aside>

        <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
          <header style={topbar}>
            <div style={{ minWidth: 0 }}>
              {title && (
                <>
                  <p style={{ margin: 0, color: "#94a3b8", fontSize: 12 }}>{ROLE_LABEL[role]}</p>
                  <h1 style={{ margin: "0.1rem 0 0", fontSize: 19, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{title}</h1>
                </>
              )}
            </div>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 5, flexShrink: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                {topInfo && (
                  <button style={bellButton} title="Việc cần chú ý" aria-label={`${topInfo.alertCount} việc cần chú ý`}>
                    <BellIcon />
                    {topInfo.alertCount > 0 && <span style={bellDot} aria-hidden />}
                  </button>
                )}
                <UserMenu account={account} role={role} multi={multi} onChooseRole={onChooseRole} onLogout={onLogout} />
              </div>
              {topInfo?.updatedAt && (
                <span style={updatedText}>
                  <ClockIcon />
                  Cập nhật: {formatUpdated(topInfo.updatedAt)}
                </span>
              )}
            </div>
          </header>

          <main style={{ flex: 1, padding: "1.5rem 1.75rem 2.5rem", width: "100%", boxSizing: "border-box" }}>
            {subtitle && <p style={{ margin: "0 0 1rem", color: "#475569", fontSize: 13.5 }}>{subtitle}</p>}
            {children}
          </main>
        </div>
      </div>
      <AgentFab />
      <AgentDrawer />
    </TopbarInfoSetter.Provider>
  );
}

/** "10:30 • 20/05/2024" từ ISO calculated_at — không hardcode thời gian. */
function formatUpdated(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  const time = d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
  const date = d.toLocaleDateString("vi-VN");
  return `${time} • ${date}`;
}

/* ---------- Nav sidebar (tách riêng vì useSearchParams cần Suspense) ---------- */

function SideNav({ items }: { items: NavItem[] }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const currentTab = searchParams.get("tab") ?? (pathname === "/analysis" ? "dashboard" : "overview");

  return (
    <nav style={{ display: "grid", gap: 4, padding: "0 12px" }} aria-label="Điều hướng chính">
      {items.map((item) => {
        const base = item.href.split("?")[0];
        const routeActive = pathname === base || (!item.exact && pathname.startsWith(`${base}/`));
        const active = routeActive && (item.tab === undefined || item.tab === currentTab);
        return (
          <Link key={item.href} href={item.href} style={{ ...navLink, ...(active ? navLinkActive : {}) }}>
            <span aria-hidden style={{ display: "flex", color: active ? "#dc2626" : "#94a3b8" }}>{NAV_ICONS[item.icon]}</span>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

/* ---------- User menu (chỉ hiển thị ở topbar) ---------- */

function UserMenu({
  account,
  role,
  multi,
  onChooseRole,
  onLogout,
}: {
  account: SessionAccount;
  role: Role;
  multi: boolean;
  onChooseRole: (next: Role) => void;
  onLogout: () => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { name, subtitle } = splitAccountName(account.name);
  const roleLine = subtitle || ROLE_LABEL[role];

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button onClick={() => setOpen((o) => !o)} style={userTrigger} aria-haspopup="menu" aria-expanded={open}>
        <span style={avatar} aria-hidden>{initialsFromName(name)}</span>
        <span style={{ display: "grid", gap: 1, minWidth: 0, textAlign: "left" }}>
          <span style={{ fontSize: 13.5, fontWeight: 600, color: "#0f172a", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{name}</span>
          <span style={{ fontSize: 11.5, color: "#94a3b8", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{roleLine}</span>
        </span>
        <span aria-hidden style={{ display: "flex", color: "#94a3b8", transform: open ? "rotate(180deg)" : undefined, transition: "transform 0.15s" }}><ChevronDownIcon /></span>
      </button>

      {open && (
        <div style={{ ...dropdownPanel, top: "calc(100% + 8px)" }} role="menu">
          <div style={{ padding: "4px 8px 10px" }}>
            <p style={{ margin: 0, fontSize: 13.5, fontWeight: 600, color: "#0f172a" }}>{name}</p>
            <p style={{ margin: "2px 0 0", fontSize: 12, color: "#94a3b8" }}>{roleLine}</p>
          </div>
          {multi && (
            <div style={{ padding: "0 8px 8px" }}>
              <select
                value={role}
                onChange={(e) => { onChooseRole(e.target.value as Role); setOpen(false); }}
                style={roleSelect}
                title="Chuyển vai trò"
              >
                {account.roles.map((r) => (
                  <option key={r} value={r}>{ROLE_LABEL[r]}</option>
                ))}
              </select>
            </div>
          )}
          <div style={{ height: 1, background: "#f1f5f9", margin: "0 4px 6px" }} />
          <button
            onClick={() => { setOpen(false); onLogout(); }}
            style={logoutItem}
            onMouseEnter={(e) => Object.assign(e.currentTarget.style, logoutItemHover)}
            onMouseLeave={(e) => Object.assign(e.currentTarget.style, logoutItem)}
          >
            <LogoutIcon />
            Đăng xuất
          </button>
        </div>
      )}
    </div>
  );
}

/* ---------- Styles ---------- */

const sidebar: CSSProperties = {
  width: 232,
  flexShrink: 0,
  background: "#fff",
  borderRight: "1px solid #e2e8f0",
  padding: "20px 0 16px",
  display: "flex",
  flexDirection: "column",
  gap: 18,
  position: "sticky",
  top: 0,
  alignSelf: "flex-start",
  minHeight: "100vh",
};
const logoBox: CSSProperties = {
  height: 40,
  margin: "0 16px 4px",
  backgroundImage: "url(/assets/branding/edusignal-logo-mark.png)",
  backgroundRepeat: "no-repeat",
  backgroundPosition: "left center",
  backgroundSize: "200px",
};
const topbar: CSSProperties = {
  background: "#fff",
  borderBottom: "1px solid #e2e8f0",
  padding: "12px 24px",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
  minHeight: 64,
  boxSizing: "border-box",
};
const navLink: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 12,
  padding: "11px 14px",
  borderRadius: 12,
  fontSize: 14,
  fontWeight: 500,
  color: "#475569",
  textDecoration: "none",
};
const navLinkActive: CSSProperties = { background: "#fdecec", color: "#dc2626", fontWeight: 600 };
const shieldCard: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  padding: "12px 14px",
  borderRadius: 14,
  background: "#fdecec",
  border: "1px solid #fbd7d7",
};
const shieldCardIcon: CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  width: 34,
  height: 34,
  borderRadius: 10,
  background: "#dc2626",
  color: "#fff",
  flexShrink: 0,
};
const userTrigger: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  width: "100%",
  padding: "6px 8px",
  borderRadius: 12,
  border: "none",
  background: "transparent",
  cursor: "pointer",
};
const avatar: CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  width: 36,
  height: 36,
  borderRadius: 999,
  background: "linear-gradient(135deg, #dc2626, #b91c1c)",
  color: "#fff",
  fontSize: 14,
  fontWeight: 700,
  flexShrink: 0,
};
const bellButton: CSSProperties = {
  position: "relative",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  width: 38,
  height: 38,
  borderRadius: 10,
  border: "none",
  background: "transparent",
  color: "#475569",
  cursor: "pointer",
};
const bellDot: CSSProperties = {
  position: "absolute",
  top: 8,
  right: 9,
  width: 9,
  height: 9,
  borderRadius: 999,
  background: "#dc2626",
  border: "1.5px solid #fff",
  boxSizing: "border-box",
};
const updatedText: CSSProperties = { display: "flex", alignItems: "center", gap: 6, fontSize: 12.5, color: "#64748b" };
const dropdownPanel: CSSProperties = {
  position: "absolute",
  right: 0,
  width: 240,
  background: "#fff",
  border: "1px solid #e2e8f0",
  borderRadius: 12,
  boxShadow: "0 12px 28px rgba(15, 23, 42, 0.12)",
  padding: 8,
  zIndex: 30,
};
const roleSelect: CSSProperties = {
  width: "100%",
  padding: "7px 10px",
  borderRadius: 8,
  border: "1px solid #fecaca",
  background: "#fef2f2",
  fontWeight: 600,
  color: "#b91c1c",
  fontSize: 12.5,
};
const logoutItem: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  width: "100%",
  padding: "9px 10px",
  borderRadius: 8,
  border: "none",
  background: "transparent",
  cursor: "pointer",
  color: "#475569",
  fontSize: 13.5,
  transition: "color 0.15s, background 0.15s",
};
const logoutItemHover: CSSProperties = { ...logoutItem, color: "#b91c1c", background: "#fef2f2" };

/* ---------- Icons ---------- */

const svgProps = {
  width: 20,
  height: 20,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.9,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

const NAV_ICONS: Record<NavKey, ReactNode> = {
  home: (<svg {...svgProps}><path d="M3 10.5 12 3l9 7.5" /><path d="M5 9.5V21h14V9.5" /><path d="M9.5 21v-6h5v6" /></svg>),
  dashboard: (<svg {...svgProps}><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></svg>),
  signal: (<svg {...svgProps}><path d="M3 12h4l2.5 7 5-14L17 12h4" /></svg>),
  students: (<svg {...svgProps}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>),
  fairness: (<svg {...svgProps}><path d="M12 3v18" /><path d="M7 21h10" /><path d="M5 7h14" /><path d="M5 7 2 14h6L5 7z" /><path d="M19 7l-3 7h6l-3-7z" /></svg>),
  threshold: (<svg {...svgProps}><path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3" /><path d="M2 14h4M10 8h4M18 16h4" /></svg>),
  calendar: (<svg {...svgProps}><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /><path d="m8 15 2 2 5-5" /></svg>),
  notify: (<svg {...svgProps}><rect x="2" y="4" width="20" height="16" rx="2" /><path d="M22 7l-10 6L2 7" /></svg>),
};

function ShieldHeartIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <path d="M12 13.5s-2.5-1.6-2.5-3.2A1.3 1.3 0 0 1 12 9.5a1.3 1.3 0 0 1 2.5.8c0 1.6-2.5 3.2-2.5 3.2z" fill="currentColor" stroke="none" />
    </svg>
  );
}

function BellIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
      <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </svg>
  );
}

function ChevronDownIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 9l6 6 6-6" />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="M16 17l5-5-5-5" />
      <path d="M21 12H9" />
    </svg>
  );
}
