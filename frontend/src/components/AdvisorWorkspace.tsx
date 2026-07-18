"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { CaseStateBadge } from "@/components/badges";
import { QueuePagination } from "@/components/QueuePagination";
import { useSetTopbarInfo } from "@/components/AppShell";
import { AdvisorUnavailable } from "@/components/AdvisorUnavailable";
import {
  advisorDemoStorageKey,
  allowedAdvisorDemoActions,
  countOverdueHandoffs,
  generateAdvisorDemoCases,
  handoffElapsedDays,
  isHandoffOverdue,
  markAdvisorDemoViewed,
  paginateAdvisorQueue,
  transitionAdvisorDemoCase,
  HANDOFF_ACK_OVERDUE_DAYS,
  type AdvisorDemoAction,
  type AdvisorDemoCase,
} from "@/lib/advisor-demo";
import { isAdvisorLocalDemoEnabled } from "@/lib/advisor-routing";
import { FACTOR_LABEL } from "@/lib/factors";
import { resolveLimitations } from "@/lib/limitations";

type Filter = "all" | "needs_action" | "follow_up_in_progress" | "monitoring" | "resolved";

type StoredDemo = {
  variant: number;
  cases: AdvisorDemoCase[];
};

const INITIAL_DEMO_NOW = new Date("2026-07-18T08:00:00+07:00");

const FILTERS: { id: Filter; label: string }[] = [
  { id: "all", label: "Tất cả" },
  { id: "needs_action", label: "Cần tiếp nhận" },
  { id: "follow_up_in_progress", label: "Đang hỗ trợ" },
  { id: "monitoring", label: "Đang theo dõi" },
  { id: "resolved", label: "Đã hoàn tất" },
];

type StatTone = "red" | "amber" | "sky" | "emerald";

const STAT_CARDS: { id: Exclude<Filter, "all">; label: string; sub: string; tone: StatTone; icon: ReactNode }[] = [
  { id: "needs_action", label: "Cần tiếp nhận", sub: "Cần xác nhận", tone: "red", icon: <InboxIcon /> },
  { id: "follow_up_in_progress", label: "Đang hỗ trợ", sub: "Đã tiếp nhận", tone: "amber", icon: <HandsIcon /> },
  { id: "monitoring", label: "Đang theo dõi", sub: "Có thời hạn", tone: "sky", icon: <EyeIcon /> },
  { id: "resolved", label: "Đã hoàn tất", sub: "Vòng hoàn tất", tone: "emerald", icon: <CheckIcon /> },
];

const TONE: Record<StatTone, { iconWrap: string; num: string; activeRing: string }> = {
  red: { iconWrap: "bg-red-50 text-red-600", num: "text-red-600", activeRing: "border-red-300 ring-2 ring-red-100" },
  amber: { iconWrap: "bg-amber-50 text-amber-600", num: "text-amber-600", activeRing: "border-amber-300 ring-2 ring-amber-100" },
  sky: { iconWrap: "bg-sky-50 text-sky-600", num: "text-sky-600", activeRing: "border-sky-300 ring-2 ring-sky-100" },
  emerald: { iconWrap: "bg-emerald-50 text-emerald-600", num: "text-emerald-600", activeRing: "border-emerald-300 ring-2 ring-emerald-100" },
};

export function AdvisorWorkspace({ accountId }: { accountId: string }) {
  if (!isAdvisorLocalDemoEnabled()) {
    return <AdvisorUnavailable surface="Hàng đợi case GVCN" />;
  }

  return <AdvisorLocalDemoWorkspace accountId={accountId} />;
}

function AdvisorLocalDemoWorkspace({ accountId }: { accountId: string }) {
  const [variant, setVariant] = useState(0);
  const [cases, setCases] = useState<AdvisorDemoCase[]>(() =>
    generateAdvisorDemoCases(accountId, 0, INITIAL_DEMO_NOW),
  );
  const [storageReady, setStorageReady] = useState(false);
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [monitorDate, setMonitorDate] = useState(defaultMonitorDate());
  const [notice, setNotice] = useState<string | null>(null);
  // Một mốc "bây giờ" ổn định cho một lần render để tính quá hạn không nhấp nháy.
  const [now] = useState(() => new Date());

  useEffect(() => {
    try {
      const raw = localStorage.getItem(advisorDemoStorageKey(accountId));
      if (raw) {
        const stored = JSON.parse(raw) as StoredDemo;
        if (Number.isInteger(stored.variant) && Array.isArray(stored.cases) && stored.cases.length > 0) {
          setVariant(stored.variant);
          setCases(stored.cases);
        }
      }
    } catch {
      // A malformed demo cache is disposable; the deterministic seed stays usable.
    }
    setStorageReady(true);
  }, [accountId]);

  useEffect(() => {
    if (!storageReady) return;
    try {
      localStorage.setItem(
        advisorDemoStorageKey(accountId),
        JSON.stringify({ variant, cases } satisfies StoredDemo),
      );
    } catch {
      // Local persistence is a convenience for the demo, never a workflow gate.
    }
  }, [accountId, cases, storageReady, variant]);

  const counts = useMemo<Record<Filter, number>>(
    () => ({
      all: cases.length,
      needs_action: cases.filter((item) => item.case_state === "assigned").length,
      follow_up_in_progress: cases.filter((item) => item.case_state === "follow_up_in_progress").length,
      monitoring: cases.filter((item) => item.case_state === "monitoring").length,
      resolved: cases.filter((item) => item.case_state === "resolved").length,
    }),
    [cases],
  );

  const latestUpdate = useMemo(
    () => cases.reduce((latest, item) => item.updated_at > latest ? item.updated_at : latest, ""),
    [cases],
  );
  const overdueCount = useMemo(() => countOverdueHandoffs(cases, now), [cases, now]);
  useSetTopbarInfo(latestUpdate || null, counts.needs_action);

  const visibleCases = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return [...cases]
      .filter((item) => {
        if (filter === "needs_action" && item.case_state !== "assigned") return false;
        if (filter !== "all" && filter !== "needs_action" && item.case_state !== filter) return false;
        if (!needle) return true;
        const factorText = item.contributing_factors
          .map((factor) => FACTOR_LABEL[factor.code] ?? factor.code)
          .join(" ")
          .toLowerCase();
        return item.student_ref.toLowerCase().includes(needle) || factorText.includes(needle);
      })
      .sort((left, right) => {
        const leftNeedsAction = left.case_state === "assigned" ? 1 : 0;
        const rightNeedsAction = right.case_state === "assigned" ? 1 : 0;
        if (leftNeedsAction !== rightNeedsAction) return rightNeedsAction - leftNeedsAction;
        return right.updated_at.localeCompare(left.updated_at);
      });
  }, [cases, filter, search]);

  // A filter/search change can shrink the list; reset to the first page so the view never strands.
  useEffect(() => {
    setPage(1);
  }, [filter, search]);

  const pageInfo = paginateAdvisorQueue(visibleCases, page);

  useEffect(() => {
    if (visibleCases.length === 0) {
      setSelectedId(null);
      return;
    }
    if (!visibleCases.some((item) => item.case_id === selectedId)) {
      setSelectedId(visibleCases[0].case_id);
    }
  }, [selectedId, visibleCases]);

  const selected = cases.find((item) => item.case_id === selectedId) ?? null;

  // Mở 1 case = GVCN đã nhấp vào (từ danh sách hoặc từ link trong email) → ghi nhận "đã xem".
  // Mở/đọc KHÁC với "đã tiếp nhận" — tiếp nhận vẫn là nút xác nhận riêng (accept).
  function openCase(caseId: string) {
    setSelectedId(caseId);
    setCases((current) => current.map((item) => (item.case_id === caseId ? markAdvisorDemoViewed(item, new Date()) : item)));
  }

  // Link bàn giao từ email: /advisor?case=<id> — mở đúng sinh viên và ghi nhận đã xem.
  // (Đăng nhập đã bị AppShell bắt buộc; đây là "login theo sự kiện", không phải mở dashboard hằng ngày.)
  useEffect(() => {
    if (!storageReady) return;
    const target = new URLSearchParams(window.location.search).get("case");
    if (target && cases.some((item) => item.case_id === target)) {
      openCase(target);
    }
    // Chạy một lần sau khi store demo sẵn sàng; cố ý chỉ đọc case ở thời điểm tải.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storageReady]);

  function regenerate(nextVariant: number) {
    const generated = generateAdvisorDemoCases(accountId, nextVariant, new Date());
    setVariant(nextVariant);
    setCases(generated);
    setFilter("all");
    setSearch("");
    setPage(1);
    setSelectedId(generated[0]?.case_id ?? null);
    setNotice(nextVariant === variant ? "Đã đặt lại tiến trình demo." : "Đã tạo một bộ case demo mới.");
  }

  function runAction(action: AdvisorDemoAction) {
    if (!selected) return;
    try {
      const monitoringUntil = action === "monitor"
        ? new Date(`${monitorDate}T00:00:00Z`).toISOString()
        : null;
      const updated = transitionAdvisorDemoCase(selected, action, new Date(), monitoringUntil);
      setCases((current) => current.map((item) => item.case_id === updated.case_id ? updated : item));
      setNotice(actionNotice(action));
    } catch (error) {
      setNotice(error instanceof Error && error.message === "missing_monitoring_until"
        ? "Hãy chọn thời hạn theo dõi trước."
        : "Thao tác không hợp lệ ở trạng thái hiện tại.");
    }
  }

  return (
    <div id="cases" className="scroll-mt-5 space-y-5">
      <DemoBanner onReset={() => regenerate(variant)} onRegenerate={() => regenerate(variant + 1)} />

      {notice && (
        <div role="status" className="flex items-center justify-between rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <span>✓ {notice}</span>
          <button type="button" onClick={() => setNotice(null)} className="font-semibold text-emerald-700">Đóng</button>
        </div>
      )}

      {overdueCount > 0 && (
        <div role="status" className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <span aria-hidden className="mt-0.5 flex-shrink-0 text-amber-500"><BellIcon /></span>
          <p className="leading-5">
            Khoa đề nghị Thầy/Cô xem và <strong>xác nhận tiếp nhận</strong> {overdueCount} case đang chờ quá {HANDOFF_ACK_OVERDUE_DAYS} ngày,
            để kịp thời hỗ trợ sinh viên. Mở case để xem chi tiết bảo mật rồi bấm “Xác nhận tiếp nhận”.
          </p>
        </div>
      )}

      <Hero total={cases.length} />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {STAT_CARDS.map((card) => (
          <StatCard
            key={card.id}
            card={card}
            count={counts[card.id]}
            active={filter === card.id}
            onSelect={() => setFilter((current) => (current === card.id ? "all" : card.id))}
          />
        ))}
      </div>

      <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(340px,0.65fr)]">
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="font-semibold text-slate-900">Hàng đợi của tôi</h3>
                <p className="mt-1 text-xs text-slate-500">Case cần tiếp nhận hoặc đang cần lên kế hoạch hỗ trợ.</p>
              </div>
              <label className="relative block min-w-[240px] flex-1 sm:max-w-xs">
                <span className="sr-only">Tìm case</span>
                <span aria-hidden className="pointer-events-none absolute left-3 top-2.5 text-slate-400">⌕</span>
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Tìm mã sinh viên hoặc lý do"
                  className="h-10 w-full rounded-lg border border-slate-200 bg-slate-50 pl-9 pr-3 text-sm outline-none focus:border-red-300 focus:ring-2 focus:ring-red-100"
                />
              </label>
            </div>

            <div className="mt-4 flex gap-2 overflow-x-auto pb-1" role="group" aria-label="Lọc case theo trạng thái">
              {FILTERS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setFilter(item.id)}
                  className={`whitespace-nowrap rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors ${
                    filter === item.id
                      ? "border-red-600 bg-red-600 text-white"
                      : "border-slate-200 bg-white text-slate-600 hover:border-red-200 hover:text-red-700"
                  }`}
                >
                  {item.label} ({counts[item.id]})
                </button>
              ))}
            </div>
          </div>

          <div className="divide-y divide-slate-100">
            {pageInfo.pageItems.length === 0 ? (
              <div className="px-6 py-14 text-center text-sm text-slate-500">
                Không có case nào khớp bộ lọc. Thử đổi trạng thái hoặc xóa từ khóa tìm kiếm.
              </div>
            ) : pageInfo.pageItems.map((item) => (
              <CaseRow
                key={item.case_id}
                item={item}
                selected={item.case_id === selectedId}
                overdue={isHandoffOverdue(item, now)}
                onSelect={() => openCase(item.case_id)}
              />
            ))}
          </div>

          {pageInfo.total > 0 && (
            <QueuePagination
              start={pageInfo.start}
              end={pageInfo.end}
              total={pageInfo.total}
              page={pageInfo.page}
              totalPages={pageInfo.totalPages}
              noun="case"
              onChange={setPage}
            />
          )}
        </section>

        <aside className="xl:sticky xl:top-5">
          {selected ? (
            <CasePanel
              item={selected}
              now={now}
              monitorDate={monitorDate}
              onMonitorDateChange={setMonitorDate}
              onAction={runAction}
            />
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
              Chọn một case để xem thông tin bàn giao.
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function Hero({ total }: { total: number }) {
  return (
    <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-red-600 to-red-700 p-6 text-white shadow-sm">
      <div className="relative z-10 max-w-2xl">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-red-100">Không gian cố vấn</p>
        <h2 className="mt-2 text-2xl font-bold leading-tight">Case đã được giao cho tôi</h2>
        <p className="mt-3 text-sm leading-6 text-red-50">
          Chỉ hiển thị lý do bàn giao và dữ liệu tối thiểu để bắt đầu hỗ trợ.
          <br className="hidden sm:block" />
          Không có bảng xếp hạng, raw score hay case chưa được phê duyệt.
        </p>
      </div>
      <span className="absolute right-5 top-5 z-10 inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold text-white ring-1 ring-inset ring-white/25">
        <ShieldIcon />
        {total} case pseudonymous
      </span>
      <span aria-hidden className="pointer-events-none absolute -right-2 bottom-2 z-0 text-white/15">
        <HeartHandsIcon />
      </span>
    </section>
  );
}

function StatCard({
  card,
  count,
  active,
  onSelect,
}: {
  card: (typeof STAT_CARDS)[number];
  count: number;
  active: boolean;
  onSelect: () => void;
}) {
  const tone = TONE[card.tone];
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={active}
      className={`group flex items-center justify-between gap-3 rounded-2xl border bg-white px-4 py-4 text-left shadow-sm transition-colors ${
        active ? tone.activeRing : "border-slate-200 hover:border-slate-300"
      }`}
    >
      <div className="flex items-center gap-3">
        <span className={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl ${tone.iconWrap}`}>{card.icon}</span>
        <div>
          <p className={`text-2xl font-bold leading-none ${tone.num}`}>{count}</p>
          <p className="mt-1.5 text-sm font-semibold text-slate-800">{card.label}</p>
          <p className="text-[11px] text-slate-400">{card.sub}</p>
        </div>
      </div>
      <span aria-hidden className="text-slate-300 transition-transform group-hover:translate-x-0.5">›</span>
    </button>
  );
}

function DemoBanner({ onReset, onRegenerate }: { onReset: () => void; onRegenerate: () => void }) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <span className="rounded-md bg-amber-100 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-amber-700">Demo</span>
      <div className="min-w-[240px] flex-1">
        <p className="text-sm leading-5 text-slate-700">
          Bạn chỉ thấy case đã được Ban quản lý phê duyệt và bàn giao.
          <br className="hidden sm:block" />
          Cách tiếp cận sinh viên do bạn quyết định theo bối cảnh thực tế.
        </p>
        <p className="mt-1 text-[11px] leading-4 text-slate-500">
          Bạn chỉ cần đăng nhập khi có sinh viên được gắn cờ (theo link trong email) — không phải mở dashboard mỗi ngày. Email là kênh chính.
        </p>
        <p className="mt-1 text-[11px] leading-4 text-slate-400">
          Dữ liệu sinh cục bộ, thao tác chỉ lưu trên trình duyệt — không ghi database và không chứng minh RBAC backend.
        </p>
      </div>
      <button type="button" onClick={onReset} className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50">
        <ResetIcon />
        Đặt lại tiến trình
      </button>
      <button type="button" onClick={onRegenerate} className="rounded-lg bg-red-600 px-3 py-2 text-xs font-semibold text-white hover:bg-red-700">
        Tạo bộ demo khác
      </button>
    </div>
  );
}

function CaseRow({ item, selected, overdue, onSelect }: { item: AdvisorDemoCase; selected: boolean; overdue: boolean; onSelect: () => void }) {
  const factor = item.contributing_factors[0];
  const factorLabel = factor ? FACTOR_LABEL[factor.code] ?? factor.code : "Xem chi tiết bàn giao";
  const unseen = item.case_state === "assigned" && !item.viewed_at;
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`grid w-full gap-3 px-5 py-4 text-left transition-colors sm:grid-cols-[minmax(150px,0.7fr)_minmax(220px,1.3fr)_auto] sm:items-center ${
        selected ? "bg-red-50/70 ring-1 ring-inset ring-red-100" : "hover:bg-slate-50"
      }`}
    >
      <div>
        <div className="flex items-center gap-2">
          <p className="font-mono text-sm font-bold text-slate-900">{item.student_ref}</p>
          {unseen && <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-500">Chưa xem</span>}
        </div>
        <p className="mt-1 text-xs text-slate-400">Giao {formatDate(item.assigned_at)}</p>
      </div>
      <div>
        <p className="text-sm font-medium text-slate-700">{factorLabel}</p>
        <p className="mt-1 text-xs text-slate-400">{item.coverage.n_valid_terms} kỳ · {item.coverage.n_courses} học phần</p>
      </div>
      <div className="flex items-center justify-between gap-3 sm:justify-end">
        {overdue && <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-bold text-amber-700">Quá hạn</span>}
        <CaseStateBadge state={item.case_state} />
        <span aria-hidden className="text-slate-300">›</span>
      </div>
    </button>
  );
}

function CasePanel({
  item,
  now,
  monitorDate,
  onMonitorDateChange,
  onAction,
}: {
  item: AdvisorDemoCase;
  now: Date;
  monitorDate: string;
  onMonitorDateChange: (value: string) => void;
  onAction: (action: AdvisorDemoAction) => void;
}) {
  const actions = allowedAdvisorDemoActions(item.case_state);
  const limitations = resolveLimitations(item.limitations);
  const factor = item.contributing_factors[0];
  const factorLabel = factor ? FACTOR_LABEL[factor.code] ?? factor.code : "Không có lý do bàn giao";
  const awaitingAccept = item.case_state === "assigned";
  const overdue = isHandoffOverdue(item, now);
  const elapsedDays = handoffElapsedDays(item, now);

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Chi tiết bàn giao</p>
            <h3 className="mt-1 font-mono text-lg font-bold text-slate-900">{item.student_ref}</h3>
          </div>
          <CaseStateBadge state={item.case_state} />
        </div>
        <p className="mt-3 text-xs leading-5 text-slate-500">
          Case pseudonymous · giao {formatDateTime(item.assigned_at)} · cập nhật {formatDateTime(item.updated_at)}
        </p>
      </div>

      <div className="space-y-5 p-5">
        <div className="flex items-center justify-between gap-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-xs">
          <span className="text-slate-500">Trạng thái xem</span>
          {item.viewed_at
            ? <span className="font-semibold text-emerald-700">Đã xem · {formatDateTime(item.viewed_at)}</span>
            : <span className="font-semibold text-slate-500">Chưa ghi nhận lượt xem</span>}
        </div>

        {awaitingAccept && (
          <div className={`rounded-xl border px-3 py-3 text-xs leading-5 ${overdue ? "border-amber-200 bg-amber-50 text-amber-900" : "border-sky-200 bg-sky-50 text-sky-800"}`}>
            {overdue
              ? <>Khoa đề nghị Thầy/Cô xác nhận tiếp nhận sớm — case đã chờ <strong>{elapsedDays} ngày</strong> (quá {HANDOFF_ACK_OVERDUE_DAYS} ngày) để kịp thời hỗ trợ sinh viên.</>
              : <>Case vừa được bàn giao và <strong>chưa được tiếp nhận</strong>. Xem chi tiết rồi bấm “Xác nhận tiếp nhận” để đóng vòng bàn giao với khoa.</>}
          </div>
        )}

        <section>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Lý do trung lập</p>
          <div className="mt-2 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-800">{factorLabel}</p>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              Bằng chứng: {factor?.evidence_refs.join(" → ") || "không có"}. Đây là tín hiệu để con người xem xét, không phải kết luận về sinh viên.
            </p>
          </div>
        </section>

        <section>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Dữ liệu tối thiểu</p>
          <dl className="mt-2 grid grid-cols-2 gap-2">
            <DataPoint label="Học kỳ hợp lệ" value={String(item.coverage.n_valid_terms)} />
            <DataPoint label="Học phần" value={String(item.coverage.n_courses)} />
          </dl>
          <ul className="mt-2 space-y-1 text-xs leading-5 text-slate-500">
            {limitations.map((limitation) => <li key={limitation.text}>• {limitation.text}</li>)}
          </ul>
        </section>

        {item.monitoring_until && (
          <div className="rounded-lg border border-sky-200 bg-sky-50 px-3 py-2 text-xs text-sky-800">
            Theo dõi đến {formatDate(item.monitoring_until)}.
          </div>
        )}

        <section className="border-t border-slate-100 pt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Bước tiếp theo</p>
          {actions.length === 0 ? (
            <p className="mt-2 text-sm text-slate-500">
              Vòng hỗ trợ hiện tại đã hoàn tất. Không có thao tác bổ sung trên case này.
            </p>
          ) : (
            <div className="mt-3 space-y-3">
              {actions.includes("accept") && (
                <ActionButton label="Xác nhận tiếp nhận" help="Bước xác nhận rõ ràng — mở/đọc chưa tính là tiếp nhận. Chuyển case sang Đang hỗ trợ và báo khoa đã tiếp nhận." onClick={() => onAction("accept")} primary />
              )}
              {actions.includes("monitor") && (
                <div className="rounded-xl border border-slate-200 p-3">
                  <label className="text-xs font-medium text-slate-600">
                    Theo dõi đến
                    <input
                      type="date"
                      value={monitorDate}
                      onChange={(event) => onMonitorDateChange(event.target.value)}
                      className="mt-2 h-9 w-full rounded-lg border border-slate-200 px-3 text-sm outline-none focus:border-sky-300"
                    />
                  </label>
                  <button type="button" onClick={() => onAction("monitor")} className="mt-2 w-full rounded-lg border border-sky-300 bg-sky-50 px-3 py-2 text-sm font-semibold text-sky-800 hover:bg-sky-100">
                    Chuyển sang theo dõi
                  </button>
                </div>
              )}
              {actions.includes("resolve") && (
                <ActionButton label="Hoàn tất vòng hỗ trợ" help="Đóng vòng hiện tại; không gắn nhãn cố định cho sinh viên." onClick={() => onAction("resolve")} />
              )}
            </div>
          )}
        </section>

        <p className="rounded-lg bg-slate-50 px-3 py-2 text-[11px] leading-5 text-slate-500">
          Không nhập ghi chép tư vấn nhạy cảm vào dashboard. Cách tiếp cận sinh viên do người phụ trách quyết định theo bối cảnh thực tế.
        </p>
      </div>
    </div>
  );
}

function DataPoint({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-white px-3 py-2">
      <dt className="text-[11px] text-slate-400">{label}</dt>
      <dd className="mt-0.5 text-sm font-bold text-slate-800">{value}</dd>
    </div>
  );
}

function ActionButton({ label, help, onClick, primary = false }: { label: string; help: string; onClick: () => void; primary?: boolean }) {
  return (
    <div>
      <button
        type="button"
        onClick={onClick}
        className={`w-full rounded-lg px-3 py-2.5 text-sm font-semibold ${
          primary ? "bg-red-600 text-white hover:bg-red-700" : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
        }`}
      >
        {label}
      </button>
      <p className="mt-1.5 text-[11px] leading-4 text-slate-400">{help}</p>
    </div>
  );
}

function defaultMonitorDate(): string {
  const date = new Date();
  date.setDate(date.getDate() + 14);
  return date.toISOString().slice(0, 10);
}

function actionNotice(action: AdvisorDemoAction): string {
  if (action === "accept") return "Đã xác nhận tiếp nhận case trong phiên demo.";
  if (action === "monitor") return "Đã chuyển case sang theo dõi có thời hạn trong phiên demo.";
  return "Đã hoàn tất vòng hỗ trợ trong phiên demo.";
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString("vi-VN");
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/* ---------- Icons (line style, inherit currentColor) ---------- */

const statSvg = {
  width: 22,
  height: 22,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

function InboxIcon() {
  return (
    <svg {...statSvg}>
      <path d="M22 12h-6l-2 3h-4l-2-3H2" />
      <path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
    </svg>
  );
}

function HandsIcon() {
  return (
    <svg {...statSvg}>
      <path d="M20 11a2 2 0 0 0-2-2h-3l-1.5-5.5a1.5 1.5 0 0 0-3 .3V9" />
      <path d="M4 13a2 2 0 0 1 2-2h2l2 4h4a2 2 0 0 1 0 4H9l-3-2H4z" />
    </svg>
  );
}

function EyeIcon() {
  return (
    <svg {...statSvg}>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg {...statSvg}>
      <circle cx="12" cy="12" r="9" />
      <path d="m8.5 12 2.5 2.5 4.5-5" />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

function BellIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
      <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
    </svg>
  );
}

function ResetIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
      <path d="M3 3v5h5" />
    </svg>
  );
}

function HeartHandsIcon() {
  return (
    <svg width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 21s-6.5-4-9-8.5a4.2 4.2 0 0 1 7.2-4.2L12 9l1.8-.7A4.2 4.2 0 0 1 21 12.5C18.5 17 12 21 12 21z" fill="currentColor" fillOpacity="0.35" />
    </svg>
  );
}
