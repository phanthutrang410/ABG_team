"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CaseStateBadge } from "@/components/badges";
import { QueuePagination } from "@/components/QueuePagination";
import { useSetTopbarInfo } from "@/components/AppShell";
import {
  ActionButton,
  BellIcon,
  DataPoint,
  FILTERS,
  Hero,
  STAT_CARDS,
  StatCard,
  defaultMonitorDate,
  formatDateTime,
  type Filter,
} from "@/components/advisor-shared";
import { HANDOFF_ACK_OVERDUE_DAYS, paginateAdvisorQueue } from "@/lib/advisor-demo";
import {
  fetchCaseWorkflow,
  fetchReviewCase,
  fetchReviewCases,
  postCaseTransition,
  postCaseViewed,
} from "@/lib/api";
import { FACTOR_LABEL } from "@/lib/factors";
import { resolveLimitations } from "@/lib/limitations";
import type {
  CaseAction,
  CaseListResponse,
  CaseState,
  ReviewCase,
  TransitionResponse,
} from "@/lib/types";

type ServerAction = Extract<CaseAction, "accept" | "monitor" | "resolve">;

/** GVCN care actions permitted per Process §4 state (mirror backend GVCN_ACTIONS). */
function allowedServerActions(state: CaseState): ServerAction[] {
  if (state === "assigned") return ["accept"];
  if (state === "follow_up_in_progress") return ["monitor", "resolve"];
  if (state === "monitoring") return ["resolve"];
  return [];
}

function elapsedDaysSince(iso: string | null, now: Date): number {
  if (!iso) return 0;
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return 0;
  return Math.max(0, Math.floor((now.getTime() - then) / 86_400_000));
}

/**
 * Real-data GVCN case queue (H36 scoped). The list comes from GET /review-cases
 * (backend filters to the advisor's own cases); the "đã xem" receipt and the
 * authoritative workflow state come from GET /cases/{id}. No localStorage, no
 * client-side scoping, no fabricated band — fail-closed on every transport error.
 */
export function AdvisorServerWorkspace() {
  // null = loading; otherwise the fetched (possibly error/empty) envelope.
  const [list, setList] = useState<CaseListResponse | null>(null);
  const [detailById, setDetailById] = useState<Record<string, ReviewCase | null>>({});
  const [workflowById, setWorkflowById] = useState<Record<string, TransitionResponse>>({});
  // Case ids whose GET /cases/{id} failed (403/404/transport) — panel fails closed.
  const [workflowFailed, setWorkflowFailed] = useState<Record<string, true>>({});
  const [openingId, setOpeningId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [monitorDate, setMonitorDate] = useState(defaultMonitorDate());
  const [notice, setNotice] = useState<string | null>(null);
  const [actionPending, setActionPending] = useState(false);
  // Stable "now" for one render so overdue math doesn't flicker.
  const [now] = useState(() => new Date());

  useEffect(() => {
    const controller = new AbortController();
    fetchReviewCases(controller.signal).then((res) => {
      if (!controller.signal.aborted) setList(res);
    });
    return () => controller.abort();
  }, []);

  const cases = useMemo(() => list?.items ?? [], [list]);

  // Open a case: load neutral detail + authoritative workflow, then log "đã xem"
  // once (idempotent) when the advisor genuinely opens an unseen case.
  const openCase = useCallback(async (caseId: string) => {
    setSelectedId(caseId);
    setOpeningId(caseId);
    const [detail, workflow] = await Promise.all([
      fetchReviewCase(caseId),
      fetchCaseWorkflow(caseId),
    ]);
    setDetailById((prev) => ({ ...prev, [caseId]: detail.case }));

    let resolved = workflow;
    if (resolved && !resolved.viewed_at) {
      const marked = await postCaseViewed(caseId);
      if (marked) resolved = marked;
    }
    if (resolved) {
      setWorkflowById((prev) => ({ ...prev, [caseId]: resolved! }));
    } else {
      setWorkflowFailed((prev) => ({ ...prev, [caseId]: true }));
    }
    setOpeningId((current) => (current === caseId ? null : current));
  }, []);

  // Deep-link from the handoff email: /advisor?case=<real_id>. Login is enforced
  // by AppShell; this is "event-driven login", not a daily dashboard visit.
  useEffect(() => {
    const target = new URLSearchParams(window.location.search).get("case");
    if (target) void openCase(target);
  }, [openCase]);

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
    () => cases.reduce((latest, item) => (item.calculated_at > latest ? item.calculated_at : latest), ""),
    [cases],
  );
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
        return right.calculated_at.localeCompare(left.calculated_at);
      });
  }, [cases, filter, search]);

  useEffect(() => {
    setPage(1);
  }, [filter, search]);

  const pageInfo = paginateAdvisorQueue(visibleCases, page);

  const selectedCase =
    (selectedId ? detailById[selectedId] : null) ??
    cases.find((item) => item.case_id === selectedId) ??
    null;
  const selectedWorkflow = selectedId ? workflowById[selectedId] ?? null : null;

  async function runAction(action: ServerAction) {
    if (!selectedId || actionPending) return;
    if (action === "monitor" && !monitorDate) {
      setNotice("Hãy chọn thời hạn theo dõi trước.");
      return;
    }
    setActionPending(true);
    const payload =
      action === "monitor"
        ? { action, monitoring_until: new Date(`${monitorDate}T00:00:00Z`).toISOString() }
        : { action };
    const result = await postCaseTransition(selectedId, payload);
    setActionPending(false);

    if (!result.ok) {
      setNotice(
        result.error?.code === "forbidden_transition"
          ? "Thao tác không hợp lệ ở trạng thái hiện tại."
          : "Không thực hiện được thao tác. Vui lòng thử lại.",
      );
      return;
    }

    const updated = result.data;
    setWorkflowById((prev) => ({ ...prev, [selectedId]: updated }));
    // Reflect the new workflow state in the queue so grouping/counts update
    // without refetching the whole list.
    setList((prev) =>
      prev
        ? {
            ...prev,
            items: prev.items.map((item) =>
              item.case_id === selectedId ? { ...item, case_state: updated.state } : item,
            ),
          }
        : prev,
    );
    setNotice(actionNotice(action));
  }

  if (list === null) {
    return (
      <div id="cases" className="scroll-mt-5 rounded-2xl border border-slate-200 bg-white px-6 py-12 text-center text-sm text-slate-400 shadow-sm">
        Đang tải hàng đợi case…
      </div>
    );
  }

  if (list.state === "error") {
    return (
      <div
        id="cases"
        role="status"
        data-advisor-state="error"
        className="scroll-mt-5 rounded-2xl border border-amber-200 bg-amber-50 px-6 py-12 text-center shadow-sm"
      >
        <p className="text-sm font-semibold text-amber-900">Không tải được hàng đợi case</p>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-amber-800">
          Máy chủ tạm thời không phản hồi. Hệ thống không hiển thị danh sách phỏng đoán — vui lòng thử lại sau.
        </p>
      </div>
    );
  }

  return (
    <div id="cases" className="scroll-mt-5 space-y-5">
      {notice && (
        <div role="status" className="flex items-center justify-between rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <span>✓ {notice}</span>
          <button type="button" onClick={() => setNotice(null)} className="font-semibold text-emerald-700">Đóng</button>
        </div>
      )}

      {list.state === "stale" && (
        <div role="status" className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Dữ liệu có thể đã cũ so với đợt trích xuất gần nhất. Trạng thái xử lý vẫn phản ánh thao tác thực tế.
        </div>
      )}

      {counts.needs_action > 0 && (
        <div role="status" className="flex items-start gap-3 rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900">
          <span aria-hidden className="mt-0.5 flex-shrink-0 text-sky-500"><BellIcon /></span>
          <p className="leading-5">
            Có <strong>{counts.needs_action}</strong> case khoa vừa bàn giao, đang chờ Thầy/Cô <strong>xác nhận tiếp nhận</strong>.
            Mở từng case để xem chi tiết bảo mật rồi bấm “Xác nhận tiếp nhận” để đóng vòng bàn giao.
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
            {cases.length === 0 ? (
              <div className="px-6 py-14 text-center text-sm text-slate-500">
                Hiện chưa có case nào được bàn giao cho bạn.
              </div>
            ) : pageInfo.pageItems.length === 0 ? (
              <div className="px-6 py-14 text-center text-sm text-slate-500">
                Không có case nào khớp bộ lọc. Thử đổi trạng thái hoặc xóa từ khóa tìm kiếm.
              </div>
            ) : (
              pageInfo.pageItems.map((item) => (
                <CaseRow
                  key={item.case_id}
                  item={item}
                  selected={item.case_id === selectedId}
                  onSelect={() => void openCase(item.case_id)}
                />
              ))
            )}
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
          {selectedId ? (
            <CasePanel
              caseData={selectedCase}
              workflow={selectedWorkflow}
              workflowFailed={Boolean(workflowFailed[selectedId])}
              loading={openingId === selectedId}
              now={now}
              monitorDate={monitorDate}
              onMonitorDateChange={setMonitorDate}
              onAction={runAction}
              actionPending={actionPending}
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

function CaseRow({ item, selected, onSelect }: { item: ReviewCase; selected: boolean; onSelect: () => void }) {
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
        <p className="mt-1 text-xs text-slate-400">Mở để xem trạng thái tiếp nhận</p>
      </div>
      <div>
        <p className="text-sm font-medium text-slate-700">{factorLabel}</p>
        <p className="mt-1 text-xs text-slate-400">{item.coverage.n_valid_terms} kỳ · {item.coverage.n_courses} học phần</p>
      </div>
      <div className="flex items-center justify-end gap-3">
        <CaseStateBadge state={item.case_state} />
        <span aria-hidden className="text-slate-300">›</span>
      </div>
    </button>
  );
}

function CasePanel({
  caseData,
  workflow,
  workflowFailed,
  loading,
  now,
  monitorDate,
  onMonitorDateChange,
  onAction,
  actionPending,
}: {
  caseData: ReviewCase | null;
  workflow: TransitionResponse | null;
  workflowFailed: boolean;
  loading: boolean;
  now: Date;
  monitorDate: string;
  onMonitorDateChange: (value: string) => void;
  onAction: (action: ServerAction) => void;
  actionPending: boolean;
}) {
  if (loading && !caseData) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-400 shadow-sm">
        Đang mở case…
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-8 text-center text-sm text-amber-800 shadow-sm">
        Không mở được case này. Có thể case không thuộc phạm vi của bạn hoặc máy chủ tạm thời không phản hồi.
      </div>
    );
  }

  // Workflow is authoritative for state/actions; fall back to the list value only
  // for display when the workflow surface is unavailable.
  const state = workflow?.state ?? caseData.case_state;
  const actions = allowedServerActions(state);
  const limitations = resolveLimitations(caseData.limitations);
  const factor = caseData.contributing_factors[0];
  const factorLabel = factor ? FACTOR_LABEL[factor.code] ?? factor.code : "Không có lý do bàn giao";
  const awaitingAccept = state === "assigned";
  const elapsedDays = elapsedDaysSince(workflow?.updated_at ?? null, now);
  const overdue = awaitingAccept && elapsedDays >= HANDOFF_ACK_OVERDUE_DAYS;

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Chi tiết bàn giao</p>
            <h3 className="mt-1 font-mono text-lg font-bold text-slate-900">{caseData.student_ref}</h3>
          </div>
          <CaseStateBadge state={state} />
        </div>
        {workflow?.updated_at && (
          <p className="mt-3 text-xs leading-5 text-slate-500">
            Case pseudonymous · cập nhật {formatDateTime(workflow.updated_at)}
          </p>
        )}
      </div>

      <div className="space-y-5 p-5">
        <div className="flex items-center justify-between gap-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-xs">
          <span className="text-slate-500">Trạng thái xem</span>
          {workflowFailed ? (
            <span className="font-semibold text-slate-500">Chưa lấy được lượt xem</span>
          ) : workflow?.viewed_at ? (
            <span className="font-semibold text-emerald-700">Đã xem · {formatDateTime(workflow.viewed_at)}</span>
          ) : (
            <span className="font-semibold text-slate-500">Chưa ghi nhận lượt xem</span>
          )}
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
            <DataPoint label="Học kỳ hợp lệ" value={String(caseData.coverage.n_valid_terms)} />
            <DataPoint label="Học phần" value={String(caseData.coverage.n_courses)} />
          </dl>
          <ul className="mt-2 space-y-1 text-xs leading-5 text-slate-500">
            {limitations.map((limitation) => <li key={limitation.text}>• {limitation.text}</li>)}
          </ul>
        </section>

        {workflow?.monitoring_until && (
          <div className="rounded-lg border border-sky-200 bg-sky-50 px-3 py-2 text-xs text-sky-800">
            Theo dõi đến {formatDateTime(workflow.monitoring_until)}.
          </div>
        )}

        <section className="border-t border-slate-100 pt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Bước tiếp theo</p>
          {workflowFailed ? (
            <p className="mt-2 text-sm text-slate-500">
              Không lấy được trạng thái xử lý nên tạm ẩn thao tác. Vui lòng mở lại case sau.
            </p>
          ) : actions.length === 0 ? (
            <p className="mt-2 text-sm text-slate-500">
              Vòng hỗ trợ hiện tại đã hoàn tất. Không có thao tác bổ sung trên case này.
            </p>
          ) : (
            <div className="mt-3 space-y-3">
              {actions.includes("accept") && (
                <ActionButton
                  label="Xác nhận tiếp nhận"
                  help="Bước xác nhận rõ ràng — mở/đọc chưa tính là tiếp nhận. Chuyển case sang Đang hỗ trợ và báo khoa đã tiếp nhận."
                  onClick={() => onAction("accept")}
                  primary
                  disabled={actionPending}
                />
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
                  <button
                    type="button"
                    onClick={() => onAction("monitor")}
                    disabled={actionPending}
                    className="mt-2 w-full rounded-lg border border-sky-300 bg-sky-50 px-3 py-2 text-sm font-semibold text-sky-800 hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Chuyển sang theo dõi
                  </button>
                </div>
              )}
              {actions.includes("resolve") && (
                <ActionButton
                  label="Hoàn tất vòng hỗ trợ"
                  help="Đóng vòng hiện tại; không gắn nhãn cố định cho sinh viên."
                  onClick={() => onAction("resolve")}
                  disabled={actionPending}
                />
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

function actionNotice(action: ServerAction): string {
  if (action === "accept") return "Đã xác nhận tiếp nhận case và báo khoa.";
  if (action === "monitor") return "Đã chuyển case sang theo dõi có thời hạn.";
  return "Đã hoàn tất vòng hỗ trợ.";
}
