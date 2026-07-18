"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { AdvisorDemoBanner } from "@/components/AdvisorDemoBanner";
import { AdvisorUnavailable } from "@/components/AdvisorUnavailable";
import { CaseStateBadge } from "@/components/badges";
import { useSetTopbarInfo } from "@/components/AppShell";
import { buildAdvisorFollowUps, type AdvisorFollowUpKind } from "@/lib/advisor-demo";
import { isAdvisorLocalDemoEnabled } from "@/lib/advisor-routing";
import { useAdvisorDemoSnapshot } from "@/lib/use-advisor-demo";

type ScheduleFilter = "all" | "overdue" | AdvisorFollowUpKind;
const DEMO_TODAY = new Date("2026-07-18T12:00:00+07:00");
const SOON_LIMIT = new Date("2026-07-26T00:00:00+07:00");

export function AdvisorFollowUpsWorkspace({ accountId }: { accountId: string }) {
  if (!isAdvisorLocalDemoEnabled()) {
    return <AdvisorUnavailable surface="Lịch theo dõi" />;
  }

  return <AdvisorFollowUpsLocalDemo accountId={accountId} />;
}

function AdvisorFollowUpsLocalDemo({ accountId }: { accountId: string }) {
  const { cases } = useAdvisorDemoSnapshot(accountId);
  const followUps = useMemo(() => buildAdvisorFollowUps(cases), [cases]);
  const [filter, setFilter] = useState<ScheduleFilter>("all");
  const overdue = followUps.filter((item) => new Date(item.due_at) < DEMO_TODAY).length;
  const dueSoon = followUps.filter((item) => {
    const due = new Date(item.due_at);
    return due >= DEMO_TODAY && due < SOON_LIMIT;
  }).length;
  const monitoring = followUps.filter((item) => item.kind === "monitoring_check").length;
  const latest = cases.reduce((value, item) => item.updated_at > value ? item.updated_at : value, "");
  const visibleItems = followUps.filter((item) => {
    if (filter === "all") return true;
    if (filter === "overdue") return new Date(item.due_at) < DEMO_TODAY;
    return item.kind === filter;
  });

  useSetTopbarInfo(latest || null, overdue);

  return (
    <div className="space-y-5">
      <AdvisorDemoBanner detail="Lịch được suy ra từ trạng thái case mock: tiếp nhận trong 2 ngày, cập nhật hỗ trợ sau 7 ngày và kiểm tra lại đúng hạn monitoring." />

      <section className="grid gap-4 sm:grid-cols-3">
        <Metric label="Đã quá hạn" value={overdue} detail="Theo mốc thời gian demo 18/07/2026" tone="red" />
        <Metric label="Sắp đến hạn" value={dueSoon} detail="Trong 7 ngày tiếp theo" tone="amber" />
        <Metric label="Lịch monitoring" value={monitoring} detail="Có ngày kiểm tra lại cụ thể" tone="sky" />
      </section>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Lịch công việc cá nhân</h2>
              <p className="mt-1 text-sm text-slate-500">Sắp theo hạn xử lý; không phải thứ tự ưu tiên hay xếp hạng sinh viên.</p>
            </div>
            <Link href="/advisor#cases" className="rounded-xl bg-red-600 px-4 py-2.5 text-sm font-semibold text-white no-underline hover:bg-red-700">
              Cập nhật tại Case của tôi
            </Link>
          </div>
          <div className="mt-4 flex flex-wrap gap-2" aria-label="Lọc lịch theo dõi">
            <ScheduleButton active={filter === "all"} onClick={() => setFilter("all")}>Tất cả</ScheduleButton>
            <ScheduleButton active={filter === "overdue"} onClick={() => setFilter("overdue")}>Quá hạn</ScheduleButton>
            <ScheduleButton active={filter === "accept_handoff"} onClick={() => setFilter("accept_handoff")}>Cần tiếp nhận</ScheduleButton>
            <ScheduleButton active={filter === "continue_support"} onClick={() => setFilter("continue_support")}>Đang hỗ trợ</ScheduleButton>
            <ScheduleButton active={filter === "monitoring_check"} onClick={() => setFilter("monitoring_check")}>Monitoring</ScheduleButton>
          </div>
        </div>

        <div className="divide-y divide-slate-100">
          {visibleItems.map((item) => {
            const isOverdue = new Date(item.due_at) < DEMO_TODAY;
            return (
              <article key={item.case_id} className="grid gap-4 px-5 py-5 md:grid-cols-[130px_minmax(180px,0.8fr)_minmax(220px,1.2fr)_auto] md:items-center">
                <div>
                  <p className={`text-sm font-bold ${isOverdue ? "text-red-700" : "text-slate-800"}`}>{formatDate(item.due_at)}</p>
                  <span className={`mt-1 inline-block rounded-full px-2 py-1 text-[11px] font-bold ${isOverdue ? "bg-red-50 text-red-700" : "bg-emerald-50 text-emerald-700"}`}>
                    {isOverdue ? "Quá hạn" : "Sắp tới"}
                  </span>
                </div>
                <div>
                  <p className="font-mono text-sm font-bold text-slate-800">{item.student_ref}</p>
                  <p className="mt-1 truncate text-xs text-slate-400">{item.case_id}</p>
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-700">{kindLabel(item.kind)}</p>
                  <div className="mt-2"><CaseStateBadge state={item.case_state} /></div>
                </div>
                <Link href="/advisor#cases" className="text-sm font-semibold text-red-600 no-underline hover:text-red-700">Mở case →</Link>
              </article>
            );
          })}
        </div>

        {visibleItems.length === 0 && (
          <div className="px-5 py-12 text-center">
            <p className="font-semibold text-slate-700">Không có công việc trong nhóm này</p>
            <p className="mt-1 text-sm text-slate-400">Chọn bộ lọc khác để xem lịch demo.</p>
          </div>
        )}
      </section>
    </div>
  );
}

function Metric({ label, value, detail, tone }: { label: string; value: number; detail: string; tone: "red" | "amber" | "sky" }) {
  const toneClass = {
    red: "bg-red-50 text-red-700",
    amber: "bg-amber-50 text-amber-700",
    sky: "bg-sky-50 text-sky-700",
  }[tone];
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <span className={`inline-flex min-w-11 items-center justify-center rounded-xl px-3 py-2 text-xl font-bold ${toneClass}`}>{value}</span>
      <p className="mt-3 text-sm font-semibold text-slate-800">{label}</p>
      <p className="mt-1 text-xs text-slate-400">{detail}</p>
    </div>
  );
}

function ScheduleButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button type="button" onClick={onClick} className={`rounded-lg border px-3 py-2 text-xs font-semibold transition ${active ? "border-red-200 bg-red-50 text-red-700" : "border-slate-200 bg-white text-slate-500 hover:bg-slate-50"}`}>
      {children}
    </button>
  );
}

function kindLabel(kind: AdvisorFollowUpKind): string {
  if (kind === "accept_handoff") return "Xác nhận đã tiếp nhận bàn giao";
  if (kind === "monitoring_check") return "Kiểm tra lại theo lịch monitoring";
  return "Cập nhật tiến trình hỗ trợ";
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString("vi-VN");
}
