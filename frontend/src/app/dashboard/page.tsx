"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { ScopeBanner } from "@/components/ScopeBanner";
import { BandBadge, CaseStateBadge } from "@/components/badges";
import { FairnessPanel } from "@/components/FairnessPanel";
import { LimitationsList } from "@/components/LimitationsList";
import { ThresholdPanel } from "@/components/ThresholdPanel";
import { fetchReviewCases } from "@/lib/api";
import {
  BAND_LABEL,
  CASE_STATE_LABEL,
  type CaseListResponse,
  type ReviewCase,
  type ReviewPriorityBand,
} from "@/lib/types";

/**
 * Dashboard Ban quản lý (ui-design-spec §4.1) — dữ liệu live GET /review-cases.
 * Tab điều hướng bởi sidebar AppShell qua /dashboard?tab=… Restyle Tailwind 18/7.
 * Fail-closed: nguồn lỗi → hiện lỗi, không bịa dữ liệu (mọi số trên trang đều
 * tính từ response — không hardcode đếm/trend/thời gian).
 */

type Tab = "overview" | "signals" | "students" | "fairness" | "threshold";
const TAB_IDS: Tab[] = ["overview", "signals", "students", "fairness", "threshold"];

export default function DashboardPage() {
  return (
    <AppShell
      role="ban_quan_ly"
      title="Bảng điều khiển giám sát học tập"
      subtitle="Hệ thống hỗ trợ rà soát sớm — không phải công cụ kỷ luật. Con người phê duyệt trước khi bàn giao."
    >
      <Suspense fallback={<ListSkeleton />}>
        <DashboardBody />
      </Suspense>
    </AppShell>
  );
}

function DashboardBody() {
  const router = useRouter();
  const searchParams = useSearchParams();
  // Tab điều khiển bởi sidebar qua /dashboard?tab=… (AppShell); giá trị lạ → overview.
  const rawTab = searchParams.get("tab");
  const tab: Tab = TAB_IDS.includes(rawTab as Tab) ? (rawTab as Tab) : "overview";
  const setTab = useCallback(
    (t: Tab) => router.replace(`/dashboard?tab=${t}`, { scroll: false }),
    [router],
  );

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
    <div className="space-y-6">
      <ScopeBanner />

      <div className="flex justify-end">
        <button
          onClick={() => load()}
          className="text-xs text-slate-500 border border-slate-200 bg-white rounded-lg px-3 py-1.5 hover:border-slate-300 transition-colors"
        >
          ↻ Tải lại dữ liệu
        </button>
      </div>

      {tab === "overview" && (
        <OverviewTab loading={loading} response={response} setTab={setTab} />
      )}
      {tab === "signals" && (
        loading ? <ListSkeleton /> : response ? <SignalsList response={response} onOpenCase={openCase} /> : null
      )}
      {tab === "students" && (
        loading ? <ListSkeleton /> : response ? <StudentsTab response={response} onOpenCase={openCase} /> : null
      )}
      {tab === "fairness" && <FairnessPanel />}
      {tab === "threshold" && <ThresholdPanel />}

      <p className="text-xs text-slate-400">
        Dữ liệu và hành động đi thẳng API — không hiển thị điểm số nội bộ của model.
        Scoping theo khoa/lớp và danh sách toàn bộ SV chờ API bổ sung (design spec §9).
      </p>
    </div>
  );
}

/* ================= Tổng quan ================= */

function OverviewTab({ loading, response, setTab }: { loading: boolean; response: CaseListResponse | null; setTab: (t: Tab) => void }) {
  const items = useMemo(() => (response && response.state !== "error" ? response.items : []), [response]);

  const counts = useMemo(() => {
    const byState = (s: string) => items.filter((c) => c.case_state === s).length;
    return {
      total: items.length,
      newSignals: byState("new_signal"),
      pending: byState("pending_review"),
      active: byState("assigned") + byState("follow_up_in_progress") + byState("monitoring"),
      earlyPriority: items.filter((c) => c.review_priority_band === "uu_tien_som").length,
    };
  }, [items]);

  if (loading) return <ListSkeleton />;
  if (!response) return null;

  if (response.state === "error") {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 p-6 rounded-2xl">
        <h3 className="font-semibold">Không tải được dữ liệu tổng quan</h3>
        <p className="text-sm text-red-600/80 mt-1">Máy chủ tạm thời không phản hồi. Vui lòng bấm “Tải lại dữ liệu”.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Cam kết phạm vi — care, không kỷ luật (copy H12a/FR-11) */}
      <div className="bg-blue-50/70 border border-blue-100 rounded-2xl p-6 flex items-start gap-5">
        <div className="p-3 bg-blue-100 rounded-xl text-blue-600 shrink-0">
          <Icon path={iconPaths.shield} className="w-6 h-6" />
        </div>
        <div className="flex-1">
          <h3 className="text-base font-semibold text-blue-900">Silent Shield chỉ hỗ trợ rà soát</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-6 gap-y-2 mt-3 text-sm text-blue-800/80">
            <div className="flex items-center gap-2"><Icon path={iconPaths.check} className="w-4 h-4 text-blue-500 shrink-0" /> Không chẩn đoán</div>
            <div className="flex items-center gap-2"><Icon path={iconPaths.check} className="w-4 h-4 text-blue-500 shrink-0" /> Không gán nhãn</div>
            <div className="flex items-center gap-2"><Icon path={iconPaths.check} className="w-4 h-4 text-blue-500 shrink-0" /> Không kỷ luật</div>
            <div className="flex items-center gap-2"><Icon path={iconPaths.check} className="w-4 h-4 text-blue-500 shrink-0" /> Con người quyết định</div>
          </div>
        </div>
      </div>

      {response.state === "empty" ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center shadow-sm">
          <div className="mx-auto w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
            <Icon path={iconPaths.heart} className="w-8 h-8 text-slate-300" />
          </div>
          <h3 className="text-lg font-semibold text-slate-700">Chưa có tín hiệu trong kỳ này</h3>
          <p className="text-sm text-slate-400 mt-1">Không có tín hiệu không đồng nghĩa mọi sinh viên đều ổn định — xem thêm độ phủ nguồn.</p>
        </div>
      ) : (
        <>
          {response.state === "stale" && (
            <div className="bg-amber-50 border border-amber-200 text-amber-700 p-4 rounded-2xl text-sm">
              Dữ liệu có thể đã cũ — snapshot chưa được cập nhật gần đây.
            </div>
          )}

          {/* KPI — tất cả tính từ response, không hardcode */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <KpiCard label="Tổng tín hiệu" value={counts.total} icon={iconPaths.activity} color="blue" />
            <KpiCard label="Tín hiệu mới" value={counts.newSignals} icon={iconPaths.sparkles} color="amber" />
            <KpiCard label="Chờ duyệt" value={counts.pending} icon={iconPaths.clock} color="indigo" />
            <KpiCard label="Đang theo dõi / hỗ trợ" value={counts.active} icon={iconPaths.users} color="emerald" />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <ChartCard title="Mức ưu tiên rà soát" subtitle="Phân bổ từ dữ liệu live" icon={iconPaths.scale}>
              <StackedBar rows={bandRows(items)} colors={["#2a78d6", "#f59e0b"]} />
            </ChartCard>
            <ChartCard title="Trạng thái xử lý" subtitle="Tiến độ hiện tại" icon={iconPaths.activity}>
              <StackedBar rows={stateRows(items)} colors={["#2a78d6", "#10b981", "#8b5cf6", "#ec4899"]} />
            </ChartCard>
            <ChartCard title="Yếu tố đóng góp phổ biến" subtitle="Từ model, tối đa 5" icon={iconPaths.sparkles}>
              <StackedBar rows={factorRows(items)} colors={["#0ea5e9"]} />
            </ChartCard>
          </div>

          {/* Xu hướng — chưa có API, nói thẳng là thiếu */}
          <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm">
            <h3 className="text-base font-semibold text-slate-800">Xu hướng tín hiệu theo kỳ</h3>
            <div className="mt-6 flex flex-col items-center justify-center text-center py-10 border-2 border-dashed border-slate-100 rounded-xl">
              <div className="p-4 bg-slate-50 rounded-full mb-4">
                <Icon path={iconPaths.chart} className="w-10 h-10 text-slate-300" />
              </div>
              <p className="text-sm font-medium text-slate-500">Chưa có API lịch sử tín hiệu theo học kỳ — không vẽ số liệu giả.</p>
              <p className="text-xs text-slate-400 mt-1">Design spec §9 — chờ backend bổ sung.</p>
            </div>
          </div>

          {/* Việc nên làm — số thật từ response; card ẩn khi không có việc */}
          {(counts.earlyPriority > 0 || counts.pending > 0 || counts.active > 0) && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-slate-800">Việc nên thực hiện hôm nay</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {counts.earlyPriority > 0 && (
                  <ActionCard
                    title="Rà soát mức Ưu tiên sớm"
                    desc={`Có ${counts.earlyPriority} tín hiệu ở mức Ưu tiên sớm. Xem yếu tố đóng góp và độ phủ trước khi quyết định.`}
                    cta="Đi tới Tín hiệu"
                    onClick={() => setTab("signals")}
                    icon={iconPaths.sparkles}
                    color="bg-amber-50 text-amber-600"
                  />
                )}
                {counts.pending > 0 && (
                  <ActionCard
                    title="Duyệt case đang chờ"
                    desc={`${counts.pending} case đang ở trạng thái Chờ duyệt — phê duyệt, loại hoặc hoãn kèm lý do.`}
                    cta="Đi tới Tín hiệu"
                    onClick={() => setTab("signals")}
                    icon={iconPaths.clock}
                    color="bg-indigo-50 text-indigo-600"
                  />
                )}
                {counts.active > 0 && (
                  <ActionCard
                    title="Theo dõi case đã bàn giao"
                    desc={`${counts.active} case đang được hỗ trợ hoặc theo dõi — kiểm tra tiến độ.`}
                    cta="Đi tới Sinh viên"
                    onClick={() => setTab("students")}
                    icon={iconPaths.users}
                    color="bg-emerald-50 text-emerald-600"
                  />
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function bandRows(items: ReviewCase[]) {
  const bands: ReviewPriorityBand[] = ["can_ra_soat", "uu_tien_som"];
  return bands.map((b) => ({ label: BAND_LABEL[b], value: items.filter((c) => c.review_priority_band === b).length }));
}

function stateRows(items: ReviewCase[]) {
  const present = Array.from(new Set(items.map((c) => c.case_state)));
  return present
    .map((s) => ({ label: CASE_STATE_LABEL[s], value: items.filter((c) => c.case_state === s).length }))
    .sort((a, b) => b.value - a.value);
}

/** Nhãn VI cho factor codes M02 (fallback: nguyên code) — đồng bộ trang chi tiết case. */
const FACTOR_LABEL: Record<string, string> = {
  grade_trend_declining: "Kết quả học tập giảm",
  grade_volatility_elevated: "Điểm biến động giữa các kỳ",
  attendance_rate_below_target: "Tỷ lệ điểm danh thấp",
  attendance_trend_declining: "Chuyên cần giảm dần",
};

function factorRows(items: ReviewCase[]) {
  const counts = new Map<string, number>();
  for (const c of items) for (const f of c.contributing_factors) counts.set(f.code, (counts.get(f.code) ?? 0) + 1);
  return Array.from(counts.entries())
    .map(([code, value]) => ({ label: FACTOR_LABEL[code] ?? code, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 5);
}

/* ================= Tín hiệu & Sinh viên ================= */

function SignalsList({ response, onOpenCase }: { response: CaseListResponse; onOpenCase: (caseId: string) => void }) {
  if (response.state === "error") {
    return <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl">Không tải được danh sách tín hiệu — máy chủ tạm thời không phản hồi.</div>;
  }
  if (response.state === "empty") {
    return <div className="bg-blue-50 border border-blue-100 text-blue-700 p-4 rounded-xl">Chưa có tín hiệu mới trong kỳ dữ liệu này.</div>;
  }
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-slate-800">Danh sách tín hiệu</h2>
      {response.state === "stale" && (
        <div className="bg-amber-50 border border-amber-200 text-amber-700 p-4 rounded-xl text-sm">
          Dữ liệu có thể đã cũ — danh sách vẫn hiển thị nhưng không được coi là mới nhất.
        </div>
      )}
      <CaseRowsTable items={response.items} onOpenCase={onOpenCase} />
    </div>
  );
}

type SortKey = "band" | "ref" | "state";

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
      case "ref": return [...list].sort((a, b) => a.student_ref.localeCompare(b.student_ref));
      case "state": return [...list].sort((a, b) => a.case_state.localeCompare(b.case_state));
      default: return [...list].sort((a, b) => bandRank(a) - bandRank(b));
    }
  }, [response, q, sort]);

  if (response.state === "error") {
    return <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl">Không tải được danh sách — máy chủ tạm thời không phản hồi.</div>;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-slate-800">Sinh viên có tín hiệu</h2>
      <div className="flex flex-wrap gap-3 items-center bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="🔍 Tìm theo mã SV…"
          aria-label="Tìm kiếm sinh viên"
          className="flex-1 min-w-[220px] px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400 transition-all"
        />
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as SortKey)}
          className="px-4 py-2.5 bg-white border border-slate-200 rounded-lg text-sm text-slate-600 outline-none cursor-pointer focus:ring-2 focus:ring-blue-100"
        >
          <option value="band">Mức độ cần quan tâm</option>
          <option value="ref">Mã SV (A → Z)</option>
          <option value="state">Trạng thái case</option>
        </select>
        <span className="text-sm text-slate-400 ml-auto">{rows.length} sinh viên</span>
      </div>

      {rows.length === 0 ? (
        <div className="bg-blue-50 border border-blue-100 text-blue-700 p-4 rounded-xl">Không có kết quả khớp tìm kiếm. Thử xóa từ khóa hoặc đổi bộ lọc.</div>
      ) : (
        <CaseRowsTable items={rows} onOpenCase={onOpenCase} />
      )}

      <p className="text-xs text-slate-400">
        Danh sách hiện gồm SV có tín hiệu (từ API case). Danh sách toàn bộ SV + tên/lớp + GPA cần API
        bổ sung — mã SV là pseudonym trong demo.
      </p>
    </div>
  );
}

/* ================= Reusable UI ================= */

function CaseRowsTable({ items, onOpenCase }: { items: ReviewCase[]; onOpenCase: (caseId: string) => void }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse min-w-[800px]">
          <thead>
            <tr className="bg-slate-50/50 border-b border-slate-200">
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Mã SV</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Trạng thái case</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Mức ưu tiên rà soát</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Yếu tố đóng góp</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Giới hạn dữ liệu</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr
                key={c.case_id}
                onClick={() => onOpenCase(c.case_id)}
                title="Mở chi tiết"
                className="border-b border-slate-100 last:border-0 cursor-pointer hover:bg-slate-50/70 transition-colors"
              >
                <td className="p-4 text-sm font-medium text-blue-600">{c.student_ref}</td>
                <td className="p-4"><CaseStateBadge state={c.case_state} /></td>
                <td className="p-4"><BandBadge band={c.review_priority_band} /></td>
                <td className="p-4 text-sm text-slate-500">
                  {c.contributing_factors.map((f) => FACTOR_LABEL[f.code] ?? f.code).join(", ") || "—"}
                </td>
                <td className="p-4 max-w-[300px]"><LimitationsList limitations={c.limitations} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function KpiCard({ label, value, icon, color }: { label: string; value: number; icon: string; color: "blue" | "amber" | "indigo" | "emerald" }) {
  const colors = {
    blue: "bg-blue-50 text-blue-600",
    amber: "bg-amber-50 text-amber-600",
    indigo: "bg-indigo-50 text-indigo-600",
    emerald: "bg-emerald-50 text-emerald-600",
  };
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5">
      <div className={`p-2.5 rounded-xl w-fit mb-4 ${colors[color]}`}>
        <Icon path={icon} className="w-5 h-5" />
      </div>
      <div className="text-3xl font-bold text-slate-800 tracking-tight tabular-nums">{value}</div>
      <div className="text-sm text-slate-500 mt-1">{label}</div>
    </div>
  );
}

function ChartCard({ title, subtitle, children, icon }: { title: string; subtitle: string; children: React.ReactNode; icon: string }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
      <div className="flex items-center gap-3 mb-5">
        <div className="p-2 bg-slate-50 rounded-lg text-slate-400">
          <Icon path={icon} className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
          <p className="text-xs text-slate-400">{subtitle}</p>
        </div>
      </div>
      {children}
    </div>
  );
}

/** Thanh tỷ lệ + legend chữ và số — màu không bao giờ là tín hiệu duy nhất. */
function StackedBar({ rows, colors }: { rows: { label: string; value: number }[]; colors: string[] }) {
  const total = rows.reduce((acc, r) => acc + r.value, 0);
  if (total === 0) return <div className="text-sm text-slate-400 italic py-4 text-center">Chưa có dữ liệu.</div>;

  return (
    <div className="space-y-4">
      <div className="flex w-full h-3 rounded-full overflow-hidden bg-slate-50">
        {rows.map((r, i) => (
          <div
            key={r.label}
            className="h-full"
            style={{ width: `${(r.value / total) * 100}%`, backgroundColor: colors[i % colors.length] }}
            title={`${r.label}: ${r.value}`}
          />
        ))}
      </div>
      <div className="space-y-2.5">
        {rows.map((r, i) => (
          <div key={r.label} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 min-w-0">
              <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: colors[i % colors.length] }} />
              <span className="text-slate-600 font-medium truncate">{r.label}</span>
            </div>
            <span className="text-slate-800 font-semibold tabular-nums">{r.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ActionCard({ title, desc, cta, onClick, icon, color }: { title: string; desc: string; cta: string; onClick: () => void; icon: string; color: string }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col transition-all duration-200 hover:shadow-md hover:-translate-y-0.5">
      <div className={`p-2.5 rounded-xl w-fit mb-4 ${color}`}>
        <Icon path={icon} className="w-5 h-5" />
      </div>
      <h4 className="text-base font-semibold text-slate-800">{title}</h4>
      <p className="text-sm text-slate-500 mt-1 mb-4 flex-1">{desc}</p>
      <button
        onClick={onClick}
        className="text-sm font-semibold text-blue-600 hover:text-blue-700 inline-flex items-center gap-1 group"
      >
        {cta}
        <Icon path={iconPaths.arrowRight} className="w-4 h-4 transition-transform group-hover:translate-x-1" />
      </button>
    </div>
  );
}

function ListSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Đang tải">
      <div className="h-24 bg-slate-100 rounded-2xl animate-pulse" />
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => <div key={i} className="h-32 bg-slate-100 rounded-2xl animate-pulse" />)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => <div key={i} className="h-48 bg-slate-100 rounded-2xl animate-pulse" />)}
      </div>
    </div>
  );
}

/* ================= Icons (Lucide-style paths) ================= */

const iconPaths: Record<string, string> = {
  shield: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
  check: "M20 6L9 17l-5-5",
  activity: "M22 12h-4l-3 9L9 3l-3 9H2",
  sparkles: "M12 3l1.9 5.8a2 2 0 001.3 1.3L21 12l-5.8 1.9a2 2 0 00-1.3 1.3L12 21l-1.9-5.8a2 2 0 00-1.3-1.3L3 12l5.8-1.9a2 2 0 001.3-1.3L12 3z",
  clock: "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zM12 6v6l4 2",
  users: "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2 M9 11a4 4 0 100-8 4 4 0 000 8z M23 21v-2a4 4 0 00-3-3.87 M16 3.13a4 4 0 010 7.75",
  scale: "M12 3v18 M7 21h10 M5 7l14 0 M5 7l-3 7h6l-3-7zM19 7l-3 7h6l-3-7z",
  heart: "M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z",
  chart: "M3 3v18h18 M7 14l4-4 4 4 5-5",
  arrowRight: "M5 12h14 M12 5l7 7-7 7",
};

function Icon({ path, className }: { path: string; className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d={path} />
    </svg>
  );
}
