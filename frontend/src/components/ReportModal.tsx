"use client";

import { useEffect, useMemo } from "react";
import { createPortal } from "react-dom";
import { BandBadge, CaseStateBadge } from "@/components/badges";
import { LimitationsList } from "@/components/LimitationsList";
import { FACTOR_LABEL } from "@/lib/factors";
import type { ReviewCase } from "@/lib/types";

/**
 * Tool 1 của EduSignal AI (plan.md §3.2) — "Báo cáo tổng thể" cho Ban quản lý.
 * Toàn bộ số liệu từ GET /review-cases (public allowlist H11a): student_ref
 * pseudonym + band + state + factor + limitations — KHÔNG score/PII/advisor_ref.
 * "Mới" = case_state new_signal, đánh dấu bằng chữ + icon (không chỉ màu).
 * In / Lưu PDF = window.print() + @media print trong globals.css — không có
 * endpoint export/CSV (doc 11 option C bị loại vì rủi ro join PII ngoài hệ thống).
 */

const BAND_RANK: Record<string, number> = { uu_tien_som: 0, can_ra_soat: 1 };

function bandRank(c: ReviewCase): number {
  return c.review_priority_band ? (BAND_RANK[c.review_priority_band] ?? 2) : 2;
}

/** "18:13 • 18/07/2026" từ ISO — cùng cách format với topbar AppShell. */
function formatSnapshot(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  const time = d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
  return `${time} • ${d.toLocaleDateString("vi-VN")}`;
}

export function ReportModal({
  items,
  onClose,
  onOpenCase,
}: {
  items: ReviewCase[];
  onClose: () => void;
  onOpenCase: (caseId: string) => void;
}) {
  // Diện theo dõi = mọi case trừ dismissed; resolved tách nhóm "đã hoàn tất".
  // Sắp xếp: band ưu tiên trước, trong band thì tín hiệu mới lên đầu.
  const watched = useMemo(
    () =>
      items
        .filter((c) => c.case_state !== "dismissed" && c.case_state !== "resolved")
        .sort(
          (a, b) =>
            bandRank(a) - bandRank(b) ||
            Number(b.case_state === "new_signal") - Number(a.case_state === "new_signal") ||
            a.student_ref.localeCompare(b.student_ref),
        ),
    [items],
  );
  const resolved = useMemo(() => items.filter((c) => c.case_state === "resolved"), [items]);

  const newCount = watched.filter((c) => c.case_state === "new_signal").length;
  const earlyCount = watched.filter((c) => c.review_priority_band === "uu_tien_som").length;
  const studentCount = new Set(watched.map((c) => c.student_ref)).size;
  const latest = useMemo(
    () => (items.length > 0 ? items.reduce((m, c) => (c.calculated_at > m.calculated_at ? c : m)) : null),
    [items],
  );

  // Esc để đóng + khóa scroll nền khi modal mở.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [onClose]);

  // Portal ra document.body để @media print có thể ẩn phần app còn lại (globals.css).
  return createPortal(
    <div
      className="ss-report-overlay fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-sm p-4 md:p-10"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Báo cáo tổng thể: Sinh viên trong diện cần theo dõi"
        className="ss-report-sheet mx-auto max-w-5xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Thanh hành động — ẩn khi in */}
        <div className="ss-print-hide flex items-center justify-between gap-3 px-6 py-3.5 border-b border-slate-100 bg-slate-50/70">
          <p className="text-sm font-semibold text-slate-700">Xem trước báo cáo</p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-2 bg-[#dc2626] hover:bg-[#b91c1c] text-white text-sm font-semibold rounded-lg px-4 py-2 shadow-sm shadow-red-600/25 transition-colors"
            >
              <PrinterIcon />
              In / Lưu PDF
            </button>
            <button
              onClick={onClose}
              aria-label="Đóng báo cáo"
              className="inline-flex items-center justify-center w-9 h-9 rounded-lg border border-slate-200 bg-white text-slate-500 hover:text-slate-700 hover:border-slate-300 transition-colors"
            >
              <CloseIcon />
            </button>
          </div>
        </div>

        <div className="px-6 md:px-8 py-6 space-y-5">
          {/* Header báo cáo */}
          <header className="flex items-start justify-between gap-4 flex-wrap border-b border-slate-100 pb-5">
            <div className="min-w-0">
              <p className="text-[11px] font-bold tracking-widest text-[#dc2626] uppercase">
                EduSignal · Silent Shield
              </p>
              <h2 className="text-xl md:text-2xl font-bold text-slate-800 mt-1">
                Báo cáo tổng thể: Sinh viên trong diện cần theo dõi
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                Hệ thống chỉ gợi ý mức ưu tiên rà soát. Mọi quyết định do con người thực hiện.
              </p>
            </div>
            {latest && (
              <dl className="shrink-0 text-xs text-slate-500 space-y-1 bg-slate-50 border border-slate-100 rounded-xl px-4 py-3">
                <div className="flex gap-2">
                  <dt className="font-semibold text-slate-600">Cập nhật:</dt>
                  <dd className="tabular-nums">{formatSnapshot(latest.calculated_at)}</dd>
                </div>
                <div className="flex gap-2">
                  <dt className="font-semibold text-slate-600">Bộ dữ liệu:</dt>
                  <dd>{latest.dataset_version}</dd>
                </div>
                <div className="flex gap-2">
                  <dt className="font-semibold text-slate-600">Phiên bản phân tích:</dt>
                  <dd>{latest.model_version}</dd>
                </div>
              </dl>
            )}
          </header>

          {/* Tổng hợp — mọi số tính từ response */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <SummaryStat label="Sinh viên theo dõi" value={studentCount} />
            <SummaryStat label="Case trong diện" value={watched.length} />
            <SummaryStat label="Phát hiện mới" value={newCount} />
            <SummaryStat label="Ưu tiên sớm" value={earlyCount} />
          </div>

          {/* Danh sách */}
          {watched.length === 0 ? (
            <p className="text-sm text-slate-500 bg-slate-50 border border-slate-200 rounded-xl p-4">
              Chưa có sinh viên trong diện theo dõi ở kỳ dữ liệu này.
            </p>
          ) : (
            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="w-full text-left border-collapse min-w-[780px]">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <Th>#</Th>
                    <Th>Mã SV</Th>
                    <Th>Phát hiện</Th>
                    <Th>Mức ưu tiên rà soát</Th>
                    <Th>Trạng thái case</Th>
                    <Th>Yếu tố đóng góp</Th>
                    <Th>Giới hạn dữ liệu</Th>
                  </tr>
                </thead>
                <tbody>
                  {watched.map((c, i) => (
                    <tr
                      key={c.case_id}
                      onClick={() => onOpenCase(c.case_id)}
                      title="Mở chi tiết case"
                      className="border-b border-slate-100 last:border-0 cursor-pointer hover:bg-slate-50/70 transition-colors"
                    >
                      <td className="p-3 text-xs text-slate-400 tabular-nums">{i + 1}</td>
                      <td className="p-3 text-sm font-medium text-[#dc2626]">{c.student_ref}</td>
                      <td className="p-3">
                        {c.case_state === "new_signal" ? (
                          <NewBadge />
                        ) : (
                          <span className="text-xs text-slate-300" aria-hidden>
                            —
                          </span>
                        )}
                      </td>
                      <td className="p-3">
                        <BandBadge band={c.review_priority_band} />
                      </td>
                      <td className="p-3">
                        <CaseStateBadge state={c.case_state} />
                      </td>
                      <td className="p-3 text-sm text-slate-500">
                        {c.contributing_factors.map((f) => FACTOR_LABEL[f.code] ?? f.code).join(", ") || "—"}
                      </td>
                      <td className="p-3 max-w-[260px]">
                        <LimitationsList limitations={c.limitations} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Đã hoàn tất vòng hỗ trợ — tách riêng, không tính vào diện theo dõi */}
          {resolved.length > 0 && (
            <div className="text-sm text-slate-500 bg-slate-50 border border-slate-200 rounded-xl p-4">
              <p className="font-semibold text-slate-600">Đã hoàn tất vòng hỗ trợ ({resolved.length})</p>
              <p className="mt-1 text-xs">{resolved.map((c) => c.student_ref).join(" · ")}</p>
            </div>
          )}

          {/* Phạm vi & cam kết — bắt buộc theo plan.md §3.2 / RULES */}
          <footer className="border-t border-slate-100 pt-4 space-y-1.5 text-[11.5px] text-slate-400 leading-relaxed">
            <p>
              Danh sách gồm sinh viên có tín hiệu từ nguồn dữ liệu đã duyệt, không phải danh sách toàn bộ sinh viên của trường.
              Những case đã loại không được đưa vào báo cáo.
            </p>
            <p>
              Mã SV là mã định danh được bảo vệ; báo cáo không chứa điểm số nội bộ của mô hình hay thông tin cá nhân.
              &ldquo;Mới&rdquo; = tín hiệu ở trạng thái Tín hiệu mới trong kỳ dữ liệu này.
            </p>
          </footer>
        </div>
      </div>
    </div>,
    document.body,
  );
}

/* ---------- Mảnh UI nhỏ dùng riêng cho báo cáo ---------- */

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="p-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">
      {children}
    </th>
  );
}

function SummaryStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl px-4 py-3">
      <p className="text-2xl font-bold text-slate-800 tabular-nums">{value}</p>
      <p className="text-xs text-slate-400 mt-0.5">{label}</p>
    </div>
  );
}

/** Badge "Mới" — chữ + icon, không dùng màu làm tín hiệu duy nhất (RULES §3). */
function NewBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 border border-amber-200 text-amber-700 text-[11px] font-bold px-2 py-0.5 whitespace-nowrap">
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d="M12 3l1.9 5.8a2 2 0 001.3 1.3L21 12l-5.8 1.9a2 2 0 00-1.3 1.3L12 21l-1.9-5.8a2 2 0 00-1.3-1.3L3 12l5.8-1.9a2 2 0 001.3-1.3L12 3z" />
      </svg>
      Mới
    </span>
  );
}

function PrinterIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M6 9V2h12v7" />
      <path d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2" />
      <path d="M6 14h12v8H6z" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M18 6L6 18M6 6l12 12" />
    </svg>
  );
}
