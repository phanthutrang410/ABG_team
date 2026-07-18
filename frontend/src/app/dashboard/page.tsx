"use client";

import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { ScopeBanner } from "@/components/ScopeBanner";
import { BandBadge, CaseStateBadge } from "@/components/badges";
import { FairnessPanel } from "@/components/FairnessPanel";
import { LimitationsList } from "@/components/LimitationsList";
import { ThresholdPanel } from "@/components/ThresholdPanel";
import { apiBase, fetchReviewCases } from "@/lib/api";
import {
  BAND_LABEL,
  CASE_STATE_LABEL,
  type CaseListResponse,
  type ReviewCase,
  type ReviewPriorityBand,
} from "@/lib/types";

/**
 * Dashboard Ban quản lý (ui-design-spec §4.1) — dữ liệu live GET /review-cases.
 * 5 tab: Tổng quan (thẻ đếm + biểu đồ) · Tín hiệu · Sinh viên (sort/tìm kiếm) ·
 * Fairness (G04, fail-closed) · Ngưỡng (G04, impact tổng hợp).
 * Fail-closed: nguồn lỗi → hiện lỗi, không bịa dữ liệu. Scoping khoa/lớp chờ
 * ReviewCase public có cohort/department (gap đã báo Hoàng).
 */

type Tab = "overview" | "signals" | "students" | "fairness" | "threshold";
const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "Tổng quan" },
  { id: "signals", label: "Tín hiệu" },
  { id: "students", label: "Sinh viên" },
  { id: "fairness", label: "Fairness" },
  { id: "threshold", label: "Ngưỡng" },
];

export default function DashboardPage() {
  return (
    <AppShell
      role="ban_quan_ly"
      title="Bảng điều khiển giám sát học tập"
      subtitle="Gợi ý ưu tiên sự quan tâm — không phải kết luận hay kỷ luật. Con người phê duyệt trước khi bàn giao."
    >
      <DashboardBody />
    </AppShell>
  );
}

function DashboardBody() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("overview");
  const [loading, setLoading] = useState(true);
  const [response, setResponse] = useState<CaseListResponse | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    const controller = new AbortController();
    fetchReviewCases(controller.signal).then((r) => {
      setResponse(r);
      setLoading(false);
    });
    return controller;
  }, []);

  useEffect(() => {
    const controller = load();
    return () => controller.abort();
  }, [load]);

  const openCase = useCallback((id: string) => router.push(`/cases/${id}`), [router]);

  return (
    <>
      <ScopeBanner />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem", fontSize: 12, color: "#94a3b8" }}>
        <span>Nguồn: <code>{apiBase()}/review-cases</code></span>
        <button onClick={() => load()} style={retryBtn}>↻ Tải lại</button>
      </div>

      <nav style={{ display: "flex", gap: 4, borderBottom: "1px solid #e2e8f0", marginBottom: "1.25rem", flexWrap: "wrap" }}>
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              padding: "10px 16px",
              border: "none",
              borderBottom: tab === t.id ? "2px solid #1d4ed8" : "2px solid transparent",
              background: "none",
              fontSize: 14,
              fontWeight: tab === t.id ? 600 : 400,
              color: tab === t.id ? "#1d4ed8" : "#64748b",
              cursor: "pointer",
            }}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "overview" && (
        <OverviewTab loading={loading} response={response} onGoSignals={() => setTab("signals")} />
      )}
      {tab === "signals" && (
        loading ? <ListSkeleton /> : response ? <SignalsList response={response} onOpenCase={openCase} /> : null
      )}
      {tab === "students" && (
        loading ? <ListSkeleton /> : response ? <StudentsTab response={response} onOpenCase={openCase} /> : null
      )}
      {tab === "fairness" && <FairnessPanel />}
      {tab === "threshold" && <ThresholdPanel />}

      <p style={{ marginTop: "1.25rem", fontSize: 13, color: "#94a3b8" }}>
        Dữ liệu và hành động đi thẳng API — không hiển thị điểm số nội bộ của model.
        Scoping theo khoa/lớp và danh sách toàn bộ SV chờ API bổ sung (xem design spec §9).
      </p>
    </>
  );
}

/* ================= Tổng quan ================= */

function OverviewTab({ loading, response, onGoSignals }: { loading: boolean; response: CaseListResponse | null; onGoSignals: () => void }) {
  const items = useMemo(() => (response && response.state !== "error" ? response.items : []), [response]);

  const counts = useMemo(() => {
    const byState = (s: string) => items.filter((c) => c.case_state === s).length;
    return {
      total: items.length,
      newSignals: byState("new_signal"),
      pending: byState("pending_review"),
      active: byState("assigned") + byState("follow_up_in_progress") + byState("monitoring"),
    };
  }, [items]);

  if (loading) return <ListSkeleton />;
  if (!response) return null;

  if (response.state === "error") {
    return <Notice tone="error">Không tải được dữ liệu tổng quan — máy chủ tạm thời không phản hồi. Bấm “Tải lại”.</Notice>;
  }

  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      {response.state === "stale" && (
        <Notice tone="warning">Dữ liệu có thể đã cũ — snapshot chưa được cập nhật gần đây.</Notice>
      )}
      {response.state === "empty" ? (
        <Notice tone="info">Chưa có tín hiệu trong kỳ dữ liệu này. Không có tín hiệu không đồng nghĩa mọi sinh viên đều ổn định — xem thêm độ phủ nguồn.</Notice>
      ) : (
        <>
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
            <Summary label="Tổng tín hiệu" value={counts.total} />
            <Summary label="Tín hiệu mới" value={counts.newSignals} />
            <Summary label="Chờ duyệt" value={counts.pending} />
            <Summary label="Đang theo dõi / hỗ trợ" value={counts.active} />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1rem" }}>
            <ChartCard title="Phân bố mức ưu tiên rà soát" subtitle="Từ dữ liệu live">
              <HBars rows={bandRows(items)} />
            </ChartCard>
            <ChartCard title="Case theo trạng thái" subtitle="Từ dữ liệu live">
              <HBars rows={stateRows(items)} />
            </ChartCard>
            <ChartCard title="Yếu tố đóng góp phổ biến" subtitle="Từ dữ liệu live">
              <HBars rows={factorRows(items)} />
            </ChartCard>
            <ChartCard title="Xu hướng tín hiệu theo kỳ" subtitle="Chờ API lịch sử theo kỳ (design spec §9)">
              <p style={{ margin: 0, fontSize: 13, color: "#94a3b8", fontStyle: "italic" }}>
                Chưa có API lịch sử tín hiệu theo học kỳ — không vẽ số liệu giả.
              </p>
            </ChartCard>
          </div>

          <button onClick={onGoSignals} style={{ justifySelf: "start", padding: "9px 16px", borderRadius: 8, border: "1px solid #93c5fd", background: "#eff6ff", fontSize: 14, fontWeight: 600, color: "#1d4ed8", cursor: "pointer" }}>
            → Mở danh sách tín hiệu cần rà soát
          </button>
        </>
      )}
    </div>
  );
}

function bandRows(items: ReviewCase[]) {
  const bands: (ReviewPriorityBand)[] = ["can_ra_soat", "uu_tien_som"];
  return bands.map((b) => ({ label: BAND_LABEL[b], value: items.filter((c) => c.review_priority_band === b).length }));
}

function stateRows(items: ReviewCase[]) {
  const present = Array.from(new Set(items.map((c) => c.case_state)));
  return present
    .map((s) => ({ label: CASE_STATE_LABEL[s], value: items.filter((c) => c.case_state === s).length }))
    .sort((a, b) => b.value - a.value);
}

function factorRows(items: ReviewCase[]) {
  const counts = new Map<string, number>();
  for (const c of items) for (const f of c.contributing_factors) counts.set(f.code, (counts.get(f.code) ?? 0) + 1);
  return Array.from(counts.entries())
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 5);
}

/* ================= Tín hiệu ================= */

function SignalsList({ response, onOpenCase }: { response: CaseListResponse; onOpenCase: (caseId: string) => void }) {
  if (response.state === "error") {
    return <Notice tone="error">Không tải được danh sách tín hiệu — máy chủ tạm thời không phản hồi.</Notice>;
  }
  if (response.state === "empty") {
    return <Notice tone="info">Chưa có tín hiệu mới trong kỳ dữ liệu này.</Notice>;
  }
  return (
    <>
      {response.state === "stale" && (
        <Notice tone="warning">Dữ liệu có thể đã cũ — danh sách vẫn hiển thị nhưng không được coi là mới nhất.</Notice>
      )}
      <CaseRowsTable items={response.items} onOpenCase={onOpenCase} />
    </>
  );
}

/* ================= Sinh viên (sort/tìm kiếm) ================= */

type SortKey = "band" | "ref" | "state";
const SORTS: { id: SortKey; label: string }[] = [
  { id: "band", label: "Mức độ cảnh báo" },
  { id: "ref", label: "Mã SV (A → Z)" },
  { id: "state", label: "Trạng thái case" },
];

function StudentsTab({ response, onOpenCase }: { response: CaseListResponse; onOpenCase: (caseId: string) => void }) {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<SortKey>("band");

  const rows = useMemo(() => {
    if (response.state === "error") return [];
    const needle = q.trim().toLowerCase();
    let list = response.items;
    if (needle) list = list.filter((c) => c.student_ref.toLowerCase().includes(needle) || c.case_id.toLowerCase().includes(needle));
    const bandRank = (c: ReviewCase) => (c.review_priority_band === "uu_tien_som" ? 0 : c.review_priority_band === "can_ra_soat" ? 1 : 2);
    switch (sort) {
      case "ref":
        return [...list].sort((a, b) => a.student_ref.localeCompare(b.student_ref));
      case "state":
        return [...list].sort((a, b) => a.case_state.localeCompare(b.case_state));
      default:
        return [...list].sort((a, b) => bandRank(a) - bandRank(b));
    }
  }, [response, q, sort]);

  if (response.state === "error") {
    return <Notice tone="error">Không tải được danh sách — máy chủ tạm thời không phản hồi.</Notice>;
  }

  return (
    <>
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: "0.75rem", fontSize: 13, flexWrap: "wrap" }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="🔍 Tìm theo mã SV…"
          style={{ padding: "7px 12px", borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 13, minWidth: 220, fontFamily: "inherit" }}
          aria-label="Tìm kiếm sinh viên"
        />
        <label style={{ color: "#475569" }}>
          Sắp xếp:{" "}
          <select value={sort} onChange={(e) => setSort(e.target.value as SortKey)} style={{ padding: "4px 8px", borderRadius: 6, border: "1px solid #e2e8f0" }}>
            {SORTS.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
          </select>
        </label>
        <span style={{ marginLeft: "auto", color: "#94a3b8" }}>{rows.length} sinh viên có tín hiệu</span>
      </div>

      {rows.length === 0 ? (
        <Notice tone="info">Không có kết quả khớp tìm kiếm. Thử xóa từ khóa hoặc đổi bộ lọc.</Notice>
      ) : (
        <CaseRowsTable items={rows} onOpenCase={onOpenCase} />
      )}

      <p style={{ marginTop: "0.75rem", fontSize: 12, color: "#94a3b8" }}>
        Danh sách hiện gồm SV có tín hiệu (từ API case). Danh sách toàn bộ SV + tên/lớp + GPA cần API
        bổ sung — tìm “theo tên/lớp” sẽ hoạt động khi API đó sẵn sàng (mã SV là pseudonym trong demo).
      </p>
    </>
  );
}

/* ================= shared ================= */

function CaseRowsTable({ items, onOpenCase }: { items: ReviewCase[]; onOpenCase: (caseId: string) => void }) {
  return (
    <section style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, overflow: "hidden" }}>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 700 }}>
          <thead>
            <tr style={{ background: "#f8fafc", textAlign: "left" }}>
              <th style={th}>Mã SV</th>
              <th style={th}>Trạng thái case</th>
              <th style={th}>Mức ưu tiên rà soát</th>
              <th style={th}>Yếu tố đóng góp</th>
              <th style={th}>Giới hạn dữ liệu</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.case_id} onClick={() => onOpenCase(c.case_id)} style={{ borderTop: "1px solid #e2e8f0", cursor: "pointer" }} title="Mở chi tiết">
                <td style={{ ...td, color: "#1d4ed8", fontWeight: 500 }}>{c.student_ref}</td>
                <td style={td}><CaseStateBadge state={c.case_state} /></td>
                <td style={td}><BandBadge band={c.review_priority_band} /></td>
                <td style={td}>{c.contributing_factors.map((f) => f.code).join(", ") || "—"}</td>
                <td style={{ ...td, maxWidth: 300 }}><LimitationsList limitations={c.limitations} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ChartCard({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <section style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: "1.1rem 1.35rem" }}>
      <h3 style={{ margin: "0 0 2px", fontSize: 14, fontWeight: 600, color: "#1e293b" }}>{title}</h3>
      <p style={{ margin: "0 0 0.9rem", fontSize: 12, color: "#94a3b8" }}>{subtitle}</p>
      {children}
    </section>
  );
}

/** Bar ngang 1 series — 1 hue xanh, nhãn giá trị trực tiếp, chữ luôn đi kèm (dataviz rules). */
function HBars({ rows }: { rows: { label: string; value: number }[] }) {
  if (rows.length === 0) return <p style={{ margin: 0, fontSize: 13, color: "#94a3b8", fontStyle: "italic" }}>Chưa có dữ liệu.</p>;
  const max = Math.max(1, ...rows.map((r) => r.value));
  return (
    <div style={{ display: "grid", gap: 10 }}>
      {rows.map((r) => (
        <div key={r.label} title={`${r.label}: ${r.value}`} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13 }}>
          <span style={{ width: 150, color: "#64748b", flexShrink: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.label}</span>
          <div style={{ flex: 1, height: 14, background: "#eef2f7", borderRadius: 4, overflow: "hidden" }}>
            <div style={{ width: `${(r.value / max) * 100}%`, height: "100%", background: "#2a78d6", borderRadius: "0 4px 4px 0" }} />
          </div>
          <span style={{ width: 24, textAlign: "right", color: "#1e293b", fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>{r.value}</span>
        </div>
      ))}
    </div>
  );
}

function Summary({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ flex: "1 1 150px", background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: "1rem 1.25rem" }}>
      <div style={{ fontSize: 13, color: "#64748b" }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color: "#1e293b", fontVariantNumeric: "tabular-nums" }}>{value}</div>
    </div>
  );
}

function Notice({ tone, children }: { tone: "info" | "warning" | "error"; children: React.ReactNode }) {
  const styles: Record<typeof tone, CSSProperties> = {
    info: { background: "#f8fafc", border: "1px solid #e2e8f0", color: "#475569" },
    warning: { background: "#fffbeb", border: "1px solid #fde68a", color: "#92400e" },
    error: { background: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b" },
  };
  return <div style={{ ...styles[tone], padding: "0.9rem 1.1rem", borderRadius: 8, fontSize: 14 }}>{children}</div>;
}

function ListSkeleton() {
  return (
    <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: "1.5rem", display: "grid", gap: 10 }} aria-busy="true" aria-label="Đang tải">
      {[0, 1, 2].map((i) => (
        <div key={i} style={{ height: 16, borderRadius: 4, background: "#f1f5f9", width: `${70 - i * 10}%` }} />
      ))}
    </div>
  );
}

const th: CSSProperties = { padding: "12px 16px", fontSize: 13, color: "#64748b" };
const td: CSSProperties = { padding: "13px 16px", fontSize: 14, verticalAlign: "top" };
const retryBtn: CSSProperties = { padding: "3px 10px", borderRadius: 6, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", color: "#475569", fontSize: 12 };
