"use client";

import { useEffect, useMemo, useState } from "react";
import { CaseStateBadge } from "@/components/badges";
import { useSetTopbarInfo } from "@/components/AppShell";
import {
  advisorDemoStorageKey,
  allowedAdvisorDemoActions,
  generateAdvisorDemoCases,
  transitionAdvisorDemoCase,
  type AdvisorDemoAction,
  type AdvisorDemoCase,
} from "@/lib/advisor-demo";
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

export function AdvisorWorkspace({ accountId }: { accountId: string }) {
  const [variant, setVariant] = useState(0);
  const [cases, setCases] = useState<AdvisorDemoCase[]>(() =>
    generateAdvisorDemoCases(accountId, 0, INITIAL_DEMO_NOW),
  );
  const [storageReady, setStorageReady] = useState(false);
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [monitorDate, setMonitorDate] = useState(defaultMonitorDate());
  const [notice, setNotice] = useState<string | null>(null);

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

  const assignedCount = useMemo(
    () => cases.filter((item) => item.case_state === "assigned").length,
    [cases],
  );

  const latestUpdate = useMemo(
    () => cases.reduce((latest, item) => item.updated_at > latest ? item.updated_at : latest, ""),
    [cases],
  );
  useSetTopbarInfo(latestUpdate || null, assignedCount);

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

  function regenerate(nextVariant: number) {
    const generated = generateAdvisorDemoCases(accountId, nextVariant, new Date());
    setVariant(nextVariant);
    setCases(generated);
    setFilter("all");
    setSearch("");
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

      <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(340px,0.65fr)]">
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="font-semibold text-slate-900">Hàng đợi của tôi</h3>
                <p className="mt-1 text-xs text-slate-500">Case cần tiếp nhận luôn được đưa lên đầu.</p>
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
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          <div className="divide-y divide-slate-100">
            {visibleCases.length === 0 ? (
              <div className="px-6 py-14 text-center text-sm text-slate-500">
                Không có case nào khớp bộ lọc. Thử đổi trạng thái hoặc xóa từ khóa tìm kiếm.
              </div>
            ) : visibleCases.map((item) => (
              <CaseRow
                key={item.case_id}
                item={item}
                selected={item.case_id === selectedId}
                onSelect={() => setSelectedId(item.case_id)}
              />
            ))}
          </div>
        </section>

        <aside className="xl:sticky xl:top-5">
          {selected ? (
            <CasePanel
              item={selected}
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

function DemoBanner({ onReset, onRegenerate }: { onReset: () => void; onRegenerate: () => void }) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-950">
      <span className="rounded-full bg-amber-200 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide">Dữ liệu demo</span>
      <p className="min-w-[240px] flex-1 text-sm leading-5">
        Case được sinh cục bộ để thử UI phân vai; thao tác chỉ lưu trên trình duyệt, không ghi database và không chứng minh RBAC backend.
      </p>
      <button type="button" onClick={onReset} className="rounded-lg border border-amber-300 bg-white px-3 py-2 text-xs font-semibold hover:bg-amber-100">
        Đặt lại tiến trình
      </button>
      <button type="button" onClick={onRegenerate} className="rounded-lg bg-amber-900 px-3 py-2 text-xs font-semibold text-white hover:bg-amber-800">
        Tạo bộ demo khác
      </button>
    </div>
  );
}

function CaseRow({ item, selected, onSelect }: { item: AdvisorDemoCase; selected: boolean; onSelect: () => void }) {
  const factor = item.contributing_factors[0];
  const factorLabel = factor ? FACTOR_LABEL[factor.code] ?? factor.code : "Xem chi tiết bàn giao";
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`grid w-full gap-3 px-5 py-4 text-left transition-colors sm:grid-cols-[minmax(150px,0.7fr)_minmax(220px,1.3fr)_auto] sm:items-center ${
        selected ? "bg-red-50/70 ring-1 ring-inset ring-red-100" : "hover:bg-slate-50"
      }`}
    >
      <div>
        <p className="font-mono text-sm font-bold text-slate-900">{item.student_ref}</p>
        <p className="mt-1 text-xs text-slate-400">Giao {formatDate(item.assigned_at)}</p>
      </div>
      <div>
        <p className="text-sm font-medium text-slate-700">{factorLabel}</p>
        <p className="mt-1 text-xs text-slate-400">{item.coverage.n_valid_terms} kỳ · {item.coverage.n_courses} học phần</p>
      </div>
      <div className="flex items-center justify-between gap-3 sm:justify-end">
        <CaseStateBadge state={item.case_state} />
        <span aria-hidden className="text-slate-300">›</span>
      </div>
    </button>
  );
}

function CasePanel({
  item,
  monitorDate,
  onMonitorDateChange,
  onAction,
}: {
  item: AdvisorDemoCase;
  monitorDate: string;
  onMonitorDateChange: (value: string) => void;
  onAction: (action: AdvisorDemoAction) => void;
}) {
  const actions = allowedAdvisorDemoActions(item.case_state);
  const limitations = resolveLimitations(item.limitations);
  const factor = item.contributing_factors[0];
  const factorLabel = factor ? FACTOR_LABEL[factor.code] ?? factor.code : "Không có lý do bàn giao";

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
                <ActionButton label="Xác nhận tiếp nhận" help="Chuyển case sang Đang hỗ trợ." onClick={() => onAction("accept")} primary />
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
