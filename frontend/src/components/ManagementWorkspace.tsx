"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AppShell, useSetTopbarInfo } from "@/components/AppShell";
import { BandBadge, CaseStateBadge } from "@/components/badges";
import { FairnessPanel } from "@/components/FairnessPanel";
import { LimitationsList } from "@/components/LimitationsList";
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
 * /overview là Agent Home; /analysis chứa 5 tab nội bộ theo plan.md §2–3.
 * hero → KPI → charts → việc cần làm → tín hiệu gần đây.
 * Tab Tổng quan = Agent Home (plan.md §3.2): robot + MỘT bản tin duy nhất về kỳ
 * dữ liệu + 3 tool (xuất báo cáo / phân tích SV / soạn mail GVCN — G06 chưa mở).
 * Fail-closed: nguồn lỗi → hiện lỗi, không bịa dữ liệu (mọi số trên trang đều
 * tính từ response — không hardcode đếm/trend/thời gian; không vẽ delta tuần
 * hay sparkline vì chưa có API lịch sử).
 */

type Tab = "overview" | "analytics" | "signals" | "students" | "fairness" | "threshold";
type AnalysisTab = "dashboard" | "signals" | "students" | "fairness" | "threshold";
const ANALYSIS_TAB_IDS: AnalysisTab[] = ["dashboard", "signals", "students", "fairness", "threshold"];

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
  // /analysis dùng đúng 5 tab của plan §3.3; /overview chỉ hiển thị Agent Home.
  const rawTab = searchParams.get("tab");
  const analysisTab = ANALYSIS_TAB_IDS.includes(rawTab as AnalysisTab) ? (rawTab as AnalysisTab) : "dashboard";
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
      {(tab === "analytics" || tab === "signals" || tab === "students") && (
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
        <AnalyticsTab loading={loading} response={response} setTab={setTab} onOpenCase={openCase} onReload={load} />
      )}
      {tab === "signals" && (
        loading ? <ListSkeleton /> : response ? <SignalsList response={response} onOpenCase={openCase} /> : null
      )}
      {tab === "students" && (
        loading ? <ListSkeleton /> : response ? <StudentsTab response={response} onOpenCase={openCase} /> : null
      )}
      {tab === "fairness" && <FairnessPanel />}
      {tab === "threshold" && <ThresholdPanel />}

      {/* Ẩn ở Tổng quan để khu AI phủ trọn màn hình */}
      {tab !== "overview" && (
        <p className="text-xs text-slate-400">
          Dữ liệu và hành động được đồng bộ trực tiếp, không hiển thị điểm số nội bộ của mô hình.
          Phạm vi theo khoa, lớp và danh sách toàn bộ sinh viên đang được hoàn thiện.
        </p>
      )}
    </div>
  );
}

function AnalysisTabs({ active, onChange }: { active: AnalysisTab; onChange: (tab: AnalysisTab) => void }) {
  const tabs: { id: AnalysisTab; label: string }[] = [
    { id: "dashboard", label: "Dashboard" },
    { id: "signals", label: "Tín hiệu" },
    { id: "students", label: "Sinh viên" },
    { id: "fairness", label: "Fairness" },
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
  if (counts.limitedData > 0) segments.push({ strong: `${counts.limitedData} case`, text: "có dữ liệu còn hạn chế; hệ thống chưa đưa ra kết luận" });

  // 3 tool của EduSignal AI (plan.md §3.2). Các tool chỉ điều hướng tới route
  // đã có thật; trang Tổng quan không tự tính thêm band hay dữ liệu sinh viên.
  const watched = items.filter((c) => c.case_state !== "dismissed" && c.case_state !== "resolved");
  const watchStudents = new Set(watched.map((c) => c.student_ref)).size;
  const tools: { key: string; icon: string; title: string; desc: string; accent: string; onClick?: () => void; disabled?: boolean }[] = [
    {
      key: "report",
      icon: iconPaths.fileText,
      title: "Xuất báo cáo tổng thể",
      desc: `${watchStudents} SV trong diện theo dõi · ${counts.newSignals} phát hiện mới · xem, in hoặc lưu PDF`,
      accent: "bg-[#fee2e2] text-[#dc2626]",
      onClick: () => setReportOpen(true),
    },
    {
      key: "analyze",
      icon: iconPaths.search,
      title: "Phân tích sinh viên",
      desc: `${counts.students} sinh viên có tín hiệu · tra cứu mã SV và xem phân tích chi tiết`,
      accent: "bg-emerald-50 text-emerald-600",
      onClick: () => router.push("/analysis?tab=students"),
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
            Hệ thống <strong className="font-semibold text-slate-600">chỉ đưa ra gợi ý</strong>. Mọi quyết định do thầy/cô thực hiện.
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
                  Chưa có tín hiệu mới cần chú ý trong kỳ dữ liệu này. Tôi sẽ tiếp tục theo dõi.
                </p>
              )}
              {isStale && (
                <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
                  Dữ liệu có thể đã cũ. Các số liệu trên không được coi là mới nhất.
                </p>
              )}
              <button
                onClick={() => setTab("signals")}
                className="mt-5 inline-flex items-center gap-2 bg-[#dc2626] hover:bg-[#b91c1c] text-white font-semibold text-sm rounded-xl px-5 py-3 shadow-md shadow-red-600/25 transition-colors"
              >
                Xem chi tiết gợi ý
                <Icon path={iconPaths.arrowRight} className="w-4 h-4" />
              </button>
              {/* Nguồn của bản tin — snapshot/version thật từ response, không suy đoán */}
              {latest && (
                <p className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-400">
                  Cập nhật {formatAnalyzedAt(analyzedAt)} · bộ dữ liệu {latest.dataset_version} · mô hình {latest.model_version}. Bản tin được tổng hợp trực tiếp từ dữ liệu hiện có.
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
      action: { label: "Mở danh sách tín hiệu", tab: "signals" },
    };
  }
  if (has(/tại sao|tai sao|vì sao|vi sao|giải thích|giai thich|ly do|lý do/)) {
    return {
      a: "Lý do gợi ý của từng trường hợp, gồm yếu tố đóng góp và độ phủ dữ liệu, nằm trong trang chi tiết. Mở danh sách tín hiệu và chọn case cần xem.",
      action: { label: "Mở danh sách tín hiệu", tab: "signals" },
    };
  }
  if (has(/mới|moi/)) {
    return {
      a: `Kỳ này có ${c.newSignals} tín hiệu mới${c.newEarly > 0 ? `, trong đó ${c.newEarly} ở mức Ưu tiên sớm` : ""}.`,
      action: { label: "Mở danh sách tín hiệu", tab: "signals" },
    };
  }
  if (has(/duyệt|duyet/)) {
    return {
      a: `Có ${c.pending} case đang chờ duyệt.`,
      action: { label: "Mở danh sách tín hiệu", tab: "signals" },
    };
  }
  if (has(/sinh viên|sinh vien|\bsv\b|lớp|lop/)) {
    const note = has(/lớp|lop/) ? " Chức năng lọc theo lớp và khoa đang được hoàn thiện; hiện có thể tra cứu theo mã SV." : "";
    return {
      a: `Có ${c.students} sinh viên đang có tín hiệu trong kỳ này.${note}`,
      action: { label: "Mở trang Sinh viên", tab: "students" },
    };
  }
  if (has(/dashboard|thống kê|thong ke|biểu đồ|bieu do|số liệu|so lieu|kpi/)) {
    return { a: "Toàn bộ KPI, biểu đồ và việc cần làm nằm ở trang Dashboard.", action: { label: "Mở Dashboard", tab: "analytics" } };
  }
  if (has(/fairness|công bằng|cong bang/)) {
    return { a: "Chỉ số công bằng giữa các nhóm nằm ở trang Fairness.", action: { label: "Mở Fairness", tab: "fairness" } };
  }
  if (has(/ngưỡng|nguong|threshold/)) {
    return { a: "Cấu hình ngưỡng phân band hiện hành nằm ở trang Ngưỡng.", action: { label: "Mở trang Ngưỡng", tab: "threshold" } };
  }
  if (has(/tín hiệu|tin hieu|theo dõi|theo doi|hỗ trợ|ho tro/)) {
    return {
      a: `Tổng quan hiện tại: ${c.total} tín hiệu · ${c.newSignals} mới · ${c.pending} chờ duyệt · ${c.active} đang theo dõi/hỗ trợ.`,
      action: { label: "Mở danh sách tín hiệu", tab: "signals" },
    };
  }
  return {
    a: "Tôi chưa hỗ trợ câu hỏi này. Bạn có thể hỏi về trường hợp ưu tiên, tín hiệu mới, case chờ duyệt, sinh viên, dashboard, fairness hoặc ngưỡng.",
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
        Trợ lý điều hướng trả lời dựa trên dữ liệu đang hiển thị.
      </p>
    </div>
  );
}

/* ================= Dashboard — KPI + biểu đồ + việc cần làm + gần đây ================= */

function AnalyticsTab({
  loading,
  response,
  setTab,
  onOpenCase,
  onReload,
}: {
  loading: boolean;
  response: CaseListResponse | null;
  setTab: (t: Tab) => void;
  onOpenCase: (caseId: string) => void;
  onReload: () => void;
}) {
  const items = useMemo(() => (response && response.state !== "error" ? response.items : []), [response]);
  const counts = useMemo(() => computeCounts(items), [items]);

  if (loading) return <ListSkeleton />;
  if (!response) return null;
  if (response.state === "error") return <ErrorCard onReload={onReload} />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">Tổng hợp số liệu rà soát từ dữ liệu hiện có.</p>
      </div>

      {response.state === "stale" && (
        <div className="bg-amber-50 border border-amber-200 text-amber-700 p-4 rounded-2xl text-sm">
          Dữ liệu có thể đã cũ vì chưa được cập nhật gần đây.
        </div>
      )}

      {response.state === "empty" ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center shadow-sm">
          <div className="mx-auto w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
            <Icon path={iconPaths.heart} className="w-8 h-8 text-slate-300" />
          </div>
          <h3 className="text-lg font-semibold text-slate-700">Chưa có tín hiệu trong kỳ này</h3>
          <p className="text-sm text-slate-400 mt-1">Không có tín hiệu không đồng nghĩa mọi sinh viên đều ổn định. Vui lòng xem thêm độ phủ nguồn.</p>
        </div>
      ) : (
        <>
          {/* KPI — tất cả tính từ response, không hardcode; dòng phụ là breakdown thật, không phải trend giả */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <KpiCard
              label="Tổng tín hiệu"
              value={counts.total}
              sub={`trên ${counts.students} sinh viên`}
              icon={iconPaths.activity}
              color="red"
            />
            <KpiCard
              label="Tín hiệu mới"
              value={counts.newSignals}
              sub={counts.newEarly > 0 ? `${counts.newEarly} ở mức Ưu tiên sớm` : "chưa có mức Ưu tiên sớm"}
              icon={iconPaths.sparkles}
              color="amber"
            />
            <KpiCard
              label="Chờ duyệt"
              value={counts.pending}
              sub="chờ quyết định phê duyệt"
              icon={iconPaths.clock}
              color="slate"
            />
            <KpiCard
              label="Đang theo dõi / hỗ trợ"
              value={counts.active}
              sub={`${counts.assigned} bàn giao · ${counts.inProgress} hỗ trợ · ${counts.monitoring} theo dõi`}
              icon={iconPaths.users}
              color="emerald"
            />
          </div>

          {/* Charts — bar nominal một màu (nhãn + số hiển thị); donut 2 band có legend kèm số */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            <div className="lg:col-span-3 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
              <ChartHeader title="Trạng thái xử lý" subtitle="Số case theo từng trạng thái hiện tại" icon={iconPaths.activity} />
              <BarRows rows={stateRows(items)} color="#dc2626" />
            </div>
            <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
              <ChartHeader title="Mức ưu tiên rà soát" subtitle="Phân bổ từ dữ liệu hiện có" icon={iconPaths.scale} />
              <Donut segments={bandSegments(items)} centerValue={counts.total} centerLabel="tín hiệu" />
            </div>
          </div>

          {/* Việc cần làm + yếu tố phổ biến */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            <div className="lg:col-span-3 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
              <ChartHeader title="Việc cần làm hôm nay" subtitle="Tổng hợp từ trạng thái case hiện tại" icon={iconPaths.check} />
              <TaskList counts={counts} setTab={setTab} />
            </div>
            <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
              <ChartHeader title="Yếu tố đóng góp phổ biến" subtitle="Tối đa 5 yếu tố" icon={iconPaths.sparkles} />
              <BarRows rows={factorRows(items)} color="#dc2626" />
            </div>
          </div>

          {/* Xu hướng — chưa có API lịch sử, nói thẳng là thiếu thay vì vẽ số liệu giả */}
          <div className="flex items-center gap-4 bg-white border border-dashed border-slate-200 rounded-2xl px-6 py-4">
            <div className="p-2.5 bg-slate-50 rounded-xl text-slate-300 shrink-0">
              <Icon path={iconPaths.chart} className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-600">Xu hướng tín hiệu theo kỳ</p>
              <p className="text-xs text-slate-400">Chưa đủ dữ liệu lịch sử để thể hiện xu hướng tín hiệu theo học kỳ.</p>
            </div>
          </div>

          {/* Tín hiệu gần đây — top 5 theo calculated_at từ response */}
          <RecentSignals items={items} onOpenCase={onOpenCase} onViewAll={() => setTab("signals")} />
        </>
      )}
    </div>
  );
}

/** Segments donut theo band — cặp đỏ HUST/amber đã validate CVD (ΔE 32.4); chưa phân band → xám trung tính. */
function bandSegments(items: ReviewCase[]) {
  const count = (fn: (c: ReviewCase) => boolean) => items.filter(fn).length;
  const segments = [
    { label: BAND_LABEL.can_ra_soat, value: count((c) => c.review_priority_band === "can_ra_soat"), color: "#dc2626" },
    { label: BAND_LABEL.uu_tien_som, value: count((c) => c.review_priority_band === "uu_tien_som"), color: "#f59e0b" },
    { label: "Chưa phân bổ", value: count((c) => c.review_priority_band === null), color: "#cbd5e1" },
  ];
  return segments.filter((s) => s.value > 0);
}

function stateRows(items: ReviewCase[]) {
  const present = Array.from(new Set(items.map((c) => c.case_state)));
  return present
    .map((s) => ({ label: CASE_STATE_LABEL[s], value: items.filter((c) => c.case_state === s).length }))
    .sort((a, b) => b.value - a.value);
}

function factorRows(items: ReviewCase[]) {
  const counts = new Map<string, number>();
  for (const c of items) for (const f of c.contributing_factors) counts.set(f.code, (counts.get(f.code) ?? 0) + 1);
  return Array.from(counts.entries())
    .map(([code, value]) => ({ label: FACTOR_LABEL[code] ?? code, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 5);
}

/* ================= Tín hiệu & Sinh viên ================= */

function SignalsList({ response, onOpenCase }: { response: CaseListResponse; onOpenCase: (caseId: string) => void }) {
  if (response.state === "error") {
    return <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl">Không tải được danh sách tín hiệu. Máy chủ tạm thời không phản hồi.</div>;
  }
  if (response.state === "empty") {
    return <div className="bg-slate-50 border border-slate-200 text-slate-600 p-4 rounded-xl">Chưa có tín hiệu mới trong kỳ dữ liệu này.</div>;
  }
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-slate-800">Danh sách tín hiệu</h2>
      {response.state === "stale" && (
        <div className="bg-amber-50 border border-amber-200 text-amber-700 p-4 rounded-xl text-sm">
          Dữ liệu có thể đã cũ. Danh sách vẫn hiển thị nhưng không được coi là mới nhất.
        </div>
      )}
      <CaseRowsTable items={response.items} onOpenCase={onOpenCase} />
    </div>
  );
}

type SortKey = "band" | "ref" | "state";

function StudentsTab({ response, onOpenCase }: { response: CaseListResponse; onOpenCase: (caseId: string) => void }) {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<SortKey>("band");

  const rows = useMemo(() => {
    if (response.state === "error") return [];
    const needle = q.trim().toLowerCase();
    let list = response.items;
    if (needle) list = list.filter((c) => c.student_ref.toLowerCase().includes(needle) || c.case_id.toLowerCase().includes(needle));
    const bandRank = (c: ReviewCase) => (c.review_priority_band === "uu_tien_som" ? 0 : c.review_priority_band === "can_ra_soat" ? 1 : 2);
    switch (sort) {
      case "ref": return [...list].sort((a, b) => a.student_ref.localeCompare(b.student_ref));
      case "state": return [...list].sort((a, b) => a.case_state.localeCompare(b.case_state));
      default: return [...list].sort((a, b) => bandRank(a) - bandRank(b));
    }
  }, [response, q, sort]);

  if (response.state === "error") {
    return <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl">Không tải được danh sách. Máy chủ tạm thời không phản hồi.</div>;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-slate-800">Sinh viên có tín hiệu</h2>
      <div className="flex flex-wrap gap-3 items-center bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="🔍 Tìm theo mã SV…"
          aria-label="Tìm kiếm sinh viên"
          className="flex-1 min-w-[220px] px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-100 focus:border-red-300 transition-all"
        />
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as SortKey)}
          className="px-4 py-2.5 bg-white border border-slate-200 rounded-lg text-sm text-slate-600 outline-none cursor-pointer focus:ring-2 focus:ring-red-100"
        >
          <option value="band">Mức độ cần quan tâm</option>
          <option value="ref">Mã SV (A → Z)</option>
          <option value="state">Trạng thái case</option>
        </select>
        <span className="text-sm text-slate-400 ml-auto">{rows.length} sinh viên</span>
      </div>

      {rows.length === 0 ? (
        <div className="bg-slate-50 border border-slate-200 text-slate-600 p-4 rounded-xl">Không có kết quả khớp tìm kiếm. Thử xóa từ khóa hoặc đổi bộ lọc.</div>
      ) : (
        <CaseRowsTable items={rows} onOpenCase={onOpenCase} />
      )}

      <p className="text-xs text-slate-400">
        Danh sách hiện gồm sinh viên có tín hiệu cần rà soát. Thông tin tên, lớp và GPA đang được hoàn thiện;
        mã sinh viên hiện được bảo vệ bằng mã định danh riêng.
      </p>
    </div>
  );
}

/* ================= Reusable UI ================= */

function CaseRowsTable({ items, onOpenCase }: { items: ReviewCase[]; onOpenCase: (caseId: string) => void }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse min-w-[800px]">
          <thead>
            <tr className="bg-slate-50/50 border-b border-slate-200">
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Mã SV</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Trạng thái case</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Mức ưu tiên rà soát</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Yếu tố đóng góp</th>
              <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Giới hạn dữ liệu</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr
                key={c.case_id}
                onClick={() => onOpenCase(c.case_id)}
                title="Mở chi tiết"
                className="border-b border-slate-100 last:border-0 cursor-pointer hover:bg-slate-50/70 transition-colors"
              >
                <td className="p-4 text-sm font-medium text-[#dc2626]">{c.student_ref}</td>
                <td className="p-4"><CaseStateBadge state={c.case_state} /></td>
                <td className="p-4"><BandBadge band={c.review_priority_band} /></td>
                <td className="p-4 text-sm text-slate-500">
                  {c.contributing_factors.map((f) => FACTOR_LABEL[f.code] ?? f.code).join(", ") || "—"}
                </td>
                <td className="p-4 max-w-[300px]"><LimitationsList limitations={c.limitations} /></td>
              </tr>
            ))}
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

/** Donut SVG — khe 2px giữa các cung; tổng ở tâm; legend chữ + số (màu không bao giờ là tín hiệu duy nhất). */
function Donut({ segments, centerValue, centerLabel }: { segments: { label: string; value: number; color: string }[]; centerValue: number; centerLabel: string }) {
  const total = segments.reduce((acc, s) => acc + s.value, 0);
  if (total === 0) return <div className="text-sm text-slate-400 italic py-4 text-center">Chưa có dữ liệu.</div>;

  const R = 42;
  const C = 2 * Math.PI * R;
  const gap = segments.length > 1 ? 2.5 : 0;
  let offset = 0;
  const arcs = segments.map((s) => {
    const len = (s.value / total) * C;
    const arc = { ...s, len, offset };
    offset += len;
    return arc;
  });

  return (
    <div className="flex flex-col items-center gap-5">
      <div className="relative w-44 h-44">
        <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
          {arcs.map((a) => (
            <circle
              key={a.label}
              cx="60"
              cy="60"
              r={R}
              fill="none"
              stroke={a.color}
              strokeWidth="14"
              strokeDasharray={`${Math.max(a.len - gap, 0.5)} ${C - Math.max(a.len - gap, 0.5)}`}
              strokeDashoffset={-a.offset}
            >
              <title>{`${a.label}: ${a.value}`}</title>
            </circle>
          ))}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-slate-800">{centerValue}</span>
          <span className="text-xs text-slate-400">{centerLabel}</span>
        </div>
      </div>
      <div className="w-full space-y-2">
        {segments.map((s) => (
          <div key={s.label} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 min-w-0">
              <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: s.color }} />
              <span className="text-slate-600 truncate">{s.label}</span>
            </div>
            <span className="font-semibold text-slate-800 tabular-nums">{s.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

type Counts = {
  newSignals: number;
  pending: number;
  active: number;
  earlyPriority: number;
};

/** Checklist việc cần làm — chỉ hiện dòng có số thật > 0; không có việc → nói rõ, không bịa. */
function TaskList({ counts, setTab }: { counts: Counts; setTab: (t: Tab) => void }) {
  const tasks: { key: string; icon: string; color: string; text: string; sub: string; tab: Tab }[] = [];
  if (counts.earlyPriority > 0) {
    tasks.push({
      key: "early",
      icon: iconPaths.sparkles,
      color: "bg-amber-50 text-amber-600",
      text: `Rà soát ${counts.earlyPriority} tín hiệu mức Ưu tiên sớm`,
      sub: "Xem yếu tố đóng góp và độ phủ dữ liệu trước khi quyết định",
      tab: "signals",
    });
  }
  if (counts.newSignals > 0) {
    tasks.push({
      key: "new",
      icon: iconPaths.activity,
      color: "bg-[#fee2e2] text-[#dc2626]",
      text: `Xem ${counts.newSignals} tín hiệu mới`,
      sub: "Đưa vào hàng chờ duyệt hoặc loại kèm lý do",
      tab: "signals",
    });
  }
  if (counts.pending > 0) {
    tasks.push({
      key: "pending",
      icon: iconPaths.clock,
      color: "bg-slate-100 text-slate-600",
      text: `Duyệt ${counts.pending} case đang chờ`,
      sub: "Phê duyệt, loại hoặc hoãn kèm lý do",
      tab: "signals",
    });
  }
  if (counts.active > 0) {
    tasks.push({
      key: "active",
      icon: iconPaths.users,
      color: "bg-emerald-50 text-emerald-600",
      text: `Theo dõi ${counts.active} case đã bàn giao`,
      sub: "Kiểm tra tiến độ hỗ trợ cùng GVCN",
      tab: "students",
    });
  }

  if (tasks.length === 0) {
    return <div className="text-sm text-slate-400 italic py-4 text-center">Chưa có việc cần xử lý. Vui lòng quay lại khi có tín hiệu mới.</div>;
  }

  return (
    <div className="divide-y divide-slate-100">
      {tasks.map((t) => (
        <button
          key={t.key}
          onClick={() => setTab(t.tab)}
          className="w-full flex items-center gap-4 py-3.5 text-left group hover:bg-slate-50/70 rounded-lg px-2 -mx-2 transition-colors"
        >
          <div className={`p-2 rounded-lg shrink-0 ${t.color}`}>
            <Icon path={t.icon} className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-700">{t.text}</p>
            <p className="text-xs text-slate-400 mt-0.5">{t.sub}</p>
          </div>
          <Icon path={iconPaths.arrowRight} className="w-4 h-4 text-slate-300 group-hover:text-[#dc2626] group-hover:translate-x-1 transition-all shrink-0" />
        </button>
      ))}
    </div>
  );
}

/** Top 5 tín hiệu mới nhất theo calculated_at (từ response — không bịa thời gian). */
function RecentSignals({ items, onOpenCase, onViewAll }: { items: ReviewCase[]; onOpenCase: (caseId: string) => void; onViewAll: () => void }) {
  const recent = useMemo(
    () => [...items].sort((a, b) => b.calculated_at.localeCompare(a.calculated_at)).slice(0, 5),
    [items],
  );
  if (recent.length === 0) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-6 pt-5 pb-1">
        <div>
          <h3 className="text-sm font-semibold text-slate-800">Tín hiệu gần đây</h3>
          <p className="text-xs text-slate-400">5 tín hiệu có thời điểm tính mới nhất</p>
        </div>
        <button onClick={onViewAll} className="text-sm font-semibold text-[#dc2626] hover:text-[#b91c1c] inline-flex items-center gap-1 group">
          Xem tất cả
          <Icon path={iconPaths.arrowRight} className="w-4 h-4 transition-transform group-hover:translate-x-1" />
        </button>
      </div>
      <div className="divide-y divide-slate-100 px-2 pb-2 mt-2">
        {recent.map((c) => (
          <button
            key={c.case_id}
            onClick={() => onOpenCase(c.case_id)}
            title="Mở chi tiết"
            className="w-full flex flex-wrap items-center gap-x-4 gap-y-1.5 px-4 py-3.5 text-left hover:bg-slate-50/70 rounded-lg transition-colors"
          >
            <span className="text-sm font-medium text-[#dc2626] w-24 shrink-0">{c.student_ref}</span>
            <span className="text-xs text-slate-500 flex-1 min-w-[160px] truncate">
              {c.contributing_factors.map((f) => FACTOR_LABEL[f.code] ?? f.code).join(", ") || "—"}
            </span>
            <span className="shrink-0"><BandBadge band={c.review_priority_band} /></span>
            <span className="shrink-0"><CaseStateBadge state={c.case_state} /></span>
            <span className="text-xs text-slate-400 tabular-nums shrink-0 w-20 text-right">
              {new Date(c.calculated_at).toLocaleDateString("vi-VN")}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

function ListSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Đang tải">
      <div className="h-52 bg-slate-100 rounded-2xl animate-pulse" />
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => <div key={i} className="h-36 bg-slate-100 rounded-2xl animate-pulse" />)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3 h-64 bg-slate-100 rounded-2xl animate-pulse" />
        <div className="lg:col-span-2 h-64 bg-slate-100 rounded-2xl animate-pulse" />
      </div>
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
