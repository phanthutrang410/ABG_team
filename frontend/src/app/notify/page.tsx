"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { AIThinkingOverlay } from "@/components/AIThinkingOverlay";
import { BandBadge, CaseStateBadge } from "@/components/badges";
import { fetchAdvisorHandoffDrafts } from "@/lib/api";
import { FACTOR_LABEL } from "@/lib/factors";
import { resolveLimitations } from "@/lib/limitations";
import {
  CASE_STATE_LABEL,
  type AdvisorHandoffDraftBundle,
  type AdvisorHandoffDraftListResponse,
  type CaseState,
  type HandoffDraftCaseLine,
} from "@/lib/types";

/**
 * F6 / G06 — Trang Thông báo: "Soạn mail gợi ý cho GVCN" (plan.md §3.4, FR-12).
 * Consumer của GET /advisor-handoff-drafts (H22). Draft-only: FE render nguyên
 * văn subject/body từ API — KHÔNG tự viết/sửa lời; chỉ Copy hoặc mở mail client
 * (mailto: không recipient). KHÔNG có nút Gửi, không claim "đã gửi"; badge
 * requires_human_approval là invariant. advisor_ref chỉ dùng để nhóm/route,
 * không phải PII (H11a exception). Fail-closed như các trang khác.
 */

type ListFilter =
  | "all"
  | "approved_for_follow_up"
  | "assigned"
  | "uu_tien_som"
  | "can_ra_soat";

export default function NotifyPage() {
  return (
    <AppShell role="ban_quan_ly">
      <Body />
    </AppShell>
  );
}

function Body() {
  const [loading, setLoading] = useState(true);
  const [response, setResponse] = useState<AdvisorHandoffDraftListResponse | null>(null);
  const activeLoadRef = useRef<AbortController | null>(null);

  const load = useCallback(() => {
    activeLoadRef.current?.abort();
    setLoading(true);
    const controller = new AbortController();
    activeLoadRef.current = controller;
    fetchAdvisorHandoffDrafts(controller.signal).then((r) => {
      if (controller.signal.aborted || activeLoadRef.current !== controller) return;
      setResponse(r);
      setLoading(false);
      activeLoadRef.current = null;
    });
    return controller;
  }, []);

  useEffect(() => {
    const controller = load();
    return () => controller.abort();
  }, [load]);

  const [q, setQ] = useState("");
  const [advisor, setAdvisor] = useState("all");
  const [listFilter, setListFilter] = useState<ListFilter>("all");

  const bundles = useMemo(
    () => (response && response.state !== "error" ? response.bundles : []),
    [response],
  );

  const advisorOptions = useMemo(
    () => [...bundles]
      .map((bundle) => ({ ref: bundle.advisor_ref, name: bundle.advisor_display_name ?? bundle.advisor_ref }))
      .sort((a, b) => a.name.localeCompare(b.name, "vi")),
    [bundles],
  );

  // Lọc ở cấp BUNDLE để draft.body luôn khớp nguyên văn với danh sách do API trả.
  // Ô tìm kiếm cũng nhận factor code/nhãn, nên vẫn đáp ứng filter factor của G06.
  const visible = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return bundles.filter((b) => {
      const matchText =
        !needle ||
        b.advisor_ref.toLowerCase().includes(needle) ||
        (b.advisor_display_name ?? "").toLowerCase().includes(needle) ||
        b.cases.some(
          (c) =>
            c.student_ref.toLowerCase().includes(needle) ||
            c.contributing_factor_codes.some(
              (factor) =>
                factor.toLowerCase().includes(needle) ||
                (FACTOR_LABEL[factor] ?? "").toLowerCase().includes(needle),
            ),
        );
      const matchAdvisor = advisor === "all" || b.advisor_ref === advisor;
      const matchListFilter =
        listFilter === "all" ||
        b.cases.some(
          (c) => c.case_state === listFilter || c.review_priority_band === listFilter,
        );
      return matchText && matchAdvisor && matchListFilter;
    });
  }, [advisor, bundles, listFilter, q]);

  const totalCases = bundles.reduce((n, b) => n + b.case_count, 0);
  const repair = response && response.state !== "error"
    ? response.mapping_repair
    : { case_count: 0, cases: [], limitations: [] };
  const nothing = bundles.length === 0 && repair.case_count === 0;

  const resetAndLoad = () => {
    setQ("");
    setAdvisor("all");
    setListFilter("all");
    load();
  };

  return (
    <div className="space-y-5 pb-1">
      <AIThinkingOverlay visible={loading} />
      <header>
        <h1 className="text-[28px] font-bold tracking-tight text-slate-900">
          Soạn mail cho giảng viên phụ trách
        </h1>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-500">
          Lọc sinh viên cần theo dõi theo từng giảng viên và xem bản nháp mail bàn giao.<br className="hidden xl:block" /> Hệ thống chỉ soạn nội dung; Ban quản lý duyệt và tự gửi ngoài hệ thống.
        </p>
      </header>

      {/* Cam kết draft-only — hiển thị cố định, không phụ thuộc dữ liệu. */}
      <div className="flex min-h-[66px] items-center gap-4 rounded-xl border border-red-200 bg-red-50/40 px-5 py-4">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 border-red-500 text-red-500" aria-hidden>
          <AlertIcon />
        </span>
        <p className="text-sm leading-6 text-slate-600">
          <strong className="font-semibold text-red-600">Chỉ là bản nháp.</strong> Hệ thống không gửi mail và không lưu địa chỉ liên hệ của giảng viên/sinh viên.<br className="hidden xl:block" />
          Ban quản lý sao chép nội dung và tự gửi bằng hộp thư của mình sau khi rà soát.
        </p>
      </div>

      {/* Toolbar luôn hiện cả ở trạng thái empty/error để đúng hành vi của mockup. */}
      <div className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm xl:grid-cols-[230px_190px_minmax(260px,1fr)_116px_154px]">
        <label className="relative">
          <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500"><TeacherGroupIcon /></span>
          <select
            value={advisor}
            onChange={(event) => setAdvisor(event.target.value)}
            aria-label="Lọc theo nhóm giảng viên"
            className="h-11 w-full appearance-none rounded-lg border border-slate-200 bg-white pl-11 pr-9 text-sm text-slate-600 outline-none transition focus:border-red-300 focus:ring-2 focus:ring-red-100"
          >
            <option value="all">Nhóm giảng viên</option>
            {advisorOptions.map((o) => <option key={o.ref} value={o.ref}>{o.name}</option>)}
          </select>
          <span className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-700"><ChevronIcon /></span>
        </label>

        <label className="relative">
          <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500"><TagIcon /></span>
          <select
            value={listFilter}
            onChange={(event) => setListFilter(event.target.value as ListFilter)}
            aria-label="Lọc theo trạng thái hoặc mức ưu tiên"
            className="h-11 w-full appearance-none rounded-lg border border-slate-200 bg-white pl-11 pr-9 text-sm text-slate-600 outline-none transition focus:border-red-300 focus:ring-2 focus:ring-red-100"
          >
            <option value="all">Trạng thái</option>
            <optgroup label="Trạng thái case">
              <option value="approved_for_follow_up">Đã duyệt theo dõi</option>
              <option value="assigned">Đã bàn giao</option>
            </optgroup>
            <optgroup label="Mức ưu tiên">
              <option value="uu_tien_som">Ưu tiên sớm</option>
              <option value="can_ra_soat">Cần rà soát</option>
            </optgroup>
          </select>
          <span className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-700"><ChevronIcon /></span>
        </label>

        <label className="relative">
          <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"><SearchIcon /></span>
          <input
            value={q}
            onChange={(event) => setQ(event.target.value)}
            placeholder="Tìm theo tên/mã giảng viên"
            aria-label="Tìm theo tên hoặc mã giảng viên, mã sinh viên hoặc yếu tố đóng góp"
            className="h-11 w-full rounded-lg border border-slate-200 bg-white pl-11 pr-4 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-red-300 focus:ring-2 focus:ring-red-100"
          />
        </label>

        <button
          type="button"
          onClick={resetAndLoad}
          disabled={loading}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-lg border border-red-400 bg-white px-4 text-sm font-semibold text-red-600 transition hover:bg-red-50 disabled:cursor-wait disabled:opacity-60"
        >
          <RefreshIcon /> Làm mới
        </button>
        <button
          type="button"
          onClick={load}
          disabled={loading}
          title="Tải các bản nháp do máy chủ tạo; trình duyệt không tự sinh hoặc gửi mail"
          className="inline-flex h-11 items-center justify-center gap-2 rounded-lg bg-red-600 px-4 text-sm font-semibold text-white shadow-sm shadow-red-600/20 transition hover:bg-red-700 disabled:cursor-wait disabled:opacity-60"
        >
          <PlusIcon /> Tạo bản nháp
        </button>
      </div>

      {loading ? (
        <Skeleton />
      ) : !response || response.state === "error" ? (
        <ErrorCard onReload={load} />
      ) : response.state === "empty" || nothing ? (
        <EmptyCard />
      ) : visible.length === 0 ? (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500 shadow-sm">
          Không có giảng viên nào khớp bộ lọc. Hãy xóa từ khóa hoặc chọn lại trạng thái.
        </div>
      ) : (
        <div className="space-y-5">
          <p className="px-1 text-xs text-slate-400">
            {visible.length}/{bundles.length} giảng viên · {totalCases} case đã duyệt
          </p>
          {visible.map((bundle) => <BundleCard key={bundle.advisor_ref} bundle={bundle} />)}
        </div>
      )}

      {/* Case đã duyệt nhưng thiếu mapping GVCN — không thể soạn mail (Process §4.4) */}
      {repair.case_count > 0 && <MappingRepairCard bucket={repair} />}

      <div className="flex items-start gap-4 rounded-xl border border-slate-200 bg-slate-50/70 px-5 py-4 text-xs leading-5 text-slate-400">
        <span className="mt-0.5 shrink-0 text-slate-500" aria-hidden><InfoIcon /></span>
        <p>
          Danh sách được nhóm theo mã giảng viên phụ trách từ dữ liệu đã duyệt, chỉ gồm case ở trạng thái Đã duyệt hoặc Đã bàn giao.<br />
          Bản nháp không chứa điểm số nội bộ, email, số điện thoại hay họ tên thật.
        </p>
      </div>
    </div>
  );
}

/* ================= Bundle theo giảng viên ================= */

function BundleCard({ bundle }: { bundle: AdvisorHandoffDraftBundle }) {
  const router = useRouter();
  const limitations = resolveLimitations(bundle.limitations);

  return (
    <section className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
      {/* Header giảng viên */}
      <div className="flex flex-wrap items-center gap-3 px-6 py-4 border-b border-slate-100 bg-slate-50/50">
        <span className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-[#fee2e2] text-[#dc2626] shrink-0">
          <TeacherIcon />
        </span>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-slate-800">
            Giảng viên <span className="text-[#dc2626]">{bundle.advisor_display_name ?? bundle.advisor_ref}</span>
          </p>
          <p className="text-xs text-slate-400">
            {bundle.advisor_display_name && <span className="font-mono">Mã {bundle.advisor_ref} · </span>}
            {bundle.case_count} sinh viên trong danh sách bàn giao
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-0">
        {/* Danh sách case */}
        <div className="p-5 lg:border-r border-slate-100">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Sinh viên</p>
          <div className="space-y-2">
            {bundle.cases.map((c) => (
              <CaseLineRow key={c.case_id} line={c} onOpen={() => router.push(`/analysis/${c.case_id}`)} />
            ))}
          </div>
          {limitations.length > 0 && (
            <ul className="mt-4 space-y-1">
              {limitations.map((r, i) => (
                <li
                  key={i}
                  className={`text-xs ${r.known ? "text-slate-500" : "text-slate-400 italic"}`}
                >
                  {r.known ? r.text : `Mã kỹ thuật chưa có bản dịch: ${r.text}`}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Bản nháp mail */}
        <DraftPanel bundle={bundle} />
      </div>
    </section>
  );
}

function CaseLineRow({ line, onOpen }: { line: HandoffDraftCaseLine; onOpen: () => void }) {
  const factors = line.contributing_factor_codes.map((f) => FACTOR_LABEL[f] ?? f).join(", ") || "—";
  return (
    <button
      onClick={onOpen}
      title="Mở chi tiết case"
      className="w-full flex flex-wrap items-center gap-x-3 gap-y-1.5 px-3 py-2.5 text-left rounded-lg hover:bg-slate-50 transition-colors"
    >
      <span className="text-sm font-medium text-[#dc2626] w-20 shrink-0">{line.student_ref}</span>
      {line.class_code && (
        <span className="text-xs text-slate-400 shrink-0">{line.class_code}</span>
      )}
      <BandBadge band={line.review_priority_band} />
      {isCaseState(line.case_state) && <CaseStateBadge state={line.case_state} />}
      <span className="text-xs text-slate-500 flex-1 min-w-[140px] truncate">{factors}</span>
    </button>
  );
}

function DraftPanel({ bundle }: { bundle: AdvisorHandoffDraftBundle }) {
  const { draft } = bundle;
  const [copied, setCopied] = useState(false);

  const fullText = `${draft.subject}\n\n${draft.body}`;
  const mailto = `mailto:?subject=${encodeURIComponent(draft.subject)}&body=${encodeURIComponent(draft.body)}`;

  async function copy() {
    try {
      await navigator.clipboard.writeText(fullText);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="p-5 bg-slate-50/40">
      <div className="flex items-center justify-between gap-2 mb-3">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Bản nháp mail</p>
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 border border-amber-200 text-amber-700 text-[11px] font-semibold px-2.5 py-0.5">
          <DraftDot /> Cần Ban quản lý duyệt trước khi gửi
        </span>
      </div>

      {/* Nội dung render NGUYÊN VĂN từ API — FE không tự viết/sửa lời */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-100">
          <p className="text-[11px] text-slate-400">Tiêu đề</p>
          <p className="text-sm font-medium text-slate-700 mt-0.5">{draft.subject}</p>
        </div>
        <pre className="px-4 py-3 text-sm text-slate-600 whitespace-pre-wrap font-sans leading-relaxed max-h-72 overflow-y-auto">
          {draft.body}
        </pre>
      </div>

      <div className="flex flex-wrap gap-2 mt-3">
        <button
          onClick={copy}
          className="inline-flex items-center gap-2 bg-[#dc2626] hover:bg-[#b91c1c] text-white text-sm font-semibold rounded-lg px-4 py-2 shadow-sm shadow-red-600/25 transition-colors"
        >
          <CopyIcon />
          {copied ? "Đã sao chép" : "Sao chép nội dung"}
        </button>
        <a
          href={mailto}
          className="inline-flex items-center gap-2 bg-white hover:bg-slate-50 border border-slate-200 hover:border-slate-300 text-slate-600 text-sm font-semibold rounded-lg px-4 py-2 transition-colors"
        >
          <MailIcon />
          Mở trong mail
        </a>
      </div>
      <p className="text-[11px] text-slate-400 mt-2">
        &ldquo;Mở trong mail&rdquo; chỉ tạo thư nháp trong ứng dụng của bạn. Bạn chủ động điền người nhận.
      </p>
    </div>
  );
}

/* ================= Mapping repair ================= */

function MappingRepairCard({ bucket }: { bucket: { case_count: number; cases: HandoffDraftCaseLine[]; limitations: string[] } }) {
  const router = useRouter();
  const limitations = resolveLimitations(bucket.limitations);
  return (
    <section className="bg-white border border-dashed border-slate-300 rounded-2xl shadow-sm overflow-hidden">
      <div className="flex items-center gap-3 px-6 py-4 border-b border-slate-100 bg-slate-50/60">
        <span className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-slate-100 text-slate-500 shrink-0">
          <WrenchIcon />
        </span>
        <div>
          <p className="text-sm font-semibold text-slate-700">Chưa gán được giảng viên phụ trách</p>
          <p className="text-xs text-slate-400">
            {bucket.case_count} case đã duyệt nhưng chưa xác định được giảng viên phụ trách, nên chưa thể soạn mail bàn giao.
          </p>
        </div>
      </div>
      <div className="p-5">
        <div className="space-y-2">
          {bucket.cases.map((c) => (
            <CaseLineRow key={c.case_id} line={c} onOpen={() => router.push(`/analysis/${c.case_id}`)} />
          ))}
        </div>
        {limitations.length > 0 && (
          <ul className="mt-4 space-y-1">
            {limitations.map((r, i) => (
              <li key={i} className={`text-xs ${r.known ? "text-slate-500" : "text-slate-400 italic"}`}>
                {r.known ? r.text : `Mã kỹ thuật chưa có bản dịch: ${r.text}`}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

/* ================= States phụ ================= */

function EmptyCard() {
  return (
    <div className="flex min-h-[300px] flex-col items-center justify-center overflow-hidden rounded-2xl border border-red-100 bg-gradient-to-br from-red-50/90 via-rose-50/60 to-white px-8 py-7 text-center shadow-sm shadow-red-950/5 ring-1 ring-white/70 sm:min-h-[318px]">
      <Image
        src="/assets/branding/notify-empty-envelope.png"
        alt="Minh họa phong bì chứa bản nháp mail"
        width={190}
        height={190}
        priority
        className="mb-1 h-[148px] w-[148px] object-contain sm:h-[162px] sm:w-[162px]"
      />
      <h3 className="text-lg font-semibold tracking-tight text-slate-900">Chưa có danh sách bàn giao</h3>
      <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500">
        Khi Ban quản lý phê duyệt và bàn giao case cho giảng viên, bản nháp mail sẽ xuất hiện ở đây.
      </p>
      <div className="mt-4 inline-flex items-center gap-3 rounded-xl border border-red-100 bg-white/90 px-5 py-2.5 text-sm text-slate-600 shadow-sm shadow-red-950/5 backdrop-blur-sm">
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-red-50 text-red-500" aria-hidden><BulbIcon /></span>
        Hãy chọn bộ lọc hoặc tạo bản nháp để bắt đầu.
      </div>
    </div>
  );
}

function ErrorCard({ onReload }: { onReload: () => void }) {
  return (
    <div className="min-h-[260px] rounded-xl border border-red-200 bg-white p-8 text-center text-red-700 shadow-sm">
      <h3 className="font-semibold">Không tải được danh sách bàn giao</h3>
      <p className="text-sm text-red-600/80 mt-1">Máy chủ tạm thời không phản hồi. Vui lòng thử lại.</p>
      <button
        onClick={onReload}
        className="mt-4 text-sm font-medium text-red-700 border border-red-200 bg-white rounded-lg px-4 py-2 hover:border-red-300 transition-colors"
      >
        ↻ Thử lại
      </button>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="h-[318px] animate-pulse rounded-xl border border-slate-200 bg-white p-8 shadow-sm" aria-busy="true" aria-label="Đang tải danh sách bản nháp">
      <div className="mx-auto mt-10 h-32 w-32 rounded-full bg-slate-100" />
      <div className="mx-auto mt-5 h-5 w-56 rounded bg-slate-100" />
      <div className="mx-auto mt-3 h-4 w-96 max-w-full rounded bg-slate-100" />
    </div>
  );
}

/* ================= Helpers + icons ================= */

function isCaseState(s: string): s is CaseState {
  return s in CASE_STATE_LABEL;
}

function AlertIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden>
      <path d="M12 7v6" />
      <path d="M12 17h.01" />
    </svg>
  );
}

function TeacherGroupIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

function TagIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M20.6 13.6 11 23.2 1.8 14V3h11z" transform="scale(.88) translate(1 0)" />
      <circle cx="8" cy="8" r="1.2" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-4-4" />
    </svg>
  );
}

function ChevronIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

function RefreshIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M20 6v5h-5" />
      <path d="M4 18v-5h5" />
      <path d="M6.1 9a7 7 0 0 1 11.5-2.6L20 9M4 15l2.4 2.6A7 7 0 0 0 17.9 15" />
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

function InfoIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5M12 8h.01" />
    </svg>
  );
}

function BulbIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M9 18h6M10 22h4" />
      <path d="M8.2 14.5A7 7 0 1 1 15.8 14.5c-.8.7-1.2 1.5-1.3 2.5h-5c-.1-1-.5-1.8-1.3-2.5Z" />
    </svg>
  );
}

function TeacherIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
      <path d="M6 12v5c3 3 9 3 12 0v-5" />
    </svg>
  );
}

function WrenchIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M14.7 6.3a4 4 0 00-5.4 5.3L3 18l3 3 6.4-6.4a4 4 0 005.3-5.4l-2.6 2.6-2.3-2.3z" />
    </svg>
  );
}

function CopyIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <rect x="9" y="9" width="13" height="13" rx="2" />
      <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
    </svg>
  );
}

function MailIcon({ large }: { large?: boolean }) {
  const s = large ? 30 : 15;
  return (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="M22 7l-10 6L2 7" />
    </svg>
  );
}

function DraftDot() {
  return <span className="w-1.5 h-1.5 rounded-full bg-amber-500 inline-block" aria-hidden />;
}
