"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AppShell, useSetTopbarInfo } from "@/components/AppShell";
import { BandBadge, CaseStateBadge } from "@/components/badges";
import { ReportModal } from "@/components/ReportModal";
import { ThresholdPanel } from "@/components/ThresholdPanel";
import { fetchReviewCases } from "@/lib/api";
import { FACTOR_LABEL } from "@/lib/factors";
import { splitAccountName, useSession } from "@/lib/session";
import {
  BAND_LABEL,
  CASE_STATE_LABEL,
  type CaseListResponse,
  type ReviewCase,
} from "@/lib/types";

/**
 * Workspace Ban quản lý — dữ liệu live GET /review-cases.
 * /overview là Agent Home; /analysis chỉ còn 3 mục vận hành: Dashboard,
 * Danh sách rà soát và Ngưỡng. Dashboard ưu tiên tín hiệu cần rà soát sớm;
 * danh sách hợp nhất hai view Tín hiệu/Sinh viên từng render cùng một DTO.
 * Tab Tổng quan = Agent Home (plan.md §3.2): robot + MỘT bản tin duy nhất về kỳ
 * dữ liệu + 3 tool (xuất báo cáo / phân tích SV / soạn mail GVCN — G06 chưa mở).
 * Fail-closed: nguồn lỗi → hiện lỗi, không bịa dữ liệu (mọi số trên trang đều
 * tính từ response — không hardcode đếm/trend/thời gian; không vẽ delta tuần
 * hay sparkline vì chưa có API lịch sử).
 */

type Tab = "overview" | "analytics" | "reviews" | "threshold";
type AnalysisTab = "dashboard" | "reviews" | "threshold";

function normalizeAnalysisTab(raw: string | null): AnalysisTab {
  if (raw === "reviews" || raw === "signals" || raw === "students") return "reviews";
  if (raw === "threshold") return "threshold";
  return "dashboard";
}

export default function ManagementWorkspace() {
  // Không truyền title — hero chào thay cho breadcrumb + h1 (yêu cầu 18/7 v3).
  return (
    <AppShell role="ban_quan_ly">
      <Suspense fallback={<ListSkeleton />}>
        <DashboardBody />
      </Suspense>
    </AppShell>
  );
}

function DashboardBody() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const isAnalysisRoute = pathname === "/analysis";
  // Link cũ signals/students cùng về danh sách hợp nhất; fairness về Dashboard.
  const rawTab = searchParams.get("tab");
  const analysisTab = normalizeAnalysisTab(rawTab);
  const tab: Tab = isAnalysisRoute
    ? analysisTab === "dashboard" ? "analytics" : analysisTab
    : "overview";
  const setTab = useCallback(
    (t: Tab) => {
      if (isAnalysisRoute) {
        router.replace(`/analysis?tab=${t === "analytics" ? "dashboard" : t}`, { scroll: false });
      } else if (t !== "overview") {
        router.replace(`/analysis?tab=${t === "analytics" ? "dashboard" : t}`, { scroll: false });
      } else {
        router.replace("/overview", { scroll: false });
      }
    },
    [isAnalysisRoute, router],
  );

  const [loading, setLoading] = useState(true);
  const [response, setResponse] = useState<CaseListResponse | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    const controller = new AbortController();
    fetchReviewCases(controller.signal).then((r) => {
      setResponse(r);
      setLoading(false);
    });
    return controller;
  }, []);

  useEffect(() => {
    const controller = load();
    return () => controller.abort();
  }, [load]);

  const openCase = useCallback((id: string) => router.push(`/analysis/${id}`), [router]);

  // Bơm dữ liệu thật lên topbar (thời điểm cập nhật = calculated_at mới nhất;
  // badge = số case Ưu tiên sớm). Không hardcode.
  const topInfo = useMemo(() => {
    const items = response?.items ?? [];
    const updatedAt = items.reduce((m, c) => (c.calculated_at > m ? c.calculated_at : m), "");
    const alertCount = items.filter((c) => c.review_priority_band === "uu_tien_som").length;
    return { updatedAt: updatedAt || null, alertCount };
  }, [response]);
  useSetTopbarInfo(topInfo.updatedAt, topInfo.alertCount);

  return (
    <div className="space-y-6">
      {isAnalysisRoute && <AnalysisTabs active={analysisTab} onChange={(next) => setTab(next === "dashboard" ? "analytics" : next)} />}
      {/* Khối "Phạm vi MVP" (ScopeBanner/H12b) đã bỏ theo yêu cầu owner 18/7 —
          copy giới hạn phạm vi còn lại ở disclaimer đầu trang + chip cam kết trong hero. */}
      {(tab === "analytics" || tab === "reviews") && (
        <div className="flex justify-end">
          <button
            onClick={() => load()}
            className="text-xs text-slate-500 border border-slate-200 bg-white rounded-lg px-3 py-1.5 hover:border-slate-300 transition-colors"
          >
            ↻ Tải lại dữ liệu
          </button>
        </div>
      )}

      {tab === "overview" && (
        <OverviewHeader loading={loading} response={response} setTab={setTab} onReload={load} onOpenCase={openCase} />
      )}
      {tab === "analytics" && (
        <AnalyticsTab loading={loading} response={response} setTab={setTab} onReload={load} />
      )}
      {tab === "reviews" && (
        loading ? <ListSkeleton compact /> : response ? <ReviewList response={response} onOpenCase={openCase} /> : null
      )}
      {tab === "threshold" && <ThresholdPanel />}

      {/* Ẩn ở Tổng quan để khu AI phủ trọn màn hình */}
      {tab !== "overview" && (
        <p className="text-xs text-slate-400">
          Dữ liệu và hành động đi thẳng API — không hiển thị điểm số nội bộ của model.
          Scoping theo khoa/lớp và danh sách toàn bộ SV chờ API bổ sung (design spec §9).
        </p>
      )}
    </div>
  );
}

function AnalysisTabs({ active, onChange }: { active: AnalysisTab; onChange: (tab: AnalysisTab) => void }) {
  const tabs: { id: AnalysisTab; label: string }[] = [
    { id: "dashboard", label: "Dashboard" },
    { id: "reviews", label: "Danh sách rà soát" },
    { id: "threshold", label: "Ngưỡng" },
  ];

  return (
    <nav aria-label="Các mục phân tích" className="flex flex-wrap gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
      {tabs.map((item) => (
        <button
          key={item.id}
          type="button"
          onClick={() => onChange(item.id)}
          aria-current={active === item.id ? "page" : undefined}
          className={`rounded-xl px-4 py-2.5 text-sm font-medium transition-colors ${
            active === item.id ? "bg-red-50 text-red-700" : "text-slate-500 hover:bg-slate-50 hover:text-slate-800"
          }`}
        >
          {item.label}
        </button>
      ))}
    </nav>
  );
}

/* ================= Đếm dùng chung (Tổng quan + Dashboard) ================= */

function computeCounts(items: ReviewCase[]) {
  const byState = (s: string) => items.filter((c) => c.case_state === s).length;
  const early = (list: ReviewCase[]) => list.filter((c) => c.review_priority_band === "uu_tien_som").length;
  return {
    total: items.length,
    students: new Set(items.map((c) => c.student_ref)).size,
    newSignals: byState("new_signal"),
    newEarly: early(items.filter((c) => c.case_state === "new_signal")),
    pending: byState("pending_review"),
    assigned: byState("assigned"),
    inProgress: byState("follow_up_in_progress"),
    monitoring: byState("monitoring"),
    active: byState("assigned") + byState("follow_up_in_progress") + byState("monitoring"),
    earlyPriority: early(items),
    limitedData: items.filter((c) => c.data_state !== "ok").length,
  };
}

function ErrorCard({ onReload }: { onReload: () => void }) {
  return (
    <div className="bg-red-50 border border-red-200 text-red-700 p-6 rounded-2xl">
      <h3 className="font-semibold">Không tải được dữ liệu</h3>
      <p className="text-sm text-red-600/80 mt-1">Máy chủ tạm thời không phản hồi. Vui lòng bấm “Tải lại dữ liệu”.</p>
      <button
        onClick={onReload}
        className="mt-4 text-sm font-medium text-red-700 border border-red-200 bg-white rounded-lg px-4 py-2 hover:border-red-300 transition-colors"
      >
        ↻ Tải lại dữ liệu
      </button>
    </div>
  );
}

/* ================= Tổng quan — Agent Home (plan.md §3.2) ================= */

function OverviewHeader({
  loading,
  response,
  setTab,
  onReload,
  onOpenCase,
}: {
  loading: boolean;
  response: CaseListResponse | null;
  setTab: (t: Tab) => void;
  onReload: () => void;
  onOpenCase: (caseId: string) => void;
}) {
  const router = useRouter();
  const { account } = useSession();
  const { name: shortName } = splitAccountName(account?.name ?? "thầy/cô");
  const items = useMemo(() => (response && response.state !== "error" ? response.items : []), [response]);
  const counts = useMemo(() => computeCounts(items), [items]);
  // Thời điểm AI "phân tích" = calculated_at mới nhất từ response — không hardcode.
  const analyzedAt = useMemo(() => items.reduce((m, c) => (c.calculated_at > m ? c.calculated_at : m), ""), [items]);
  // Tool 1 — modal "Báo cáo tổng thể" (plan.md §3.2); mở tại chỗ, không rời trang.
  const [reportOpen, setReportOpen] = useState(false);

  // Fetch đang chạy thật → hiển thị trạng thái "đang phân tích" (không phải hiệu ứng giả).
  if (loading) {
    return (
      <div className="min-h-[calc(100vh-170px)] flex flex-col items-center justify-center gap-8 rounded-3xl border border-[#fbd7d7] bg-gradient-to-br from-white via-[#fef2f2] to-[#fde4e4]">
        <div
          role="img"
          aria-label="Trợ lý EduSignal AI"
          className="ss-float w-48 h-44 bg-contain bg-center bg-no-repeat"
          style={{ backgroundImage: "url(/assets/branding/edusignal-ai-robot.png)", mixBlendMode: "multiply" }}
        />
        <div className="bg-white rounded-2xl rounded-tl-md shadow-md border border-[#fbeaea] px-6 py-4 flex items-center gap-3">
          <span className="text-sm text-slate-600">Đang phân tích dữ liệu</span>
          <span className="flex gap-1" aria-hidden>
            <span className="ss-typing-dot w-1.5 h-1.5 rounded-full bg-[#dc2626] inline-block" />
            <span className="ss-typing-dot w-1.5 h-1.5 rounded-full bg-[#dc2626] inline-block" />
            <span className="ss-typing-dot w-1.5 h-1.5 rounded-full bg-[#dc2626] inline-block" />
          </span>
        </div>
      </div>
    );
  }
  if (!response) return null;
  if (response.state === "error") return <ErrorCard onReload={onReload} />;

  // Một thông báo duy nhất (plan.md §3.2): ghép các vế có số thật > 0 thành 1 đoạn
  // bản tin — không bịa mục, không so sánh "tuần trước" (chưa có API lịch sử, §6 #5).
  const isStale = response.state === "stale";
  const latest = items.length > 0 ? items.reduce((m, c) => (c.calculated_at > m.calculated_at ? c : m)) : null;
  const segments: { strong: string; text: string }[] = [];
  if (counts.earlyPriority > 0) segments.push({ strong: `${counts.earlyPriority} trường hợp`, text: "nên được ưu tiên rà soát trước" });
  if (counts.newSignals > 0) segments.push({ strong: `${counts.newSignals} tín hiệu mới`, text: "được phát hiện" });
  if (counts.pending > 0) segments.push({ strong: `${counts.pending} case`, text: "đang chờ thầy/cô duyệt" });
  if (counts.active > 0) segments.push({ strong: `${counts.active} case`, text: "đang được theo dõi / hỗ trợ" });
  if (counts.limitedData > 0) segments.push({ strong: `${counts.limitedData} case`, text: "dữ liệu còn hạn chế — hệ thống không kết luận khi thiếu dữ liệu" });

  // 3 tool của EduSignal AI (plan.md §3.2). Các tool chỉ điều hướng tới route
  // đã có thật; trang Tổng quan không tự tính thêm band hay dữ liệu sinh viên.
  const watched = items.filter((c) => c.case_state !== "dismissed" && c.case_state !== "resolved");
  const watchStudents = new Set(watched.map((c) => c.student_ref)).size;
  const tools: { key: string; icon: string; title: string; desc: string; accent: string; onClick?: () => void; disabled?: boolean }[] = [
    {
      key: "report",
      icon: iconPaths.fileText,
      title: "Xuất báo cáo tổng thể",
      desc: `${watchStudents} SV trong diện theo dõi · ${counts.newSignals} phát hiện mới — xem, in / lưu PDF`,
      accent: "bg-[#fee2e2] text-[#dc2626]",
      onClick: () => setReportOpen(true),
    },
    {
      key: "analyze",
      icon: iconPaths.search,
      title: "Danh sách rà soát",
      desc: `${counts.total} case trên ${counts.students} sinh viên — lọc và mở phân tích chi tiết`,
      accent: "bg-emerald-50 text-emerald-600",
      onClick: () => router.push("/analysis?tab=reviews"),
    },
    {
      key: "notify",
      icon: iconPaths.mail,
      title: "Soạn mail cho GVCN",
      desc: "Lọc sinh viên theo giảng viên phụ trách và xem bản nháp mail bàn giao",
      accent: "bg-sky-50 text-sky-600",
      onClick: () => router.push("/notify"),
    },
  ];

  return (
    // Thông báo AI phủ toàn màn hình nội dung (trừ sidebar): min-height = viewport trừ topbar
    // + padding của main. Mọi con số đều từ response — không hardcode.
    <div className="min-h-[calc(100vh-170px)] flex flex-col rounded-3xl border border-[#fbd7d7] bg-gradient-to-br from-white via-[#fef2f2] to-[#fde4e4] relative overflow-hidden px-6 py-8 md:px-12 md:py-10">
      {/* Trang trí nền — thuần CSS/SVG, không mang dữ liệu */}
      <div className="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-[#fbd7d7]/50 blur-3xl" aria-hidden />
      <div className="absolute bottom-0 left-1/3 w-80 h-80 rounded-full bg-[#fde4e4]/70 blur-3xl" aria-hidden />
      {/* Watermark shield + network node lấp khoảng trống bên phải (kiểu Copilot) */}
      <svg className="hidden lg:block absolute right-8 top-1/2 -translate-y-1/2 w-[380px] h-[420px] text-[#dc2626] opacity-[0.06]" viewBox="0 0 120 132" fill="none" aria-hidden>
        <path d="M60 6 L106 24 V66 C106 98 60 124 60 124 C60 124 14 98 14 66 V24 Z" stroke="currentColor" strokeWidth="3" />
        <path d="M60 22 L92 34 V64 C92 86 60 106 60 106 C60 106 28 86 28 64 V34 Z" stroke="currentColor" strokeWidth="1.5" />
      </svg>
      <svg className="hidden lg:block absolute right-16 top-16 w-72 h-72 text-[#dc2626] opacity-[0.10]" viewBox="0 0 200 200" fill="none" aria-hidden>
        <line x1="30" y1="40" x2="100" y2="90" stroke="currentColor" strokeWidth="1" />
        <line x1="100" y1="90" x2="170" y2="50" stroke="currentColor" strokeWidth="1" />
        <line x1="100" y1="90" x2="80" y2="160" stroke="currentColor" strokeWidth="1" />
        <line x1="170" y1="50" x2="160" y2="130" stroke="currentColor" strokeWidth="1" />
        <line x1="80" y1="160" x2="160" y2="130" stroke="currentColor" strokeWidth="1" />
        <circle cx="30" cy="40" r="5" fill="currentColor" />
        <circle cx="100" cy="90" r="7" fill="currentColor" />
        <circle cx="170" cy="50" r="5" fill="currentColor" />
        <circle cx="80" cy="160" r="5" fill="currentColor" />
        <circle cx="160" cy="130" r="5" fill="currentColor" />
      </svg>
      <svg className="absolute bottom-0 left-0 w-full h-28 opacity-60" viewBox="0 0 1200 90" preserveAspectRatio="none" aria-hidden>
        <path d="M0 45 C 200 12, 400 78, 620 45 S 1010 12, 1200 45 V90 H0 Z" fill="#fbd7d7" opacity="0.5" />
        <path d="M0 60 C 260 30, 460 86, 720 55 S 1060 32, 1200 60 V90 H0 Z" fill="#f6bcbc" opacity="0.35" />
      </svg>

      {/* Lời chào + trạng thái AI */}
      <div className="relative z-10 flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold text-slate-800">
            Chào <span className="text-[#dc2626]">{shortName}</span> 👋
          </h1>
          <p className="mt-2 text-slate-500 md:text-[15px]">
            Chúc thầy/cô một ngày làm việc hiệu quả. EduSignal đã hoàn tất rà soát dữ liệu mới nhất.
          </p>
          <p className="mt-1 text-slate-400 text-sm">
            Hệ thống <strong className="font-semibold text-slate-600">chỉ gợi ý</strong> — mọi quyết định do thầy/cô thực hiện.
          </p>
        </div>
        {analyzedAt && (
          <span className="inline-flex items-center gap-2 self-start bg-white/80 border border-emerald-100 rounded-full px-4 py-2 shadow-sm shrink-0">
            <span className="ss-live-dot w-2 h-2 rounded-full bg-emerald-500 inline-block" aria-hidden />
            <span className="text-xs text-slate-600">
              <strong className="font-semibold text-emerald-600">EduSignal AI</strong> · Đã phân tích dữ liệu lúc {formatAnalyzedAt(analyzedAt)}
            </span>
          </span>
        )}
      </div>

      {/* Khu chat: robot + bong bóng "suy nghĩ" */}
      <div className="relative z-10 flex-1 flex flex-col lg:flex-row items-center gap-8 lg:gap-4 py-8 md:py-10">
        {/* Robot mascot (asset thật, 300px, lơ lửng + bóng đổ theo nhịp) */}
        <div className="shrink-0 relative">
          <div className="absolute inset-6 rounded-full bg-white/60 blur-2xl" aria-hidden />
          <div
            role="img"
            aria-label="Trợ lý EduSignal AI"
            className="ss-float relative w-64 h-60 md:w-[300px] md:h-[270px] bg-contain bg-center bg-no-repeat"
            style={{ backgroundImage: "url(/assets/branding/edusignal-ai-robot.png)", mixBlendMode: "multiply" }}
          />
          <div className="ss-shadow-anim mx-auto mt-1 w-40 h-4 rounded-[50%] bg-[#dc2626]/15 blur-[2px]" aria-hidden />
        </div>

        {/* Chuỗi bóng suy nghĩ nối robot → panel (desktop) */}
        <div className="hidden lg:flex flex-col items-center gap-2.5 self-center shrink-0 px-2" aria-hidden>
          <span className="ss-float w-5 h-5 rounded-full bg-white border-2 border-[#f6bcbc] shadow-sm translate-x-3" style={{ animationDelay: "0.4s" }} />
          <span className="ss-float w-3 h-3 rounded-full bg-white border-2 border-[#f6bcbc] shadow-sm -translate-x-2" style={{ animationDelay: "0.8s" }} />
        </div>

        {/* Panel suy nghĩ của AI — glow đỏ thở nhẹ + viền đậm cho nổi bật */}
        <div className="flex-1 min-w-0 max-w-2xl space-y-4">
          <div className="relative">
            <div className="ss-glow absolute -inset-2 rounded-[28px] bg-[#dc2626]/10 blur-xl" aria-hidden />
            <div className="relative bg-white rounded-3xl rounded-tl-lg border-2 border-[#f6bcbc] shadow-xl shadow-red-900/10 px-7 py-6">
              {/* Đuôi bong bóng trỏ lên robot khi xếp dọc (mobile) */}
              <div className="lg:hidden absolute -top-[11px] left-12 w-5 h-5 bg-white border-l-2 border-t-2 border-[#f6bcbc] rotate-45" aria-hidden />
              <p className="inline-flex items-center gap-1.5 bg-gradient-to-r from-[#dc2626] to-[#ef4444] text-white text-xs font-bold rounded-full px-3.5 py-1.5 shadow-md shadow-red-600/30">
                <Icon path={iconPaths.sparkles} className="w-3.5 h-3.5 animate-pulse" /> EduSignal AI
              </p>
              <p className="text-xl md:text-2xl font-bold text-slate-800 mt-3">Xin chào {shortName} 👋</p>
              {/* Bản tin duy nhất về kỳ dữ liệu — một đoạn, mọi số từ response */}
              {counts.total > 0 ? (
                <p className="mt-2.5 text-[15px] text-slate-600 leading-relaxed">
                  Trong kỳ dữ liệu này, tôi ghi nhận{" "}
                  <strong className="font-semibold text-[#dc2626]">{counts.total} tín hiệu</strong> trên{" "}
                  <strong className="font-semibold text-[#dc2626]">{counts.students} sinh viên</strong>
                  {segments.length > 0 ? ": " : "."}
                  {segments.map((s, i) => (
                    <span key={s.strong + s.text}>
                      <strong className="font-semibold text-[#dc2626]">{s.strong}</strong> {s.text}
                      {i < segments.length - 1 ? "; " : "."}
                    </span>
                  ))}
                </p>
              ) : (
                <p className="text-sm text-slate-500 mt-1.5">
                  Chưa có tín hiệu mới cần chú ý trong kỳ dữ liệu này — tôi sẽ tiếp tục theo dõi.
                </p>
              )}
              {isStale && (
                <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
                  Snapshot có thể đã cũ — số liệu trên không được coi là mới nhất.
                </p>
              )}
              <button
                onClick={() => setTab("reviews")}
                className="mt-5 inline-flex items-center gap-2 bg-[#dc2626] hover:bg-[#b91c1c] text-white font-semibold text-sm rounded-xl px-5 py-3 shadow-md shadow-red-600/25 transition-colors"
              >
                Xem chi tiết gợi ý
                <Icon path={iconPaths.arrowRight} className="w-4 h-4" />
              </button>
              {/* Nguồn của bản tin — snapshot/version thật từ response, không suy đoán */}
              {latest && (
                <p className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-400">
                  Snapshot {formatAnalyzedAt(analyzedAt)} · dataset {latest.dataset_version} · model {latest.model_version} — bản tin tính trực tiếp từ dữ liệu, chưa gọi model AI.
                </p>
              )}
            </div>
          </div>

          {/* Ô hỏi nhanh — rule-based trên dữ liệu đã tải, KHÔNG gọi model (chat LLM là task lane Agent) */}
          <AiQuickChat counts={counts} setTab={setTab} />
        </div>
      </div>

      {/* 3 tool của EduSignal AI — tương tác chuột dẫn sang các hướng (plan.md §3.2) */}
      <div className="relative z-10">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {tools.map((t) => (
            <button
              key={t.key}
              onClick={t.onClick}
              disabled={t.disabled}
              className={
                t.disabled
                  ? "bg-white/60 border border-dashed border-slate-200 rounded-2xl p-5 text-left cursor-not-allowed"
                  : "group bg-white border border-[#fbeaea] rounded-2xl p-5 text-left shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-1 hover:border-[#f4b8b8]"
              }
            >
              <div className={`p-2.5 rounded-xl w-fit ${t.disabled ? "bg-slate-100 text-slate-400" : t.accent}`}>
                <Icon path={t.icon} className="w-5 h-5" />
              </div>
              <p className={`text-sm font-semibold mt-3 flex items-center gap-1.5 ${t.disabled ? "text-slate-500" : "text-slate-800"}`}>
                {t.title}
                {!t.disabled && (
                  <Icon path={iconPaths.arrowRight} className="w-3.5 h-3.5 text-slate-300 group-hover:text-[#dc2626] group-hover:translate-x-1 transition-all" />
                )}
              </p>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">{t.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Tool 1 — Báo cáo tổng thể (in / lưu PDF tại chỗ) */}
      {reportOpen && <ReportModal items={items} onClose={() => setReportOpen(false)} onOpenCase={onOpenCase} />}
    </div>
  );
}

/** "17:56 hôm nay" hoặc "17:56 • 12/07/2026" từ ISO — so sánh theo ngày địa phương. */
function formatAnalyzedAt(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  const time = d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
  const today = new Date();
  const sameDay = d.toDateString() === today.toDateString();
  return sameDay ? `${time} hôm nay` : `${time} • ${d.toLocaleDateString("vi-VN")}`;
}

/* ---------- Hỏi nhanh EduSignal — rule-based intent router (demo) ----------
 * KHÔNG gọi LLM: khớp từ khóa → trả lời bằng số đã tính từ response + nút điều hướng
 * tới trang có thật. Không nhận diện được → nói thẳng, không bịa câu trả lời.
 * Chat tự do cần agent API (H24) — task lane Agent, ngoài scope UI này. */

type QuickAnswer = { a: string; action?: { label: string; tab: Tab } };

function routeIntent(q: string, c: ReturnType<typeof computeCounts>): QuickAnswer {
  const s = q.toLowerCase();
  const has = (re: RegExp) => re.test(s);

  if (has(/ưu tiên|uu tien/)) {
    return {
      a: `Hiện có ${c.earlyPriority} trường hợp ở mức Ưu tiên sớm (trên tổng ${c.total} tín hiệu).`,
      action: { label: "Mở danh sách rà soát", tab: "reviews" },
    };
  }
  if (has(/tại sao|tai sao|vì sao|vi sao|giải thích|giai thich|ly do|lý do/)) {
    return {
      a: "Lý do gợi ý của từng trường hợp (yếu tố đóng góp, độ phủ dữ liệu) nằm trong trang chi tiết case — mở danh sách tín hiệu rồi chọn case cần xem.",
      action: { label: "Mở danh sách rà soát", tab: "reviews" },
    };
  }
  if (has(/mới|moi/)) {
    return {
      a: `Kỳ này có ${c.newSignals} tín hiệu mới${c.newEarly > 0 ? `, trong đó ${c.newEarly} ở mức Ưu tiên sớm` : ""}.`,
      action: { label: "Mở danh sách rà soát", tab: "reviews" },
    };
  }
  if (has(/duyệt|duyet/)) {
    return {
      a: `Có ${c.pending} case đang chờ duyệt.`,
      action: { label: "Mở danh sách rà soát", tab: "reviews" },
    };
  }
  if (has(/sinh viên|sinh vien|\bsv\b|lớp|lop/)) {
    const note = has(/lớp|lop/) ? " Lọc theo lớp/khoa chưa có API — hiện tra cứu được theo mã SV." : "";
    return {
      a: `Có ${c.students} sinh viên đang có tín hiệu trong kỳ này.${note}`,
      action: { label: "Mở danh sách rà soát", tab: "reviews" },
    };
  }
  if (has(/dashboard|thống kê|thong ke|biểu đồ|bieu do|số liệu|so lieu|kpi/)) {
    return { a: "Toàn bộ KPI, biểu đồ và việc cần làm nằm ở trang Dashboard.", action: { label: "Mở Dashboard", tab: "analytics" } };
  }
  if (has(/ngưỡng|nguong|threshold/)) {
    return { a: "Cấu hình ngưỡng phân band hiện hành nằm ở trang Ngưỡng.", action: { label: "Mở trang Ngưỡng", tab: "threshold" } };
  }
  if (has(/tín hiệu|tin hieu|theo dõi|theo doi|hỗ trợ|ho tro/)) {
    return {
      a: `Tổng quan hiện tại: ${c.total} tín hiệu · ${c.newSignals} mới · ${c.pending} chờ duyệt · ${c.active} đang theo dõi/hỗ trợ.`,
      action: { label: "Mở danh sách rà soát", tab: "reviews" },
    };
  }
  return {
    a: "Tôi chưa hỗ trợ câu này trong bản demo. Thử hỏi về: trường hợp ưu tiên, tín hiệu mới, case chờ duyệt, danh sách rà soát, dashboard hoặc ngưỡng.",
  };
}

function AiQuickChat({ counts, setTab }: { counts: ReturnType<typeof computeCounts>; setTab: (t: Tab) => void }) {
  const [q, setQ] = useState("");
  const [exchange, setExchange] = useState<{ q: string; answer: QuickAnswer } | null>(null);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const text = q.trim();
    if (!text) return;
    setExchange({ q: text, answer: routeIntent(text, counts) });
    setQ("");
  }

  return (
    <div className="space-y-3">
      {exchange && (
        <>
          {/* Bubble người dùng (phải) */}
          <div className="flex justify-end">
            <div className="bg-[#dc2626] text-white text-sm rounded-2xl rounded-tr-md px-5 py-3 max-w-[85%] shadow-sm">
              {exchange.q}
            </div>
          </div>
          {/* Bubble AI trả lời (trái) */}
          <div className="bg-white rounded-2xl rounded-tl-md shadow-sm border border-[#fbeaea] px-5 py-4 max-w-[92%]">
            <p className="text-sm text-slate-600">{exchange.answer.a}</p>
            {exchange.answer.action && (
              <button
                onClick={() => setTab(exchange.answer.action!.tab)}
                className="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold text-[#dc2626] hover:text-[#b91c1c] group"
              >
                {exchange.answer.action.label}
                <Icon path={iconPaths.arrowRight} className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </button>
            )}
          </div>
        </>
      )}

      <form onSubmit={submit} className="flex items-center gap-2 bg-white border border-[#fbd7d7] rounded-full pl-5 pr-2 py-2 shadow-sm focus-within:border-[#dc2626] transition-colors">
        <span className="text-base shrink-0" aria-hidden>🤖</span>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Hỏi EduSignal AI… (vd: có bao nhiêu trường hợp ưu tiên hôm nay?)"
          aria-label="Hỏi nhanh EduSignal AI"
          className="flex-1 min-w-0 bg-transparent text-sm outline-none placeholder:text-slate-400"
        />
        <button
          type="submit"
          className="shrink-0 w-9 h-9 rounded-full bg-[#dc2626] hover:bg-[#b91c1c] text-white flex items-center justify-center transition-colors"
          aria-label="Gửi câu hỏi"
        >
          <Icon path={iconPaths.arrowRight} className="w-4 h-4" />
        </button>
      </form>
      <p className="text-[11px] text-slate-400 pl-2">
        Trợ lý điều hướng (demo) — trả lời được tính từ dữ liệu đang hiển thị, chưa gọi model AI.
      </p>
    </div>
  );
}

/* ================= Dashboard — KPI + biểu đồ + việc cần làm + gần đây ================= */

function AnalyticsTab({
  loading,
  response,
  setTab,
  onReload,
}: {
  loading: boolean;
  response: CaseListResponse | null;
  setTab: (t: Tab) => void;
  onReload: () => void;
}) {
  const items = useMemo(() => (response && response.state !== "error" ? response.items : []), [response]);
  const counts = useMemo(() => computeCounts(items), [items]);

  if (loading) return <ListSkeleton />;
  if (!response) return null;
  if (response.state === "error") return <ErrorCard onReload={onReload} />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
          <p className="mt-1 text-sm text-slate-500">Tập trung vào tín hiệu cần rà soát sớm và khối lượng đang chờ xử lý.</p>
        </div>
        <button
          type="button"
          onClick={() => setTab("reviews")}
          className="inline-flex items-center gap-2 rounded-xl bg-[#dc2626] px-4 py-2.5 text-sm font-semibold text-white shadow-sm shadow-red-600/20 transition-colors hover:bg-[#b91c1c]"
        >
          Mở danh sách rà soát
          <Icon path={iconPaths.arrowRight} className="h-4 w-4" />
        </button>
      </div>

      {response.state === "stale" && (
        <div className="bg-amber-50 border border-amber-200 text-amber-700 p-4 rounded-2xl text-sm">
          Dữ liệu có thể đã cũ — snapshot chưa được cập nhật gần đây.
        </div>
      )}

      {response.state === "empty" ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center shadow-sm">
          <div className="mx-auto w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
            <Icon path={iconPaths.heart} className="w-8 h-8 text-slate-300" />
          </div>
          <h3 className="text-lg font-semibold text-slate-700">Chưa có tín hiệu trong kỳ này</h3>
          <p className="text-sm text-slate-400 mt-1">Không có tín hiệu không đồng nghĩa mọi sinh viên đều ổn định — xem thêm độ phủ nguồn.</p>
        </div>
      ) : (
        <>
          {/* Ba KPI duy nhất: một mục tiêu chính và hai tải công việc cần xử lý. */}
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-5">
            <section className="relative overflow-hidden rounded-2xl border border-red-200 bg-gradient-to-br from-red-50 via-white to-white p-6 shadow-sm lg:col-span-3">
              <div className="absolute -right-12 -top-12 h-40 w-40 rounded-full bg-red-100/60" aria-hidden />
              <div className="relative">
                <div className="flex items-center gap-2.5 text-sm font-semibold text-red-700">
                  <span className="rounded-lg bg-red-100 p-2"><Icon path={iconPaths.sparkles} className="h-4 w-4" /></span>
                  Tín hiệu cần rà soát sớm
                </div>
                <p className="mt-5 text-6xl font-bold tracking-tight text-slate-900 tabular-nums">{counts.earlyPriority}</p>
                <p className="mt-2 text-sm text-slate-500">trên {counts.total} case của {counts.students} sinh viên trong lần tracking hiện tại</p>
                <div className="mt-5 flex flex-wrap gap-x-4 gap-y-1 border-t border-red-100 pt-4 text-xs text-slate-400">
                  <span>{counts.limitedData} case có dữ liệu hạn chế</span>
                  <span>Chưa có API lịch sử để tính chênh lệch với lần trước</span>
                </div>
              </div>
            </section>

            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:col-span-2 lg:grid-cols-1">
              <KpiCard
                label="Tín hiệu mới"
                value={counts.newSignals}
                sub={counts.newEarly > 0 ? `${counts.newEarly} cần rà soát sớm` : "không có mức ưu tiên sớm"}
                icon={iconPaths.activity}
                color="amber"
              />
              <KpiCard
                label="Đang chờ duyệt"
                value={counts.pending}
                sub="cần quyết định của Ban quản lý"
                icon={iconPaths.clock}
                color="slate"
              />
            </div>
          </div>

          {/* Một biểu đồ vận hành duy nhất; chi tiết priority/factor nằm ở danh sách. */}
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <ChartHeader title="Trạng thái xử lý" subtitle="Số case ở từng bước của quy trình hiện tại" icon={iconPaths.activity} />
            <BarRows rows={stateRows(items)} color="#dc2626" />
          </section>
        </>
      )}
    </div>
  );
}

function stateRows(items: ReviewCase[]) {
  const present = Array.from(new Set(items.map((c) => c.case_state)));
  return present
    .map((s) => ({ label: CASE_STATE_LABEL[s], value: items.filter((c) => c.case_state === s).length }))
    .sort((a, b) => b.value - a.value);
}

/* ================= Danh sách rà soát hợp nhất ================= */

type SortKey = "band" | "newest" | "ref" | "state";
type BandFilter = "all" | "uu_tien_som" | "can_ra_soat" | "unassigned";

function ReviewList({ response, onOpenCase }: { response: CaseListResponse; onOpenCase: (caseId: string) => void }) {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<SortKey>("band");
  const [stateFilter, setStateFilter] = useState("all");
  const [bandFilter, setBandFilter] = useState<BandFilter>("all");

  const rows = useMemo(() => {
    if (response.state === "error") return [];
    const needle = q.trim().toLowerCase();
    let list = response.items;
    if (needle) {
      list = list.filter(
        (c) =>
          c.student_ref.toLowerCase().includes(needle) ||
          c.case_id.toLowerCase().includes(needle) ||
          c.contributing_factors.some(
            (factor) =>
              factor.code.toLowerCase().includes(needle) ||
              (FACTOR_LABEL[factor.code] ?? "").toLowerCase().includes(needle),
          ),
      );
    }
    if (stateFilter !== "all") list = list.filter((c) => c.case_state === stateFilter);
    if (bandFilter === "unassigned") list = list.filter((c) => c.review_priority_band === null);
    else if (bandFilter !== "all") list = list.filter((c) => c.review_priority_band === bandFilter);

    const bandRank = (c: ReviewCase) => (c.review_priority_band === "uu_tien_som" ? 0 : c.review_priority_band === "can_ra_soat" ? 1 : 2);
    switch (sort) {
      case "ref": return [...list].sort((a, b) => a.student_ref.localeCompare(b.student_ref));
      case "state": return [...list].sort((a, b) => a.case_state.localeCompare(b.case_state));
      case "newest": return [...list].sort((a, b) => b.calculated_at.localeCompare(a.calculated_at));
      default: return [...list].sort((a, b) => bandRank(a) - bandRank(b) || b.calculated_at.localeCompare(a.calculated_at));
    }
  }, [bandFilter, q, response, sort, stateFilter]);

  if (response.state === "error") {
    return <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">Không tải được danh sách rà soát — máy chủ tạm thời không phản hồi.</div>;
  }
  if (response.state === "empty") {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-600 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-800">Chưa có case cần rà soát</h2>
        <p className="mt-1 text-sm text-slate-400">Không có case không đồng nghĩa mọi sinh viên đều ổn định — cần đọc cùng độ phủ dữ liệu.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-slate-800">Danh sách rà soát</h2>
        <p className="mt-1 text-sm text-slate-500">Mỗi dòng là một case; dùng bộ lọc để tập trung vào việc cần xử lý.</p>
      </div>

      {response.state === "stale" && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700">
          Dữ liệu có thể đã cũ — danh sách vẫn hiển thị nhưng không được coi là mới nhất.
        </div>
      )}

      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-[minmax(240px,1fr)_180px_180px_180px_auto] lg:items-center">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Tìm mã SV, case hoặc yếu tố…"
          aria-label="Tìm trong danh sách rà soát"
          className="h-11 min-w-0 rounded-lg border border-slate-200 bg-slate-50 px-4 text-sm outline-none transition-all focus:border-red-300 focus:ring-2 focus:ring-red-100"
        />
        <select
          value={bandFilter}
          onChange={(e) => setBandFilter(e.target.value as BandFilter)}
          className="h-11 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-600 outline-none focus:ring-2 focus:ring-red-100"
          aria-label="Lọc theo mức ưu tiên"
        >
          <option value="all">Mọi mức ưu tiên</option>
          <option value="uu_tien_som">{BAND_LABEL.uu_tien_som}</option>
          <option value="can_ra_soat">{BAND_LABEL.can_ra_soat}</option>
          <option value="unassigned">Chưa phân bổ</option>
        </select>
        <select
          value={stateFilter}
          onChange={(e) => setStateFilter(e.target.value)}
          className="h-11 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-600 outline-none focus:ring-2 focus:ring-red-100"
          aria-label="Lọc theo trạng thái case"
        >
          <option value="all">Mọi trạng thái</option>
          {Object.entries(CASE_STATE_LABEL).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as SortKey)}
          className="h-11 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-600 outline-none focus:ring-2 focus:ring-red-100"
          aria-label="Sắp xếp danh sách"
        >
          <option value="band">Ưu tiên trước</option>
          <option value="newest">Cập nhật mới nhất</option>
          <option value="ref">Mã SV (A → Z)</option>
          <option value="state">Trạng thái case</option>
        </select>
        <span className="whitespace-nowrap text-right text-sm text-slate-400">{rows.length} case</span>
      </div>

      {rows.length === 0 ? (
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 text-center text-sm text-slate-600">Không có case nào khớp bộ lọc.</div>
      ) : (
        <CaseRowsTable items={rows} onOpenCase={onOpenCase} />
      )}

      <p className="text-xs text-slate-400">
        Danh sách chỉ gồm case do API trả về, không phải toàn bộ sinh viên. Mã sinh viên là pseudonym; không hiển thị điểm số nội bộ.
      </p>
    </div>
  );
}

/* ================= Reusable UI ================= */

function CaseRowsTable({ items, onOpenCase }: { items: ReviewCase[]; onOpenCase: (caseId: string) => void }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[940px] border-collapse text-left">
          <thead>
            <tr className="bg-slate-50/50 border-b border-slate-200">
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Mã SV</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Mức ưu tiên rà soát</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Trạng thái</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Yếu tố chính</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Dữ liệu</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Cập nhật</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => {
              const factorLabels = c.contributing_factors.map((factor) => FACTOR_LABEL[factor.code] ?? factor.code);
              const limited = c.data_state !== "ok" || c.limitations.length > 0;
              return (
                <tr
                  key={c.case_id}
                  onClick={() => onOpenCase(c.case_id)}
                  title="Mở chi tiết case"
                  className="cursor-pointer border-b border-slate-100 transition-colors last:border-0 hover:bg-slate-50/70"
                >
                  <td className="p-4">
                    <span className="block text-sm font-semibold text-[#dc2626]">{c.student_ref}</span>
                    <span className="mt-0.5 block text-[11px] text-slate-400">{c.case_id}</span>
                  </td>
                  <td className="p-4"><BandBadge band={c.review_priority_band} /></td>
                  <td className="p-4"><CaseStateBadge state={c.case_state} /></td>
                  <td className="max-w-[280px] p-4 text-sm text-slate-600">
                    <span>{factorLabels[0] ?? "—"}</span>
                    {factorLabels.length > 1 && <span className="ml-1 text-xs text-slate-400">+{factorLabels.length - 1}</span>}
                  </td>
                  <td className="p-4">
                    <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${limited ? "border-amber-200 bg-amber-50 text-amber-700" : "border-emerald-200 bg-emerald-50 text-emerald-700"}`}>
                      {limited ? "Dữ liệu hạn chế" : "Đủ căn cứ"}
                    </span>
                  </td>
                  <td className="p-4 text-sm tabular-nums text-slate-400">{new Date(c.calculated_at).toLocaleDateString("vi-VN")}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function KpiCard({ label, value, sub, icon, color }: { label: string; value: number; sub: string; icon: string; color: "red" | "amber" | "slate" | "emerald" }) {
  const colors = {
    red: "bg-[#fee2e2] text-[#dc2626]",
    amber: "bg-amber-50 text-amber-600",
    slate: "bg-slate-100 text-slate-600",
    emerald: "bg-emerald-50 text-emerald-600",
  };
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5">
      <div className="flex items-center gap-2.5 mb-4">
        <div className={`p-2 rounded-lg ${colors[color]}`}>
          <Icon path={icon} className="w-4 h-4" />
        </div>
        <span className="text-sm text-slate-500">{label}</span>
      </div>
      <div className="text-4xl font-bold text-slate-800 tracking-tight">{value}</div>
      <div className="text-xs text-slate-400 mt-2">{sub}</div>
    </div>
  );
}

function ChartHeader({ title, subtitle, icon }: { title: string; subtitle: string; icon: string }) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <div className="p-2 bg-slate-50 rounded-lg text-slate-400">
        <Icon path={icon} className="w-4 h-4" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
        <p className="text-xs text-slate-400">{subtitle}</p>
      </div>
    </div>
  );
}

/**
 * Bar chart ngang, nominal một màu (giá trị đã nằm ở độ dài bar — không tô mỗi hạng mục
 * một màu). Nhãn + số luôn hiển thị bằng text token; bar ≤24px, bo tròn đầu dữ liệu.
 */
function BarRows({ rows, color }: { rows: { label: string; value: number }[]; color: string }) {
  const max = Math.max(...rows.map((r) => r.value), 1);
  if (rows.length === 0 || rows.every((r) => r.value === 0)) {
    return <div className="text-sm text-slate-400 italic py-4 text-center">Chưa có dữ liệu.</div>;
  }
  return (
    <div className="space-y-3">
      {rows.map((r) => (
        <div key={r.label} className="flex items-center gap-3" title={`${r.label}: ${r.value}`}>
          <span className="w-36 text-sm text-slate-600 truncate shrink-0">{r.label}</span>
          <div className="flex-1 h-5 bg-slate-50 rounded-r">
            <div
              className="h-full rounded-r"
              style={{ width: `${Math.max((r.value / max) * 100, r.value > 0 ? 3 : 0)}%`, backgroundColor: color }}
            />
          </div>
          <span className="w-8 text-right text-sm font-semibold text-slate-800 tabular-nums shrink-0">{r.value}</span>
        </div>
      ))}
    </div>
  );
}

function ListSkeleton({ compact = false }: { compact?: boolean }) {
  if (compact) {
    return (
      <div className="space-y-4" aria-busy="true" aria-label="Đang tải danh sách rà soát">
        <div className="h-20 animate-pulse rounded-2xl bg-slate-100" />
        <div className="h-80 animate-pulse rounded-2xl bg-slate-100" />
      </div>
    );
  }
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Đang tải">
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-5">
        <div className="h-64 animate-pulse rounded-2xl bg-slate-100 lg:col-span-3" />
        <div className="grid gap-5 lg:col-span-2">
          {[1, 2].map((i) => <div key={i} className="h-[118px] animate-pulse rounded-2xl bg-slate-100" />)}
        </div>
      </div>
      <div className="h-64 animate-pulse rounded-2xl bg-slate-100" />
    </div>
  );
}

/* ================= Icons (Lucide-style paths) ================= */

const iconPaths: Record<string, string> = {
  shield: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
  check: "M20 6L9 17l-5-5",
  activity: "M22 12h-4l-3 9L9 3l-3 9H2",
  sparkles: "M12 3l1.9 5.8a2 2 0 001.3 1.3L21 12l-5.8 1.9a2 2 0 00-1.3 1.3L12 21l-1.9-5.8a2 2 0 00-1.3-1.3L3 12l5.8-1.9a2 2 0 001.3-1.3L12 3z",
  clock: "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zM12 6v6l4 2",
  users: "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2 M9 11a4 4 0 100-8 4 4 0 000 8z M23 21v-2a4 4 0 00-3-3.87 M16 3.13a4 4 0 010 7.75",
  scale: "M12 3v18 M7 21h10 M5 7l14 0 M5 7l-3 7h6l-3-7zM19 7l-3 7h6l-3-7z",
  heart: "M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z",
  chart: "M3 3v18h18 M7 14l4-4 4 4 5-5",
  arrowRight: "M5 12h14 M12 5l7 7-7 7",
  sliders: "M4 21v-7 M4 10V3 M12 21v-9 M12 8V3 M20 21v-5 M20 12V3 M2 14h4 M10 8h4 M18 16h4",
  fileText: "M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8",
  search: "M11 19a8 8 0 100-16 8 8 0 000 16z M21 21l-4.35-4.35",
  mail: "M4 4h16a2 2 0 012 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V6a2 2 0 012-2z M22 6l-10 7L2 6",
};

function Icon({ path, className }: { path: string; className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d={path} />
    </svg>
  );
}
