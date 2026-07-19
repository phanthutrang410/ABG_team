"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useId, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AgentPanel } from "@/components/AgentPanel";
import { AppShell } from "@/components/AppShell";
import { BandBadge, CaseStateBadge } from "@/components/badges";
import { CareActions } from "@/components/CareActions";
import { LimitationsList } from "@/components/LimitationsList";
import { fetchReviewCase } from "@/lib/api";
import { useSession } from "@/lib/session";
import type { CaseDetailResponse, CaseState } from "@/lib/types";

/**
 * Deep-link dự phòng cho case. Luồng chính từ danh sách dùng CaseDetailDialog
 * bên dưới để người review không mất bộ lọc/vị trí đang xem.
 */
export default function CaseDetailPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const { activeRole, ready } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (ready && activeRole === "gvcn") router.replace("/advisor#cases");
  }, [activeRole, ready, router]);

  if (activeRole === "gvcn") {
    return (
      <AppShell
        role="gvcn"
        title="Case được bàn giao cho tôi"
        subtitle="Chi tiết case của cố vấn được mở trong workspace đã scope theo vai."
      >
        <div className="rounded-2xl border border-slate-200 bg-white p-6 text-slate-500">
          Đang trở về danh sách case được giao…
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell role="ban_quan_ly" title="Chi tiết case">
      <div className="mx-auto max-w-[1280px]">
        <div className="mb-4 flex items-center justify-between gap-3">
          <Link href="/analysis?tab=signals" className="text-sm font-semibold text-red-600 hover:text-red-700">
            ← Danh sách rà soát
          </Link>
        </div>
        <PrivacyNotice />
        <CaseDetailPanel caseId={caseId} />
      </div>
    </AppShell>
  );
}

export function CaseDetailDialog({
  caseId,
  onClose,
  onCaseStateChange,
}: {
  caseId: string;
  onClose: () => void;
  onCaseStateChange?: (caseId: string, next: CaseState) => void;
}) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
      previouslyFocused?.focus();
    };
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/45 p-3 backdrop-blur-[2px] md:p-6"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="flex max-h-[94vh] w-full max-w-[1320px] flex-col overflow-hidden rounded-3xl border border-red-100 bg-[#f8f9fb] shadow-2xl"
      >
        <header className="flex shrink-0 items-center justify-between border-b border-slate-200 bg-white px-5 py-4 md:px-7">
          <div className="flex min-w-0 items-center gap-3">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-red-50 text-red-600 shadow-sm ring-1 ring-red-100" aria-hidden>
              <CaseIcon />
            </span>
            <div className="min-w-0">
              <p className="m-0 text-xs text-slate-400">Ban quản lý học tập</p>
              <h2 id={titleId} className="m-0 truncate text-xl font-bold text-slate-900">Chi tiết case</h2>
            </div>
          </div>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            aria-label="Đóng chi tiết case"
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-2xl leading-none text-slate-500 transition hover:border-red-200 hover:bg-red-50 hover:text-red-600"
          >
            ×
          </button>
        </header>

        <div className="overflow-y-auto p-4 md:p-6">
          <PrivacyNotice />
          <CaseDetailPanel caseId={caseId} onCaseStateChange={onCaseStateChange} />
        </div>
      </section>
    </div>
  );
}

function PrivacyNotice() {
  return (
    <div className="mb-4 flex items-start gap-3 rounded-xl border border-red-100 bg-gradient-to-r from-red-50 to-white px-4 py-3 text-sm text-slate-600 shadow-sm">
      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-red-300 text-xs font-bold text-red-600" aria-hidden>i</span>
      <p className="m-0">
        Dữ liệu định danh giả và mức ưu tiên rà soát; con người phê duyệt trước mọi bàn giao.
      </p>
    </div>
  );
}

export function CaseDetailPanel({
  caseId,
  onCaseStateChange,
}: {
  caseId: string;
  onCaseStateChange?: (caseId: string, next: CaseState) => void;
}) {
  const [loading, setLoading] = useState(true);
  const [response, setResponse] = useState<CaseDetailResponse | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    const controller = new AbortController();
    fetchReviewCase(caseId, controller.signal).then((next) => {
      setResponse(next);
      setLoading(false);
    });
    return controller;
  }, [caseId]);

  useEffect(() => {
    const controller = load();
    return () => controller.abort();
  }, [load]);

  const handleStateChange = useCallback((next: CaseState) => {
    setResponse((previous) =>
      previous?.case
        ? { ...previous, case: { ...previous.case, case_state: next } }
        : previous,
    );
    onCaseStateChange?.(caseId, next);
  }, [caseId, onCaseStateChange]);

  return (
    <div>
      <div className="mb-3 flex justify-end">
        <button
          type="button"
          onClick={() => load()}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-600 shadow-sm transition hover:border-red-200 hover:text-red-600"
        >
          ↻ Tải lại
        </button>
      </div>
      {loading ? (
        <DetailSkeleton />
      ) : response ? (
        <CaseDetailBody response={response} onStateChange={handleStateChange} />
      ) : null}
    </div>
  );
}

function CaseDetailBody({
  response,
  onStateChange,
}: {
  response: CaseDetailResponse;
  onStateChange: (next: CaseState) => void;
}) {
  if (response.state === "error") {
    return <Notice tone="error">Không tải được case này. Máy chủ tạm thời không phản hồi, vui lòng bấm “Tải lại”.</Notice>;
  }
  if (response.state === "empty") {
    return <Notice tone="info">Không tìm thấy case trong phạm vi được xem.</Notice>;
  }
  if (!response.case) return null;

  const c = response.case;
  const insufficient = c.data_state === "insufficient_data";

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-center gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-red-50 text-xl font-bold text-red-600 ring-1 ring-red-100" aria-hidden>SV</div>
        <div className="min-w-[220px] flex-1">
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="m-0 text-2xl font-bold text-slate-900">{c.student_ref}</h1>
            <CopyButton text={c.student_ref} />
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Mã định danh được bảo vệ · cập nhật {formatCalculatedAt(c.calculated_at)} · phiên bản {c.model_version}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <CaseStateBadge state={c.case_state} />
          <BandBadge band={c.review_priority_band} />
        </div>
      </header>

      {response.state === "stale" && <Notice tone="warning">Dữ liệu có thể đã cũ vì chưa được cập nhật gần đây.</Notice>}
      {response.state === "insufficient_data" && <Notice tone="warning">Chưa đủ dữ liệu để tạo mức ưu tiên rà soát cho case này.</Notice>}

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <SectionTitle>TIẾN TRÌNH RÀ SOÁT</SectionTitle>
        <StateStepper state={c.case_state} />
      </section>

      <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
        <div className="grid gap-4">
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <SectionTitle>YẾU TỐ ĐÓNG GÓP</SectionTitle>
            {c.contributing_factors.length === 0 ? (
              <p className="m-0 text-sm italic text-slate-500">Không có yếu tố khi thiếu dữ liệu.</p>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {c.contributing_factors.map((factor) => (
                  <div key={factor.code} className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5">
                    <div className="text-sm font-semibold text-slate-700">{factorLabel(factor.code)}</div>
                    <div className="mt-1 break-words text-xs text-slate-400">
                      <code>{factor.code}</code>
                      {factor.evidence_refs.length > 0 && <> · {factor.evidence_refs.join(", ")}</>}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <p className="mb-0 mt-3 text-xs text-slate-400">
              Độ phủ: {c.coverage.n_valid_terms} học kỳ · {c.coverage.n_courses} học phần · kỳ gần nhất {c.coverage.last_term_code ?? "—"}
            </p>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <SectionTitle>GIỚI HẠN DỮ LIỆU</SectionTitle>
            <LimitationsList limitations={c.limitations} />
          </section>
        </div>

        <div className="grid gap-4">
          {insufficient ? (
            <aside className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <SectionTitle>THAO TÁC</SectionTitle>
              <p className="m-0 text-sm italic text-slate-500">
                Không đủ dữ liệu để tạo mức ưu tiên. Hệ thống chưa đề xuất hành động rà soát cho case này.
              </p>
            </aside>
          ) : (
            <CareActions caseId={c.case_id} caseState={c.case_state} onStateChange={onStateChange} />
          )}
          <AgentPanel caseId={c.case_id} />
        </div>
      </div>
    </div>
  );
}

const MAIN_PIPELINE: CaseState[] = [
  "new_signal",
  "pending_review",
  "approved_for_follow_up",
  "assigned",
  "follow_up_in_progress",
];

const PIPELINE_LABEL: Record<CaseState, string> = {
  new_signal: "Tín hiệu mới",
  pending_review: "Chờ duyệt",
  approved_for_follow_up: "Đã duyệt",
  dismissed: "Đã loại",
  assigned: "Đã bàn giao",
  follow_up_in_progress: "Đang hỗ trợ",
  resolved: "Đã kết thúc",
  monitoring: "Đang theo dõi",
};

function StateStepper({ state }: { state: CaseState }) {
  const steps = state === "dismissed"
    ? (["new_signal", "pending_review", "dismissed"] as CaseState[])
    : state === "resolved"
      ? ([...MAIN_PIPELINE, "resolved"] as CaseState[])
      : state === "monitoring"
        ? ([...MAIN_PIPELINE, "monitoring"] as CaseState[])
        : MAIN_PIPELINE;
  const currentIndex = Math.max(0, steps.indexOf(state));

  return (
    <div className="overflow-x-auto pb-1">
      <ol
        aria-label="Tiến trình rà soát"
        data-orientation="horizontal"
        className="m-0 flex min-w-[720px] list-none p-0"
      >
        {steps.map((step, index) => {
          const done = index < currentIndex;
          const current = index === currentIndex;
          return (
            <li key={step} className="min-w-[130px] flex-1" aria-current={current ? "step" : undefined}>
              <div className="flex items-center">
                <span
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold ${
                    done
                      ? "border-red-600 bg-red-600 text-white"
                      : current
                        ? "border-red-600 bg-white text-red-600 ring-4 ring-red-50"
                        : "border-slate-300 bg-white text-slate-400"
                  }`}
                  aria-hidden
                >
                  {done ? "✓" : current ? "●" : index + 1}
                </span>
                {index < steps.length - 1 && (
                  <span className={`h-0.5 flex-1 ${done ? "bg-red-600" : "bg-slate-200"}`} aria-hidden />
                )}
              </div>
              <div className="mt-2 pr-3">
                <p className={`m-0 text-sm ${done || current ? "font-semibold text-slate-800" : "font-medium text-slate-400"}`}>
                  {PIPELINE_LABEL[step]}
                </p>
                {current && <span className="mt-1 inline-flex rounded-full bg-red-50 px-2 py-0.5 text-[11px] font-semibold text-red-600">Hiện tại</span>}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

const FACTOR_LABEL: Record<string, string> = {
  grade_trend_declining: "Điểm trung bình giữa hai kỳ giảm",
  gpa_below_target: "GPA kỳ gần nhất dưới mức tham chiếu",
  latest_term_gpa: "Kết quả kỳ gần nhất",
  failed_credits_elevated: "Tín chỉ môn không đạt ở mức cao",
  grade_volatility_elevated: "Độ phân tán điểm học phần cao",
  attendance_rate_below_target: "Tỷ lệ điểm danh thấp",
  attendance_trend_declining: "Chuyên cần giảm dần",
};

function factorLabel(code: string): string {
  return FACTOR_LABEL[code] ?? code;
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 className="mb-3 mt-0 text-sm font-bold tracking-wide text-slate-600">{children}</h2>;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      title="Sao chép mã"
      aria-label="Sao chép mã sinh viên"
      onClick={() => {
        navigator.clipboard?.writeText(text).then(() => {
          setCopied(true);
          window.setTimeout(() => setCopied(false), 1500);
        });
      }}
      className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-500 transition hover:border-red-200 hover:text-red-600"
    >
      {copied ? "✓ Đã chép" : "⧉"}
    </button>
  );
}

function Notice({ tone, children }: { tone: "info" | "warning" | "error"; children: React.ReactNode }) {
  const toneClass = tone === "error"
    ? "border-red-200 bg-red-50 text-red-700"
    : tone === "warning"
      ? "border-amber-200 bg-amber-50 text-amber-700"
      : "border-slate-200 bg-slate-50 text-slate-600";
  return <div className={`my-3 rounded-xl border px-4 py-3 text-sm ${toneClass}`}>{children}</div>;
}

function DetailSkeleton() {
  return (
    <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm" aria-busy="true" aria-label="Đang tải case">
      {["75%", "60%", "45%"].map((width) => (
        <div key={width} className="h-4 animate-pulse rounded bg-slate-100" style={{ width }} />
      ))}
    </div>
  );
}

function formatCalculatedAt(iso: string): string {
  const value = new Date(iso);
  if (Number.isNaN(value.getTime())) return "—";
  return value.toLocaleString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function CaseIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m3 10 9-5 9 5-9 5-9-5Z" />
      <path d="M7 12.5V17c3 2 7 2 10 0v-4.5" />
    </svg>
  );
}
