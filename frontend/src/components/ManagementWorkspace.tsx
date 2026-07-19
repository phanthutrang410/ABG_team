"use client";

import { Suspense, useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AppShell, useSetTopbarInfo, type TopbarNotification } from "@/components/AppShell";
import { AIThinkingOverlay } from "@/components/AIThinkingOverlay";
import { BandBadge, CaseStateBadge } from "@/components/badges";
import { CaseDetailDialog } from "@/components/CaseDetailPage";
import { QueuePagination } from "@/components/QueuePagination";
import { useGlobalAgent } from "@/components/GlobalAgentProvider";
import { ReportModal } from "@/components/ReportModal";
import { ThresholdPanel } from "@/components/ThresholdPanel";
import { fetchReviewCases, fetchReviewOverviewSummary } from "@/lib/api";
import { OVERVIEW_REPORT_QUERY, OVERVIEW_REPORT_VALUE } from "@/lib/agent-routes";
import { FACTOR_LABEL } from "@/lib/factors";
import { splitAccountName, useSession } from "@/lib/session";
import {
  BAND_LABEL,
  CASE_STATE_LABEL,
  type CaseListResponse,
  type ReviewCase,
  type ReviewOverviewSummary,
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
  const [summary, setSummary] = useState<ReviewOverviewSummary | null>(null);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const activeLoadRef = useRef<AbortController | null>(null);

  const load = useCallback(() => {
    activeLoadRef.current?.abort();
    setLoading(true);
    const controller = new AbortController();
    activeLoadRef.current = controller;
    Promise.all([
      fetchReviewCases(controller.signal),
      isAnalysisRoute
        ? Promise.resolve<ReviewOverviewSummary | null>(null)
        : fetchReviewOverviewSummary(controller.signal),
    ]).then(([caseResponse, overviewSummary]) => {
      // Route changes and React Strict Mode abort the superseded request. The
      // fetch client maps transport failures to a fail-closed error envelope,
      // so never let that obsolete envelope replace the request still running.
      if (controller.signal.aborted || activeLoadRef.current !== controller) return;
      setResponse(caseResponse);
      setSummary(overviewSummary);
      setLoading(false);
      activeLoadRef.current = null;
    });
    return controller;
  }, [isAnalysisRoute]);

  useEffect(() => {
    const controller = load();
    return () => controller.abort();
  }, [load]);

  const openCase = useCallback((id: string) => setSelectedCaseId(id), []);
  const handleCaseStateChange = useCallback((caseId: string, next: ReviewCase["case_state"]) => {
    setResponse((previous) => previous
      ? {
          ...previous,
          items: previous.items.map((item) =>
            item.case_id === caseId ? { ...item, case_state: next } : item,
          ),
        }
      : previous,
    );
  }, []);

  // Tổng quan dùng freshness của nguồn roster; trang phân tích chưa cần summary
  // nên tiếp tục dùng calculated_at của review queue.
  const topInfo = useMemo(() => {
    const items = response?.items ?? [];
    const latestCaseAt = items.reduce((m, c) => (c.calculated_at > m ? c.calculated_at : m), "");
    const updatedAt = summary?.source_extracted_at ?? latestCaseAt;
    const alertCount = summary?.priority_band_counts.uu_tien_som
      ?? items.filter((c) => c.review_priority_band === "uu_tien_som").length;
    return { updatedAt: updatedAt || null, alertCount };
  }, [response, summary]);

  // Thông báo cho chuông topbar — hiển thị ở MỌI trang management. Ưu tiên summary
  // (Tổng quan); trang /analysis không fetch summary nên suy số liệu từ danh sách case.
  const notifications = useMemo<TopbarNotification[]>(() => {
    const reviewsHref = "/analysis?tab=reviews";
    let reviewStudents: number;
    let early: number;
    let newSignal: number;
    let pending: number;
    let active: number;
    if (summary && summary.state !== "error") {
      reviewStudents = summary.review_student_count;
      early = summary.priority_band_counts.uu_tien_som;
      newSignal = summary.case_state_counts.new_signal;
      pending = summary.case_state_counts.pending_review;
      active =
        summary.case_state_counts.assigned
        + summary.case_state_counts.follow_up_in_progress
        + summary.case_state_counts.monitoring;
    } else if (response && response.state !== "error") {
      const items = response.items;
      reviewStudents = new Set(items.map((c) => c.student_ref)).size;
      early = items.filter((c) => c.review_priority_band === "uu_tien_som").length;
      newSignal = items.filter((c) => c.case_state === "new_signal").length;
      pending = items.filter((c) => c.case_state === "pending_review").length;
      active = items.filter((c) => c.case_state === "assigned" || c.case_state === "follow_up_in_progress" || c.case_state === "monitoring").length;
    } else {
      return [];
    }
    const list: TopbarNotification[] = [];
    if (reviewStudents > 0) list.push({ key: "students", count: reviewStudents, label: "sinh viên có tín hiệu cần rà soát", href: reviewsHref });
    if (early > 0) list.push({ key: "early", count: early, label: "case ở mức ưu tiên sớm", href: `${reviewsHref}&band=uu_tien_som` });
    if (newSignal > 0) list.push({ key: "new", count: newSignal, label: "case ở trạng thái tín hiệu mới", href: `${reviewsHref}&state=new_signal` });
    if (pending > 0) list.push({ key: "pending", count: pending, label: "case đang chờ duyệt", href: `${reviewsHref}&state=pending_review` });
    if (active > 0) list.push({ key: "active", count: active, label: "case đang theo dõi / hỗ trợ", href: reviewsHref });
    return list;
  }, [summary, response]);
  useSetTopbarInfo(topInfo.updatedAt, topInfo.alertCount, notifications);

  return (
    <div className={tab === "analytics" ? "space-y-3" : "space-y-6"}>
      <AIThinkingOverlay visible={loading} />
      {isAnalysisRoute && <AnalysisTabs active={analysisTab} onChange={(next) => setTab(next === "dashboard" ? "analytics" : next)} />}
      {/* Khối "Phạm vi MVP" (ScopeBanner/H12b) đã bỏ theo yêu cầu owner 18/7 —
          copy giới hạn phạm vi còn lại ở disclaimer đầu trang + chip cam kết trong hero. */}
      {tab === "reviews" && (
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
        <OverviewHeader
          loading={loading}
          response={response}
          summary={summary}
          onReload={load}
          onOpenCase={openCase}
        />
      )}
      {tab === "analytics" && (
        <AnalyticsTab loading={loading} response={response} setTab={setTab} onReload={load} />
      )}
      {tab === "reviews" && (
        loading && !response ? <ListSkeleton compact /> : response ? <ReviewList response={response} onOpenCase={openCase} initialBand={searchParams.get("band")} initialStateFilter={searchParams.get("state")} /> : null
      )}
      {tab === "threshold" && <ThresholdPanel />}

      {/* Ẩn ở Tổng quan để khu AI phủ trọn màn hình */}
      {tab !== "overview" && (
        <p className="text-xs text-slate-400">
          Dữ liệu và hành động đi thẳng API — không hiển thị điểm số nội bộ của model.
          Scoping theo khoa/lớp và danh sách toàn bộ SV chờ API bổ sung (design spec §9).
        </p>
      )}

      {selectedCaseId && (
        <CaseDetailDialog
          caseId={selectedCaseId}
          onClose={() => setSelectedCaseId(null)}
          onCaseStateChange={handleCaseStateChange}
        />
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
  summary,
  onReload,
  onOpenCase,
}: {
  loading: boolean;
  response: CaseListResponse | null;
  summary: ReviewOverviewSummary | null;
  onReload: () => void;
  onOpenCase: (caseId: string) => void;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { account } = useSession();
  const { name: shortName } = splitAccountName(account?.name ?? "thầy/cô");
  const items = useMemo(() => (response && response.state !== "error" ? response.items : []), [response]);
  // Tool 1 — modal "Báo cáo tổng thể"; also opened via agent route_key overview.report (?report=1).
  const [reportOpen, setReportOpen] = useState(false);
  // 3 tool gợi ý chỉ hiện khi bấm "Xem chi tiết gợi ý" (xuất hiện lần lượt bên phải).
  const [showTools, setShowTools] = useState(false);

  useEffect(() => {
    if (searchParams.get(OVERVIEW_REPORT_QUERY) !== OVERVIEW_REPORT_VALUE) return;
    setReportOpen(true);
    router.replace("/overview", { scroll: false });
  }, [searchParams, router]);

  // Fetch đang chạy thật → hiển thị trạng thái "đang phân tích" (không phải hiệu ứng giả).
  if (loading && (!response || !summary)) {
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
  if (!response || !summary) return <ErrorCard onReload={onReload} />;
  if (response.state === "error" || summary.state === "error") return <ErrorCard onReload={onReload} />;

  // Một thông báo duy nhất: denominator và aggregate lấy từ summary backend,
  // không suy ra roster từ review queue và không biến workflow state thành delta.
  const isStale = response.state === "stale" || summary.state === "stale";
  const overviewCounts: OverviewCounts = {
    totalStudents: summary.total_students,
    reviewCases: summary.review_case_count,
    reviewStudents: summary.review_student_count,
    workflowNew: summary.case_state_counts.new_signal,
    pending: summary.case_state_counts.pending_review,
    active:
      summary.case_state_counts.assigned
      + summary.case_state_counts.follow_up_in_progress
      + summary.case_state_counts.monitoring,
    earlyPriority: summary.priority_band_counts.uu_tien_som,
    limitedStudents: summary.limited_student_count,
    limitedReviewCases: summary.limited_review_case_count,
  };
  // Số liệu nổi bật cho bản tin gọn — mỗi mục 1 badge THIẾT KẾ ĐẶC TRƯNG theo ý
  // nghĩa (màu + icon riêng). Fail-closed: chỉ đẩy mục > 0. Mọi số từ summary backend.
  // Mỗi badge bấm được → mở danh sách rà soát đã lọc đúng loại (drill-down).
  const stats: { value: number; label: string; box: string; num: string; icon: string; href: string }[] = [
    { value: overviewCounts.reviewCases, label: "case rà soát", box: "border-rose-200 bg-rose-50", num: "text-rose-600", icon: iconPaths.search, href: "/analysis?tab=reviews" },
  ];
  if (overviewCounts.earlyPriority > 0) stats.push({ value: overviewCounts.earlyPriority, label: "ưu tiên sớm", box: "border-red-300 bg-red-100", num: "text-red-700", icon: iconPaths.alert, href: "/analysis?tab=reviews&band=uu_tien_som" });
  if (overviewCounts.workflowNew > 0) stats.push({ value: overviewCounts.workflowNew, label: "tín hiệu mới", box: "border-amber-200 bg-amber-50", num: "text-amber-600", icon: iconPaths.activity, href: "/analysis?tab=reviews&state=new_signal" });
  if (overviewCounts.active > 0) stats.push({ value: overviewCounts.active, label: "đang theo dõi / hỗ trợ", box: "border-emerald-200 bg-emerald-50", num: "text-emerald-600", icon: iconPaths.heart, href: "/analysis?tab=reviews" });

  // 3 tool của EduSignal AI (plan.md §3.2). Các tool chỉ điều hướng tới route
  // đã có thật; trang Tổng quan không tự tính thêm band hay dữ liệu sinh viên.
  const tools: OverviewTool[] = [
    {
      key: "report",
      icon: iconPaths.fileText,
      title: "Xuất báo cáo tổng thể",
      desc: `${overviewCounts.active} case đang theo dõi · ${overviewCounts.reviewCases} case rà soát — xem, in / lưu PDF`,
      gradient: "from-[#dc2626] to-[#fb923c]",
      glow: "shadow-red-500/40",
      onClick: () => setReportOpen(true),
    },
    {
      key: "analyze",
      icon: iconPaths.search,
      title: "Danh sách rà soát",
      desc: `${overviewCounts.reviewCases} case của ${overviewCounts.reviewStudents} sinh viên trên tổng ${overviewCounts.totalStudents}`,
      gradient: "from-emerald-500 to-teal-400",
      glow: "shadow-emerald-500/40",
      onClick: () => router.push("/analysis?tab=reviews"),
    },
    {
      key: "notify",
      icon: iconPaths.mail,
      title: "Soạn mail cho GVCN",
      desc: "Lọc sinh viên theo giảng viên phụ trách và xem bản nháp mail bàn giao",
      gradient: "from-sky-500 to-indigo-500",
      glow: "shadow-sky-500/40",
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
          <p className="mt-2 text-slate-500 text-base md:text-lg">
            Chúc thầy/cô một ngày làm việc hiệu quả. EduSignal đã tải bản tổng hợp từ snapshot được phê duyệt.
          </p>
          <p className="mt-1 text-slate-400 text-sm md:text-base">
            Hệ thống <strong className="font-semibold text-slate-600">chỉ gợi ý</strong> — mọi quyết định do thầy/cô thực hiện.
          </p>
        </div>
        {summary.source_extracted_at && (
          <span className="inline-flex items-center gap-2 self-start bg-white/80 border border-emerald-100 rounded-full px-4 py-2 shadow-sm shrink-0">
            <span className="ss-live-dot w-2 h-2 rounded-full bg-emerald-500 inline-block" aria-hidden />
            <span className="text-xs text-slate-600">
              <strong className="font-semibold text-emerald-600">EduSignal AI</strong> · Nguồn dữ liệu được trích xuất lúc {formatAnalyzedAt(summary.source_extracted_at)}
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
        <div className="flex-1 min-w-0 max-w-3xl space-y-4">
          <div className="relative">
            <div className="ss-glow absolute -inset-2 rounded-[28px] bg-[#dc2626]/10 blur-xl" aria-hidden />
            <div className="relative bg-white rounded-3xl rounded-tl-lg border-2 border-[#f6bcbc] shadow-xl shadow-red-900/10 px-7 py-6">
              {/* Đuôi bong bóng trỏ lên robot khi xếp dọc (mobile) */}
              <div className="lg:hidden absolute -top-[11px] left-12 w-5 h-5 bg-white border-l-2 border-t-2 border-[#f6bcbc] rotate-45" aria-hidden />
              <p className="inline-flex items-center gap-1.5 bg-gradient-to-r from-[#dc2626] to-[#ef4444] text-white text-xs font-bold rounded-full px-3.5 py-1.5 shadow-md shadow-red-600/30">
                <Icon path={iconPaths.sparkles} className="w-3.5 h-3.5 animate-pulse" /> EduSignal AI
              </p>
              <p className="text-2xl md:text-3xl font-bold text-slate-800 mt-3">Xin chào {shortName} 👋</p>
              {/* Bản tin gọn: mỗi số liệu là 1 badge đặc trưng (màu + icon riêng); mọi số từ response */}
              {overviewCounts.totalStudents > 0 ? (
                <div className="mt-3 flex flex-wrap items-center gap-2.5 text-base md:text-lg text-slate-600">
                  <span className="font-semibold text-slate-700">Tuần vừa qua:</span>
                  {stats.map((s) => (
                    <button
                      key={s.label}
                      type="button"
                      onClick={() => router.push(s.href)}
                      title={`Mở danh sách rà soát — ${s.label}`}
                      className={`group inline-flex items-center gap-2 rounded-xl border px-3.5 py-2 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md ${s.box}`}
                    >
                      <Icon path={s.icon} className={`h-5 w-5 ${s.num}`} />
                      <strong className={`text-3xl font-extrabold leading-none tabular-nums ${s.num}`}>{s.value}</strong>
                      <span className="text-xs font-medium text-slate-500">{s.label}</span>
                      <Icon path={iconPaths.arrowRight} className={`-ml-1 h-4 w-4 opacity-0 transition-all group-hover:translate-x-0.5 group-hover:opacity-100 ${s.num}`} />
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-base text-slate-500 mt-1.5">
                  Snapshot hiện không có sinh viên để tổng hợp. Hệ thống không suy diễn số liệu thay thế.
                </p>
              )}
              {isStale && (
                <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
                  Snapshot có thể đã cũ — số liệu trên không được coi là mới nhất.
                </p>
              )}
              <button
                onClick={() => setShowTools((v) => !v)}
                aria-expanded={showTools}
                className="mt-5 inline-flex items-center gap-2 bg-[#dc2626] hover:bg-[#b91c1c] text-white font-semibold text-base rounded-xl px-5 py-3 shadow-md shadow-red-600/25 transition-colors"
              >
                {showTools ? "Ẩn gợi ý" : "Xem chi tiết gợi ý"}
                <Icon path={iconPaths.arrowRight} className={`w-4 h-4 transition-transform ${showTools ? "rotate-90" : ""}`} />
              </button>
            </div>
          </div>

          {/* Launcher — mở Global Agent drawer (POST /agent/turns); 3 tool cards bên dưới vẫn click-navigate trực tiếp */}
          <AiAgentLauncher />
        </div>
      </div>

      {/* 3 tool gợi ý — chỉ hiện khi bấm "Xem chi tiết gợi ý"; xuất hiện lần lượt
          (staggered). Desktop: cột dọc bên phải phủ vùng watermark shield.
          Mobile/tablet: xếp dọc dưới khu chat. Mỗi tool dẫn sang route có thật. */}
      {showTools && (
        <>
          <div className="hidden xl:flex absolute right-10 2xl:right-16 top-40 bottom-24 z-20 w-64 flex-col justify-between">
            {tools.map((t, i) => (
              <ToolCard key={t.key} tool={t} className="ss-tool-in" style={{ animationDelay: `${i * 0.14}s` }} />
            ))}
          </div>
          <div className="xl:hidden relative z-10 grid gap-3 sm:grid-cols-3">
            {tools.map((t, i) => (
              <ToolCard key={t.key} tool={t} className="ss-tool-in" style={{ animationDelay: `${i * 0.14}s` }} />
            ))}
          </div>
        </>
      )}

      {/* Tool 1 — Báo cáo tổng thể (in / lưu PDF tại chỗ) */}
      {reportOpen && (
        <ReportModal
          items={items}
          onClose={() => setReportOpen(false)}
          onOpenCase={(caseId) => {
            setReportOpen(false);
            onOpenCase(caseId);
          }}
        />
      )}
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

/* ---------- Launcher mở Global Agent drawer (thay mock AiQuickChat) ---------- */

type OverviewCounts = {
  totalStudents: number;
  reviewCases: number;
  reviewStudents: number;
  workflowNew: number;
  pending: number;
  active: number;
  earlyPriority: number;
  limitedStudents: number;
  limitedReviewCases: number;
};

/* 3 tool gợi ý của EduSignal AI (Tổng quan). */
type OverviewTool = {
  key: string;
  icon: string;
  title: string;
  desc: string;
  gradient: string; // nền gradient sáng chói riêng cho từng tool
  glow: string; // màu đổ bóng phát sáng
  onClick?: () => void;
  disabled?: boolean;
};

/** Thẻ tool "sáng chói" — nền gradient + glow, đọc rõ là công cụ hành động chứ không phải chip thông tin. */
function ToolCard({ tool, className, style }: { tool: OverviewTool; className?: string; style?: CSSProperties }) {
  return (
    <button
      onClick={tool.onClick}
      disabled={tool.disabled}
      title={tool.desc}
      style={style}
      className={`group relative flex w-full items-center gap-3 overflow-hidden rounded-2xl bg-gradient-to-br ${tool.gradient} px-4 py-3.5 text-left text-white shadow-xl ${tool.glow} ring-1 ring-white/40 transition-all duration-200 hover:-translate-y-1 hover:shadow-2xl disabled:cursor-not-allowed disabled:opacity-60 ${className ?? ""}`}
    >
      {/* đốm sáng góc + lớp loé khi hover cho cảm giác "sáng chói" */}
      <span aria-hidden className="absolute -right-8 -top-10 h-24 w-24 rounded-full bg-white/25 blur-2xl" />
      <span aria-hidden className="absolute inset-0 bg-white/0 transition-colors duration-200 group-hover:bg-white/10" />
      <span className="relative flex shrink-0 items-center justify-center rounded-xl bg-white/25 p-2.5 shadow-inner backdrop-blur">
        <Icon path={tool.icon} className="h-5 w-5" />
      </span>
      <span className="relative min-w-0 flex-1">
        <span className="block text-sm font-bold">{tool.title}</span>
        <span className="mt-0.5 block text-xs leading-snug text-white/85">{tool.desc}</span>
      </span>
      <Icon path={iconPaths.arrowRight} className="relative h-4 w-4 shrink-0 text-white/80 transition-transform group-hover:translate-x-1" />
    </button>
  );
}

function AiAgentLauncher() {
  const { openDrawer, launcherRef, busy } = useGlobalAgent();

  return (
    <div className="space-y-3">
      <button
        type="button"
        ref={(el) => {
          launcherRef.current = el;
        }}
        onClick={openDrawer}
        disabled={busy}
        className="w-full flex items-center gap-3 bg-white border border-[#fbd7d7] rounded-full pl-5 pr-2 py-2 shadow-sm hover:border-[#dc2626] transition-colors text-left"
        aria-label="Hỏi EduSignal AI"
      >
        <span className="text-base shrink-0" aria-hidden>🤖</span>
        <span className="flex-1 min-w-0 text-sm text-slate-400">
          Hỏi EduSignal AI… (vd: mở báo cáo, danh sách rà soát, soạn mail)
        </span>
        <span
          className="shrink-0 h-9 px-4 rounded-full bg-[#dc2626] hover:bg-[#b91c1c] text-white text-sm font-semibold flex items-center justify-center transition-colors"
        >
          Hỏi
        </span>
      </button>
      <p className="text-[11px] text-slate-400 pl-2">
        Trợ lý AI chỉ giải thích và điều hướng trong phạm vi được cấp — không chẩn đoán, không tự gửi.
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

  if (loading && !response) return <ListSkeleton />;
  if (!response) return null;
  if (response.state === "error") return <ErrorCard onReload={onReload} />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">Dashboard</h1>
          <p className="mt-0.5 text-base text-slate-500">Tập trung vào tín hiệu cần rà soát sớm và khối lượng đang chờ xử lý.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={onReload}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-500 transition-colors hover:border-slate-300"
          >
            ↻ Tải lại dữ liệu
          </button>
          <button
            type="button"
            onClick={() => setTab("reviews")}
            className="inline-flex items-center gap-2 rounded-xl bg-[#dc2626] px-4 py-2 text-base font-semibold text-white shadow-sm shadow-red-600/20 transition-colors hover:bg-[#b91c1c]"
          >
            Mở danh sách rà soát
            <Icon path={iconPaths.arrowRight} className="h-4 w-4" />
          </button>
        </div>
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
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
            <section className="relative overflow-hidden rounded-2xl border border-red-200 bg-gradient-to-br from-red-50 via-white to-white p-5 shadow-sm lg:col-span-3">
              <div className="absolute -right-10 -top-14 h-36 w-36 rounded-full bg-red-100/60" aria-hidden />
              <div className="relative">
                <div className="flex items-center gap-2.5 text-base font-semibold text-red-700">
                  <span className="rounded-lg bg-red-100 p-2"><Icon path={iconPaths.sparkles} className="h-5 w-5" /></span>
                  Tín hiệu cần rà soát sớm
                </div>
                <p className="mt-3 text-7xl font-bold tracking-tight text-slate-900 tabular-nums">{counts.earlyPriority}</p>
                <p className="mt-1 text-base text-slate-500">trên {counts.total} case của {counts.students} sinh viên trong lần tracking hiện tại</p>
                <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 border-t border-red-100 pt-3 text-sm text-slate-500">
                  <span>{counts.limitedData} case có dữ liệu hạn chế</span>
                  <span>Chưa có API lịch sử để tính chênh lệch với lần trước</span>
                </div>
              </div>
            </section>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:col-span-2 lg:grid-cols-1">
              <KpiCard
                label="Trạng thái Tín hiệu mới"
                value={counts.newSignals}
                sub={counts.newEarly > 0 ? `${counts.newEarly} case ở mức Ưu tiên sớm` : "case đang ở bước đầu workflow"}
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
          <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
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

function ReviewList({
  response,
  onOpenCase,
  initialBand,
  initialStateFilter,
}: {
  response: CaseListResponse;
  onOpenCase: (caseId: string) => void;
  initialBand?: string | null;
  initialStateFilter?: string | null;
}) {
  const toBand = (b: string | null | undefined): BandFilter =>
    b === "uu_tien_som" || b === "can_ra_soat" || b === "unassigned" ? b : "all";
  const toState = (s: string | null | undefined): string => (s && s in CASE_STATE_LABEL ? s : "all");

  const [q, setQ] = useState("");
  const [sort, setSort] = useState<SortKey>("band");
  const [stateFilter, setStateFilter] = useState(() => toState(initialStateFilter));
  const [bandFilter, setBandFilter] = useState<BandFilter>(() => toBand(initialBand));

  const [page, setPage] = useState(1);

  // Đồng bộ khi mở từ badge Tổng quan (URL đổi mà component vẫn mounted).
  useEffect(() => { setBandFilter(toBand(initialBand)); }, [initialBand]);
  useEffect(() => { setStateFilter(toState(initialStateFilter)); }, [initialStateFilter]);

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

  // Phân trang 10 dòng/trang. Về trang 1 khi tìm/lọc/sắp xếp đổi.
  const PAGE_SIZE = 10;
  const total = rows.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const start = (safePage - 1) * PAGE_SIZE;
  const end = Math.min(start + PAGE_SIZE, total);
  const pageRows = rows.slice(start, end);
  useEffect(() => { setPage(1); }, [q, sort, stateFilter, bandFilter]);

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
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <CaseRowsTable items={pageRows} onOpenCase={onOpenCase} />
          <QueuePagination
            start={start}
            end={end}
            total={total}
            page={safePage}
            totalPages={totalPages}
            noun="case"
            onChange={setPage}
          />
        </div>
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
    <div className="overflow-x-auto">
      <table className="w-full min-w-[820px] border-collapse text-left">
          <thead>
            <tr className="bg-slate-50/50 border-b border-slate-200">
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Mã SV</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Mức ưu tiên rà soát</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Trạng thái</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Yếu tố chính</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Cập nhật</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => {
              const factorLabels = c.contributing_factors.map((factor) => FACTOR_LABEL[factor.code] ?? factor.code);
              return (
                <tr
                  key={c.case_id}
                  onClick={() => onOpenCase(c.case_id)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onOpenCase(c.case_id);
                    }
                  }}
                  tabIndex={0}
                  aria-label={`Mở chi tiết case ${c.case_id} của ${c.student_ref}`}
                  title="Mở chi tiết case"
                  className="cursor-pointer border-b border-slate-100 transition-colors last:border-0 hover:bg-red-50/40 focus:bg-red-50/40 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-red-300"
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
                  <td className="p-4 text-sm tabular-nums text-slate-400">{new Date(c.calculated_at).toLocaleDateString("vi-VN")}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
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
    <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5">
      <div className="mb-2 flex items-center gap-2.5">
        <div className={`p-2 rounded-lg ${colors[color]}`}>
          <Icon path={icon} className="h-5 w-5" />
        </div>
        <span className="text-base font-medium text-slate-600">{label}</span>
      </div>
      <div className="text-5xl font-bold tracking-tight text-slate-800 tabular-nums">{value}</div>
      <div className="mt-1 text-sm text-slate-500">{sub}</div>
    </div>
  );
}

function ChartHeader({ title, subtitle, icon }: { title: string; subtitle: string; icon: string }) {
  return (
    <div className="mb-3 flex items-center gap-3">
      <div className="p-2 bg-slate-50 rounded-lg text-slate-400">
        <Icon path={icon} className="h-5 w-5" />
      </div>
      <div>
        <h3 className="text-base font-semibold text-slate-800">{title}</h3>
        <p className="text-sm text-slate-500">{subtitle}</p>
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
    <div className="space-y-2">
      {rows.map((r) => (
        <div key={r.label} className="flex items-center gap-3" title={`${r.label}: ${r.value}`}>
          <span className="w-40 shrink-0 truncate text-base text-slate-600">{r.label}</span>
          <div className="flex-1 h-5 bg-slate-50 rounded-r">
            <div
              className="h-full rounded-r"
              style={{ width: `${Math.max((r.value / max) * 100, r.value > 0 ? 3 : 0)}%`, backgroundColor: color }}
            />
          </div>
          <span className="w-8 shrink-0 text-right text-base font-semibold text-slate-800 tabular-nums">{r.value}</span>
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
  alert: "M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z M12 9v4 M12 17h.01",
  info: "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z M12 16v-4 M12 8h.01",
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
