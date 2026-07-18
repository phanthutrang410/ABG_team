"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { AdvisorDemoBanner } from "@/components/AdvisorDemoBanner";
import { AdvisorUnavailable } from "@/components/AdvisorUnavailable";
import { CaseStateBadge } from "@/components/badges";
import { useSetTopbarInfo } from "@/components/AppShell";
import { generateAdvisorDemoClasses } from "@/lib/advisor-demo";
import { isAdvisorLocalDemoEnabled } from "@/lib/advisor-routing";
import { useAdvisorDemoSnapshot } from "@/lib/use-advisor-demo";

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
                  className={`w-full rounded-xl border px-4 py-3 text-left transition ${active ? "border-red-200 bg-red-50" : "border-slate-100 bg-slate-50 hover:border-slate-200"}`}
                >
                  <span className={`block font-semibold ${active ? "text-red-700" : "text-slate-800"}`}>{item.class_code}</span>
                  <span className="mt-1 block text-xs text-slate-500">{item.students.length} sinh viên · {withCase} case được giao</span>
                </button>
              );
            })}
          </div>
          <div className="mt-4 rounded-xl bg-slate-50 p-3 text-xs leading-5 text-slate-500">
            Không có case không đồng nghĩa sinh viên “an toàn”. Trang này không xếp hạng hoặc suy diễn mức rủi ro.
          </div>
        </aside>

        <section className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-bold text-slate-900">{selectedClass?.class_code}</h2>
                <p className="mt-1 text-sm text-slate-500">Danh sách giả danh trong phạm vi lớp demo</p>
              </div>
              <div className="flex gap-2 text-xs">
                <span className="rounded-full bg-slate-100 px-3 py-1.5 font-medium text-slate-600">{selectedClass?.students.length ?? 0} sinh viên</span>
                <span className="rounded-full bg-red-50 px-3 py-1.5 font-medium text-red-700">{assignedCount} có case được giao</span>
              </div>
            </div>

            <div className="mt-4 flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
              <label className="relative block min-w-0 flex-1 xl:max-w-md">
                <span className="sr-only">Tìm theo mã sinh viên giả danh</span>
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Tìm mã sinh viên giả danh…"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-800 outline-none transition focus:border-red-300 focus:bg-white focus:ring-2 focus:ring-red-100"
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
                {visibleStudents.map((student) => (
                  <tr key={student.student_ref} className="hover:bg-slate-50/70">
                    <td className="px-5 py-4">
                      <p className="font-mono text-sm font-bold text-slate-800">{student.student_ref}</p>
                      <p className="mt-1 text-xs text-slate-400">Mã giả danh demo</p>
                    </td>
                    <td className="px-5 py-4 text-sm text-slate-600">{student.class_code}</td>
                    <td className="px-5 py-4">
                      {student.case_state
                        ? <CaseStateBadge state={student.case_state} />
                        : <span className="text-sm text-slate-400">Chưa có case được giao</span>}
                    </td>
                    <td className="px-5 py-4 text-right">
                      {student.case_id
                        ? <Link href="/advisor#cases" className="text-sm font-semibold text-red-600 no-underline hover:text-red-700">Mở hàng đợi →</Link>
                        : <span className="text-xs text-slate-300">Không có thao tác</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {visibleStudents.length === 0 && (
            <div className="px-5 py-12 text-center">
              <p className="font-semibold text-slate-700">Không tìm thấy sinh viên phù hợp</p>
              <p className="mt-1 text-sm text-slate-400">Thử đổi từ khóa hoặc bộ lọc roster.</p>
            </div>
          )}
        </section>
      </section>
    </div>
  );
}

function FilterButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-lg border px-3 py-2 text-xs font-semibold transition ${active ? "border-red-200 bg-red-50 text-red-700" : "border-slate-200 bg-white text-slate-500 hover:bg-slate-50"}`}
    >
      {children}
    </button>
  );
}
