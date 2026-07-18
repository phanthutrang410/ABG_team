"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { AdvisorDemoBanner } from "@/components/AdvisorDemoBanner";
import { AdvisorUnavailable } from "@/components/AdvisorUnavailable";
import { QueuePagination } from "@/components/QueuePagination";
import { useSetTopbarInfo } from "@/components/AppShell";
import { generateAdvisorDemoClasses, paginateAdvisorQueue } from "@/lib/advisor-demo";
import { isAdvisorLocalDemoEnabled } from "@/lib/advisor-routing";
import { useAdvisorDemoSnapshot } from "@/lib/use-advisor-demo";
import type { CaseState } from "@/lib/types";

type RosterFilter = "all" | "with_case" | "without_case";

export function AdvisorClassesWorkspace({ accountId }: { accountId: string }) {
  if (!isAdvisorLocalDemoEnabled()) {
    return <AdvisorUnavailable surface="Lớp & sinh viên" />;
  }

  return <AdvisorClassesLocalDemo accountId={accountId} />;
}

function AdvisorClassesLocalDemo({ accountId }: { accountId: string }) {
  const { cases, variant } = useAdvisorDemoSnapshot(accountId);
  const classes = useMemo(
    () => generateAdvisorDemoClasses(accountId, variant, cases),
    [accountId, cases, variant],
  );
  const [selectedCode, setSelectedCode] = useState("K66-CNTT-A");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<RosterFilter>("all");
  const [page, setPage] = useState(1);
  const selectedClass = classes.find((item) => item.class_code === selectedCode) ?? classes[0];
  const latest = cases.reduce((value, item) => item.updated_at > value ? item.updated_at : value, "");
  const assignedCount = selectedClass?.students.filter((student) => student.case_id).length ?? 0;

  const visibleStudents = (selectedClass?.students ?? []).filter((student) => {
    const matchesQuery = student.student_ref.toLowerCase().includes(query.trim().toLowerCase());
    const matchesFilter = filter === "all"
      || (filter === "with_case" && student.case_id !== null)
      || (filter === "without_case" && student.case_id === null);
    return matchesQuery && matchesFilter;
  });

  // Switching class or narrowing the roster can shrink the list; reset to page 1 so the view never strands.
  useEffect(() => {
    setPage(1);
  }, [selectedCode, query, filter]);

  const pageInfo = paginateAdvisorQueue(visibleStudents, page);

  useSetTopbarInfo(latest || null, assignedCount);

  return (
    <div className="space-y-5">
      <AdvisorDemoBanner detail="Roster này được sinh cục bộ để duyệt UI. Mỗi sinh viên chỉ có mã giả danh và trạng thái bàn giao tối thiểu." />

      <section className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="px-1 pb-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Lớp phụ trách</p>
            <p className="mt-1 text-sm text-slate-500">Kỳ học demo 20251</p>
          </div>
          <div className="space-y-2">
            {classes.map((item) => {
              const active = item.class_code === selectedClass?.class_code;
              const withCase = item.students.filter((student) => student.case_id).length;
              return (
                <button
                  key={item.class_code}
                  type="button"
                  onClick={() => setSelectedCode(item.class_code)}
                  className={`flex w-full items-center gap-3 rounded-xl border px-3 py-3 text-left transition ${active ? "border-red-200 bg-red-50" : "border-slate-100 bg-slate-50 hover:border-slate-200"}`}
                >
                  <span className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full ${active ? "bg-white text-red-600 ring-1 ring-red-200" : "bg-white text-slate-400 ring-1 ring-slate-200"}`}>
                    <GradCapIcon />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className={`block font-semibold ${active ? "text-red-700" : "text-slate-800"}`}>{item.class_code}</span>
                    <span className="mt-0.5 block text-xs text-slate-500">{item.students.length} sinh viên · {withCase} case được giao</span>
                  </span>
                  <span
                    aria-hidden
                    className={`flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full ${active ? "bg-red-600 text-white" : "text-slate-300"}`}
                  >
                    ›
                  </span>
                </button>
              );
            })}
          </div>
          <div className="mt-4 flex items-start gap-2 rounded-xl bg-slate-50 p-3 text-xs leading-5 text-slate-500">
            <span aria-hidden className="mt-0.5 flex-shrink-0 text-slate-400"><ShieldIcon /></span>
            <span>Không có case không đồng nghĩa sinh viên “an toàn”. Trang này không xếp hạng hoặc suy diễn mức rủi ro.</span>
          </div>
        </aside>

        <div className="min-w-0 space-y-4">
          <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-red-600 to-red-700 p-5 text-white shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <span className="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-full bg-white/15 ring-1 ring-inset ring-white/25">
                  <GradCapIcon large />
                </span>
                <div>
                  <h2 className="text-2xl font-bold leading-tight">{selectedClass?.class_code}</h2>
                  <p className="mt-1 text-sm text-red-50">Danh sách giả danh trong phạm vi lớp demo</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-slate-800 shadow-sm">
                  <span className="text-red-600"><UsersIcon /></span>
                  {selectedClass?.students.length ?? 0} sinh viên
                </span>
                <span className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-slate-800 shadow-sm">
                  <span className="text-red-600"><BriefcaseIcon /></span>
                  {assignedCount} có case được giao
                </span>
              </div>
            </div>
          </section>

          <section className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 p-5">
              <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
                <label className="relative block min-w-0 flex-1 xl:max-w-md">
                  <span className="sr-only">Tìm theo mã sinh viên giả danh</span>
                  <span aria-hidden className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"><SearchIcon /></span>
                  <input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Tìm mã sinh viên giả danh…"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm text-slate-800 outline-none transition focus:border-red-300 focus:bg-white focus:ring-2 focus:ring-red-100"
                  />
                </label>
                <div className="flex flex-wrap gap-2" aria-label="Lọc roster">
                  <FilterButton active={filter === "all"} onClick={() => setFilter("all")}>Tất cả</FilterButton>
                  <FilterButton active={filter === "with_case"} onClick={() => setFilter("with_case")}>Có case được giao</FilterButton>
                  <FilterButton active={filter === "without_case"} onClick={() => setFilter("without_case")}>Chưa có case</FilterButton>
                </div>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px] border-collapse text-left">
                <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  <tr>
                    <th className="px-5 py-3">Sinh viên</th>
                    <th className="px-5 py-3">Lớp</th>
                    <th className="px-5 py-3">Trạng thái hỗ trợ</th>
                    <th className="px-5 py-3 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {pageInfo.pageItems.map((student) => (
                    <tr key={student.student_ref} className="hover:bg-slate-50/70">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <span className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-slate-100 text-sm font-semibold text-slate-500" aria-hidden>S</span>
                          <div>
                            <p className="font-mono text-sm font-bold text-slate-800">{student.student_ref}</p>
                            <p className="mt-1 text-xs text-slate-400">Mã giả danh demo</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-sm text-slate-600">{student.class_code}</td>
                      <td className="px-5 py-4">
                        <RosterStatusBadge state={student.case_state} />
                      </td>
                      <td className="px-5 py-4 text-right">
                        {student.case_id
                          ? (
                            <Link href="/advisor#cases" className="inline-flex items-center gap-1 text-sm font-semibold text-red-600 no-underline hover:text-red-700">
                              Mở hàng đợi <span aria-hidden>→</span>
                            </Link>
                          )
                          : <span className="text-xs text-slate-300">Không có thao tác</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {visibleStudents.length === 0 ? (
              <div className="px-5 py-12 text-center">
                <p className="font-semibold text-slate-700">Không tìm thấy sinh viên phù hợp</p>
                <p className="mt-1 text-sm text-slate-400">Thử đổi từ khóa hoặc bộ lọc roster.</p>
              </div>
            ) : (
              <QueuePagination
                start={pageInfo.start}
                end={pageInfo.end}
                total={pageInfo.total}
                page={pageInfo.page}
                totalPages={pageInfo.totalPages}
                noun="sinh viên"
                onChange={setPage}
              />
            )}
          </section>
        </div>
      </section>
    </div>
  );
}

function FilterButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-lg border px-3.5 py-2 text-xs font-semibold transition ${active ? "border-red-600 bg-red-600 text-white" : "border-slate-200 bg-white text-slate-600 hover:border-red-200 hover:text-red-700"}`}
    >
      {children}
    </button>
  );
}

const ROSTER_STATUS: Record<string, { label: string; cls: string; icon: ReactNode }> = {
  assigned: { label: "Đã bàn giao", cls: "bg-emerald-50 text-emerald-700", icon: <CheckCircleIcon /> },
  follow_up_in_progress: { label: "Đang hỗ trợ", cls: "bg-emerald-50 text-emerald-700", icon: <HeadsetIcon /> },
  monitoring: { label: "Đang theo dõi", cls: "bg-sky-50 text-sky-700", icon: <EyeIcon /> },
  resolved: { label: "Đã xử lý", cls: "bg-emerald-50 text-emerald-700", icon: <CheckCircleIcon /> },
  none: { label: "Chưa có case được giao", cls: "bg-slate-100 text-slate-500", icon: <CircleIcon /> },
};

function RosterStatusBadge({ state }: { state: CaseState | null }) {
  const meta = ROSTER_STATUS[state ?? "none"] ?? ROSTER_STATUS.none;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${meta.cls}`}>
      <span aria-hidden className="flex">{meta.icon}</span>
      {meta.label}
    </span>
  );
}

/* ---------- Icons (line style, inherit currentColor) ---------- */

const iconSvg = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

function GradCapIcon({ large = false }: { large?: boolean }) {
  const size = large ? 26 : 20;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...iconSvg}>
      <path d="M22 10 12 5 2 10l10 5 10-5z" />
      <path d="M6 12v5c0 1 2.7 2.5 6 2.5s6-1.5 6-2.5v-5" />
      <path d="M22 10v5" />
    </svg>
  );
}

function UsersIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" {...iconSvg}>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

function BriefcaseIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" {...iconSvg}>
      <rect x="2" y="7" width="20" height="14" rx="2" />
      <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
      <path d="M2 13h20" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" {...iconSvg}>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" {...iconSvg}>
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}

function EyeIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" {...iconSvg}>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function HeadsetIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" {...iconSvg}>
      <path d="M4 14v-2a8 8 0 0 1 16 0v2" />
      <path d="M4 14a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-2a2 2 0 0 1 2-2z" />
      <path d="M20 14a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2 2 2 0 0 0 2-2v-2a2 2 0 0 0-2-2z" />
      <path d="M20 18v1a3 3 0 0 1-3 3h-4" />
    </svg>
  );
}

function CheckCircleIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" {...iconSvg}>
      <circle cx="12" cy="12" r="9" />
      <path d="m8.5 12 2.5 2.5 4.5-5" />
    </svg>
  );
}

function CircleIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" {...iconSvg} strokeDasharray="3 3">
      <circle cx="12" cy="12" r="9" />
    </svg>
  );
}
