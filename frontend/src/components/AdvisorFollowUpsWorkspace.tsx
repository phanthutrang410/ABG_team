"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { AdvisorDemoBanner } from "@/components/AdvisorDemoBanner";
import { AdvisorUnavailable } from "@/components/AdvisorUnavailable";
import { QueuePagination } from "@/components/QueuePagination";
import { useSetTopbarInfo } from "@/components/AppShell";
import {
  buildAdvisorFollowUps,
  paginateAdvisorQueue,
  type AdvisorFollowUpItem,
  type AdvisorFollowUpKind,
} from "@/lib/advisor-demo";
import { isAdvisorLocalDemoEnabled } from "@/lib/advisor-routing";
import { useAdvisorDemoSnapshot } from "@/lib/use-advisor-demo";
import { CASE_STATE_LABEL, type CaseState } from "@/lib/types";

type ScheduleFilter = "all" | "overdue" | AdvisorFollowUpKind;

const DEMO_TODAY = new Date("2026-07-18T12:00:00+07:00");
const SOON_LIMIT = new Date("2026-07-26T00:00:00+07:00");
const PAGE_SIZE = 5;
const WEEKDAYS = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];
const MONTH_NAMES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"];

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
  const [page, setPage] = useState(1);

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

  useEffect(() => {
    setPage(1);
  }, [filter]);

  const pageInfo = paginateAdvisorQueue(visibleItems, page, PAGE_SIZE);

  useSetTopbarInfo(latest || null, overdue);

  return (
    <div className="space-y-5">
      <AdvisorDemoBanner detail="Lịch được suy ra từ trạng thái case demo: tiếp nhận trong 2 ngày, cập nhật hỗ trợ sau 7 ngày và kiểm tra lại đúng hạn monitoring." />

      <section className="grid gap-4 sm:grid-cols-3">
        <Metric label="Đã quá hạn" value={overdue} detail="Theo mốc thời gian demo 18/07/2026" tone="red" icon={<ClockIcon />} />
        <Metric label="Sắp đến hạn" value={dueSoon} detail="Trong 7 ngày tiếp theo" tone="amber" icon={<CalendarIcon />} />
        <Metric label="Lịch monitoring" value={monitoring} detail="Có ngày kiểm tra lại cụ thể" tone="sky" icon={<TargetIcon />} />
      </section>

      <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1.55fr)_minmax(320px,0.75fr)]">
        <section className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <span className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl bg-red-50 text-red-600"><CalendarIcon /></span>
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Lịch công việc cá nhân</h2>
                  <p className="mt-1 text-sm text-slate-500">Sắp theo hạn xử lý; không phải thứ tự ưu tiên hay xếp hạng sinh viên.</p>
                </div>
              </div>
              <Link href="/advisor#cases" className="inline-flex items-center gap-2 rounded-xl bg-red-600 px-4 py-2.5 text-sm font-semibold text-white no-underline hover:bg-red-700">
                <UploadIcon />
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

          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] border-collapse text-left">
              <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-5 py-3">Hạn xử lý</th>
                  <th className="px-5 py-3">Sinh viên / Assignment</th>
                  <th className="px-5 py-3">Công việc</th>
                  <th className="px-5 py-3">Trạng thái</th>
                  <th className="px-5 py-3 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {pageInfo.pageItems.map((item) => {
                  const isOverdue = new Date(item.due_at) < DEMO_TODAY;
                  return (
                    <tr key={item.case_id} className="hover:bg-slate-50/70">
                      <td className="px-5 py-4 align-top">
                        <p className={`text-sm font-bold ${isOverdue ? "text-red-600" : "text-slate-800"}`}>{formatDate(item.due_at)}</p>
                        <span className={`mt-1 inline-block rounded-md px-2 py-0.5 text-[11px] font-bold ${isOverdue ? "bg-red-50 text-red-600" : "bg-sky-50 text-sky-700"}`}>
                          {isOverdue ? "Quá hạn" : "Sắp tới"}
                        </span>
                      </td>
                      <td className="px-5 py-4 align-top">
                        <p className="font-mono text-sm font-bold text-slate-800">{item.student_ref}</p>
                        <p className="mt-1 truncate text-xs text-slate-400">{item.case_id}</p>
                      </td>
                      <td className="px-5 py-4 align-top text-sm text-slate-700">{kindLabel(item.kind)}</td>
                      <td className="px-5 py-4 align-top"><StatusPill state={item.case_state} /></td>
                      <td className="px-5 py-4 text-right align-top">
                        <Link href="/advisor#cases" className="inline-flex items-center gap-1 text-sm font-semibold text-red-600 no-underline hover:text-red-700">
                          Mở case <span aria-hidden>→</span>
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {visibleItems.length === 0 ? (
            <div className="px-5 py-12 text-center">
              <p className="font-semibold text-slate-700">Không có công việc trong nhóm này</p>
              <p className="mt-1 text-sm text-slate-400">Chọn bộ lọc khác để xem lịch demo.</p>
            </div>
          ) : (
            <QueuePagination
              start={pageInfo.start}
              end={pageInfo.end}
              total={pageInfo.total}
              page={pageInfo.page}
              totalPages={pageInfo.totalPages}
              noun="kết quả"
              onChange={setPage}
            />
          )}
        </section>

        <ScheduleCalendar followUps={followUps} />
      </div>
    </div>
  );
}

/* ---------- Calendar (adapted to the system: marks case follow-up deadlines) ---------- */

function dayKey(date: Date): string {
  return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
}

function ScheduleCalendar({ followUps }: { followUps: AdvisorFollowUpItem[] }) {
  const [view, setView] = useState({ year: DEMO_TODAY.getFullYear(), month: DEMO_TODAY.getMonth() });
  const [selectedKey, setSelectedKey] = useState(dayKey(DEMO_TODAY));

  const eventKeys = useMemo(() => new Set(followUps.map((item) => dayKey(new Date(item.due_at)))), [followUps]);
  const todayKey = dayKey(DEMO_TODAY);

  const selectedItems = useMemo(
    () => followUps
      .filter((item) => dayKey(new Date(item.due_at)) === selectedKey)
      .sort((left, right) => left.due_at.localeCompare(right.due_at)),
    [followUps, selectedKey],
  );

  const firstWeekday = (new Date(view.year, view.month, 1).getDay() + 6) % 7; // Mon = 0
  const daysInMonth = new Date(view.year, view.month + 1, 0).getDate();
  const cells: (number | null)[] = [
    ...Array.from({ length: firstWeekday }, () => null),
    ...Array.from({ length: daysInMonth }, (_, index) => index + 1),
  ];

  function shiftMonth(delta: number) {
    setView((current) => {
      const next = new Date(current.year, current.month + delta, 1);
      return { year: next.getFullYear(), month: next.getMonth() };
    });
  }

  function goToday() {
    setView({ year: DEMO_TODAY.getFullYear(), month: DEMO_TODAY.getMonth() });
    setSelectedKey(todayKey);
  }

  const [selYear, selMonth, selDay] = selectedKey.split("-").map(Number);
  const selectedLabel = `${String(selDay).padStart(2, "0")}/${String(selMonth + 1).padStart(2, "0")}/${selYear}`;

  return (
    <aside className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm xl:sticky xl:top-5">
      <div className="p-5">
        <div className="flex items-center justify-between">
          <button type="button" onClick={goToday} className="rounded-full border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-600 hover:bg-red-50">
            Hôm nay
          </button>
          <span className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600">
            Tháng {MONTH_NAMES[view.month]}, {view.year}
          </span>
        </div>

        <div className="mt-4 flex items-center justify-center gap-4">
          <button type="button" onClick={() => shiftMonth(-1)} aria-label="Tháng trước" className="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-600">‹</button>
          <span className="text-sm font-bold text-slate-900">Tháng {MONTH_NAMES[view.month]}, {view.year}</span>
          <button type="button" onClick={() => shiftMonth(1)} aria-label="Tháng sau" className="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-600">›</button>
        </div>

        <div className="mt-3 grid grid-cols-7 gap-1 text-center text-[11px] font-semibold text-slate-400">
          {WEEKDAYS.map((label) => <span key={label} className="py-1">{label}</span>)}
        </div>
        <div className="grid grid-cols-7 gap-1">
          {cells.map((day, index) => {
            if (day === null) return <span key={`blank-${index}`} />;
            const key = `${view.year}-${view.month}-${day}`;
            const isToday = key === todayKey;
            const isSelected = key === selectedKey;
            const hasEvent = eventKeys.has(key);
            return (
              <button
                key={key}
                type="button"
                onClick={() => setSelectedKey(key)}
                aria-pressed={isSelected}
                className="relative flex h-9 items-center justify-center"
              >
                <span
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-sm transition-colors ${
                    isToday
                      ? "bg-red-600 font-bold text-white"
                      : isSelected
                        ? "bg-sky-100 font-semibold text-sky-700 ring-1 ring-sky-400"
                        : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {day}
                </span>
                {hasEvent && (
                  <span
                    aria-hidden
                    className={`absolute bottom-0.5 h-1.5 w-1.5 rounded-full ${isToday ? "bg-white" : "bg-amber-500"}`}
                  />
                )}
              </button>
            );
          })}
        </div>
      </div>

      <div className="border-t border-slate-100 bg-slate-50/60 p-5">
        <div className="flex items-center gap-2">
          <span className="text-red-500"><PencilIcon /></span>
          <h3 className="text-sm font-bold text-slate-900">Mốc theo dõi ngày {selectedLabel}</h3>
        </div>

        {selectedItems.length === 0 ? (
          <p className="mt-3 rounded-xl border border-dashed border-slate-200 bg-white px-3 py-4 text-center text-xs text-slate-400">
            Không có mốc theo dõi trong ngày này.
          </p>
        ) : (
          <ul className="mt-3 space-y-2">
            {selectedItems.map((item) => (
              <li key={item.case_id} className="flex gap-3 rounded-xl border border-slate-200 bg-white p-3">
                <span className="mt-0.5 font-mono text-xs font-semibold text-red-600">{formatTime(item.due_at)}</span>
                <div className="min-w-0 flex-1">
                  <p className="font-mono text-sm font-bold text-slate-800">{item.student_ref}</p>
                  <p className="mt-0.5 text-xs text-slate-500">{kindLabel(item.kind)}</p>
                  <div className="mt-1.5"><StatusPill state={item.case_state} /></div>
                </div>
              </li>
            ))}
          </ul>
        )}

        <Link href="/advisor#cases" className="mt-4 flex items-center justify-center gap-1 rounded-xl border border-red-200 bg-white px-4 py-2.5 text-sm font-semibold text-red-600 no-underline hover:bg-red-50">
          Xử lý trong Case của tôi <span aria-hidden>→</span>
        </Link>
      </div>
    </aside>
  );
}

/* ---------- Pieces ---------- */

type MetricTone = "red" | "amber" | "sky";

function Metric({ label, value, detail, tone, icon }: { label: string; value: number; detail: string; tone: MetricTone; icon: ReactNode }) {
  const style = {
    red: { card: "border-red-100 bg-red-50/60", num: "text-red-600", iconWrap: "bg-red-100 text-red-500" },
    amber: { card: "border-amber-100 bg-amber-50/60", num: "text-amber-500", iconWrap: "bg-amber-100 text-amber-500" },
    sky: { card: "border-sky-100 bg-sky-50/60", num: "text-sky-600", iconWrap: "bg-sky-100 text-sky-500" },
  }[tone];
  return (
    <div className={`rounded-2xl border p-5 shadow-sm ${style.card}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className={`text-4xl font-bold leading-none ${style.num}`}>{value}</p>
          <p className="mt-3 text-sm font-semibold text-slate-800">{label}</p>
          <p className="mt-1 text-xs text-slate-500">{detail}</p>
        </div>
        <span className={`flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full ${style.iconWrap}`}>{icon}</span>
      </div>
    </div>
  );
}

function ScheduleButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button type="button" onClick={onClick} className={`rounded-lg border px-3.5 py-2 text-xs font-semibold transition ${active ? "border-red-600 bg-red-600 text-white" : "border-slate-200 bg-white text-slate-600 hover:border-red-200 hover:text-red-700"}`}>
      {children}
    </button>
  );
}

function StatusPill({ state }: { state: CaseState }) {
  const dot = state === "monitoring" ? "bg-sky-500" : "bg-emerald-500";
  const cls = state === "monitoring" ? "bg-sky-50 text-sky-700" : "bg-emerald-50 text-emerald-700";
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${cls}`}>
      {CASE_STATE_LABEL[state]}
      <span aria-hidden className={`h-1.5 w-1.5 rounded-full ${dot}`} />
    </span>
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

function formatTime(value: string): string {
  return new Date(value).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
}

/* ---------- Icons ---------- */

const iconSvg = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

function ClockIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" {...iconSvg}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </svg>
  );
}

function CalendarIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" {...iconSvg}>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M16 3v4M8 3v4M3 10h18" />
    </svg>
  );
}

function TargetIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" {...iconSvg}>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" />
    </svg>
  );
}

function UploadIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" {...iconSvg}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <path d="M17 8l-5-5-5 5" />
      <path d="M12 3v12" />
    </svg>
  );
}

function PencilIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" {...iconSvg}>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z" />
    </svg>
  );
}
