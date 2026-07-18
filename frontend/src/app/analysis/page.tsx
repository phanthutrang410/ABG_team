"use client";

import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import { useRouter } from "next/navigation";
import ManagementWorkspace from "@/components/ManagementWorkspace";
import { AppShell, useSetTopbarInfo } from "@/components/AppShell";
import { BandBadge, CaseStateBadge } from "@/components/badges";
import { LimitationsList } from "@/components/LimitationsList";
import { fetchReviewCases } from "@/lib/api";
import { FACTOR_LABEL } from "@/lib/factors";
import { useSession } from "@/lib/session";
import type { CaseListResponse, CaseState } from "@/lib/types";

/**
 * plan.md §3.3 — một route Phân tích cho cả hai vai.
 * Ban quản lý dùng 5 tab live hiện có; GVCN chỉ nhận inbox case đã bàn giao.
 * Scoping GVCN hiện là filter client-side theo state, không phải production RBAC.
 */
export default function AnalysisPage() {
  const { activeRole, ready } = useSession();

  if (!ready) {
    return <div style={loadingPage}>Đang tải…</div>;
  }

  if (activeRole === "gvcn") {
    return (
      <AppShell
        role="gvcn"
        title="Case được bàn giao cho tôi"
        subtitle="Bạn chỉ thấy case đã được Ban quản lý phê duyệt và bàn giao. Cách tiếp cận sinh viên do bạn quyết định theo bối cảnh thực tế."
      >
        <AdvisorAnalysis />
      </AppShell>
    );
  }

  return <ManagementWorkspace />;
}

const HANDED_OFF_STATES: CaseState[] = ["assigned", "follow_up_in_progress", "monitoring", "resolved"];

function AdvisorAnalysis() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [response, setResponse] = useState<CaseListResponse | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    const controller = new AbortController();
    fetchReviewCases(controller.signal).then((result) => {
      setResponse(result);
      setLoading(false);
    });
    return controller;
  }, []);

  useEffect(() => {
    const controller = load();
    return () => controller.abort();
  }, [load]);

  const mine = useMemo(() => {
    if (!response || response.state === "error") return [];
    return response.items.filter((item) => HANDED_OFF_STATES.includes(item.case_state));
  }, [response]);

  const updatedAt = useMemo(
    () => mine.reduce((latest, item) => item.calculated_at > latest ? item.calculated_at : latest, ""),
    [mine],
  );
  const earlyCount = useMemo(
    () => mine.filter((item) => item.review_priority_band === "uu_tien_som").length,
    [mine],
  );
  useSetTopbarInfo(updatedAt || null, earlyCount);

  if (loading) {
    return <div style={{ ...card, color: "#94a3b8" }} aria-busy="true">Đang tải…</div>;
  }

  if (!response || response.state === "error") {
    return (
      <div style={{ ...card, background: "#fef2f2", borderColor: "#fecaca", color: "#991b1b" }}>
        Không tải được danh sách — máy chủ tạm thời không phản hồi.{" "}
        <button onClick={() => load()} style={retryBtn}>↻ Thử lại</button>
      </div>
    );
  }

  return (
    <>
      {response.state === "stale" && (
        <div style={staleNotice}>
          Dữ liệu có thể đã cũ — danh sách vẫn hiển thị nhưng không được coi là mới nhất.
        </div>
      )}

      {mine.length === 0 ? (
        <div style={{ ...card, textAlign: "center", color: "#64748b" }}>
          Chưa có case nào được bàn giao cho bạn. Khi Ban quản lý phê duyệt và bàn giao,
          case sẽ xuất hiện ở đây kèm lý do đủ để bắt đầu hỗ trợ.
        </div>
      ) : (
        <div style={{ display: "grid", gap: "1rem" }}>
          {mine.map((item) => (
            <section key={item.case_id} style={card}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <button style={caseLink} onClick={() => router.push(`/analysis/${item.case_id}`)}>
                  {item.student_ref}
                </button>
                <BandBadge band={item.review_priority_band} />
                <span style={{ marginLeft: "auto" }}><CaseStateBadge state={item.case_state} /></span>
              </div>
              <p style={{ margin: "0.5rem 0", fontSize: 14, color: "#334155" }}>
                Lý do bàn giao: {item.contributing_factors.map((factor) => FACTOR_LABEL[factor.code] ?? factor.code).join(", ") || "xem chi tiết case"}
                {" · "}độ phủ {item.coverage.n_valid_terms} kỳ.
              </p>
              <LimitationsList limitations={item.limitations} />
              <div style={{ marginTop: "0.75rem" }}>
                <button onClick={() => router.push(`/analysis/${item.case_id}`)} style={primaryBtn}>
                  Mở chi tiết & cập nhật tiến trình
                </button>
              </div>
            </section>
          ))}
        </div>
      )}

      <p style={{ marginTop: "1.25rem", fontSize: 12, color: "#94a3b8" }}>
        Bạn không thấy danh sách tín hiệu toàn đơn vị hay mức ưu tiên của case chưa duyệt — chỉ dữ liệu
        tối thiểu để bắt đầu hỗ trợ (Ethics §3). Demo lọc theo trạng thái; production cần scope theo cố
        vấn ở phía máy chủ.
      </p>
    </>
  );
}

const loadingPage: CSSProperties = { padding: "3rem", textAlign: "center", color: "#94a3b8" };
const card: CSSProperties = { background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: "1.25rem 1.5rem" };
const primaryBtn: CSSProperties = { padding: "8px 14px", borderRadius: 8, border: "1px solid #93c5fd", background: "#eff6ff", fontSize: 13.5, fontWeight: 600, color: "#1d4ed8", cursor: "pointer" };
const retryBtn: CSSProperties = { padding: "3px 10px", borderRadius: 6, border: "1px solid #fecaca", background: "#fff", cursor: "pointer", color: "#991b1b", fontSize: 12, marginLeft: 8 };
const staleNotice: CSSProperties = { marginBottom: "1rem", padding: "0.9rem 1.1rem", borderRadius: 10, background: "#fffbeb", border: "1px solid #fde68a", color: "#92400e", fontSize: 13.5 };
const caseLink: CSSProperties = { border: 0, padding: 0, background: "transparent", color: "#1d4ed8", cursor: "pointer", fontSize: 15, fontWeight: 700 };
