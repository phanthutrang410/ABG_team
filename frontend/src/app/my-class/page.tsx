"use client";

import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { BandBadge, CaseStateBadge } from "@/components/badges";
import { LimitationsList } from "@/components/LimitationsList";
import { fetchReviewCases } from "@/lib/api";
import type { CaseListResponse, CaseState } from "@/lib/types";

/**
 * Màn GVCN "hộp công việc" (ui-design-spec §4.2, §7.7) — chỉ case ĐÃ được duyệt
 * và bàn giao (Ethics §3: GVCN không thấy band của case chưa duyệt).
 * Demo: lọc client-side theo case_state; production cần API scope theo advisor
 * (server-side) — ghi chú gap trong design spec §9.
 */

const HANDED_OFF_STATES: CaseState[] = ["assigned", "follow_up_in_progress", "monitoring", "resolved"];

export default function MyClassPage() {
  return (
    <AppShell
      role="gvcn"
      title="Case được bàn giao cho tôi"
      subtitle="Bạn chỉ thấy case đã được Ban quản lý phê duyệt và bàn giao. Cách tiếp cận sinh viên do bạn quyết định theo bối cảnh thực tế."
    >
      <Body />
    </AppShell>
  );
}

function Body() {
  const router = useRouter();
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

  const mine = useMemo(() => {
    if (!response || response.state === "error") return [];
    return response.items.filter((c) => HANDED_OFF_STATES.includes(c.case_state));
  }, [response]);

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
      {mine.length === 0 ? (
        <div style={{ ...card, textAlign: "center", color: "#64748b" }}>
          Chưa có case nào được bàn giao cho bạn. Khi Ban quản lý phê duyệt và bàn giao, case sẽ xuất hiện ở đây kèm lý do đủ để bắt đầu hỗ trợ.
        </div>
      ) : (
        <div style={{ display: "grid", gap: "1rem" }}>
          {mine.map((c) => (
            <section key={c.case_id} style={card}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <strong style={{ fontSize: 15, color: "#1d4ed8", cursor: "pointer" }} onClick={() => router.push(`/cases/${c.case_id}`)}>
                  {c.student_ref}
                </strong>
                <BandBadge band={c.review_priority_band} />
                <span style={{ marginLeft: "auto" }}><CaseStateBadge state={c.case_state} /></span>
              </div>
              <p style={{ margin: "0.5rem 0", fontSize: 14, color: "#334155" }}>
                Lý do bàn giao: {c.contributing_factors.map((f) => f.code).join(", ") || "xem chi tiết case"} · độ phủ {c.coverage.n_valid_terms} kỳ.
              </p>
              <LimitationsList limitations={c.limitations} />
              <div style={{ marginTop: "0.75rem" }}>
                <button onClick={() => router.push(`/cases/${c.case_id}`)} style={primaryBtn}>
                  Mở chi tiết & cập nhật tiến trình
                </button>
              </div>
            </section>
          ))}
        </div>
      )}

      <p style={{ marginTop: "1.25rem", fontSize: 12, color: "#94a3b8" }}>
        Bạn không thấy danh sách tín hiệu toàn đơn vị hay mức ưu tiên của case chưa duyệt — chỉ dữ liệu
        tối thiểu để bắt đầu hỗ trợ (Ethics §3). Demo lọc theo trạng thái; production sẽ scope theo cố
        vấn ở phía máy chủ.
      </p>
    </>
  );
}

const card: CSSProperties = { background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: "1.25rem 1.5rem" };
const primaryBtn: CSSProperties = { padding: "8px 14px", borderRadius: 8, border: "1px solid #93c5fd", background: "#eff6ff", fontSize: 13.5, fontWeight: 600, color: "#1d4ed8", cursor: "pointer" };
const retryBtn: CSSProperties = { padding: "3px 10px", borderRadius: 6, border: "1px solid #fecaca", background: "#fff", cursor: "pointer", color: "#991b1b", fontSize: 12, marginLeft: 8 };
