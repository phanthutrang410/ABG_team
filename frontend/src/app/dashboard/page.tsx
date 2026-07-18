"use client";

import { useCallback, useEffect, useState, type CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { ScopeBanner } from "@/components/ScopeBanner";
import { BandBadge, CaseStateBadge } from "@/components/badges";
import { LimitationsList } from "@/components/LimitationsList";
import { apiBase, fetchReviewCases } from "@/lib/api";
import type { CaseListResponse } from "@/lib/types";

/**
 * G02 — dashboard wired to live GET /review-cases (H02, H11a envelopes).
 * Renders ok/empty/stale/error exactly as the API reports; never fabricates
 * a band/item when the source is unavailable (fail-closed — RULES / AGENTS).
 * Cohort/lớp scoping is NOT built here: public ReviewCase (H06a) has no
 * cohort/department/class_code field today — see handoff note to Hoàng.
 */
export default function DashboardPage() {
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

  return (
    <main style={{ maxWidth: 1000, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <header style={{ marginBottom: "1.25rem" }}>
        <p style={{ margin: 0, color: "#64748b", fontSize: 14 }}>Silent Shield · VAIC 2026</p>
        <h1 style={{ margin: "0.25rem 0 0", fontSize: 28 }}>Danh sách cần rà soát</h1>
        <p style={{ margin: "0.5rem 0 0", color: "#475569" }}>
          Gợi ý mức độ ưu tiên rà soát — không phải kết luận hay kỷ luật. Con người phê duyệt trước khi bàn giao.
        </p>
      </header>

      <ScopeBanner />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem", fontSize: 12, color: "#94a3b8" }}>
        <span>Nguồn: <code>{apiBase()}/review-cases</code></span>
        <button onClick={() => load()} style={retryBtn}>↻ Tải lại</button>
      </div>

      {loading ? <ListSkeleton /> : response ? <ListBody response={response} onOpenCase={(id) => router.push(`/cases/${id}`)} /> : null}

      <p style={{ marginTop: "1rem", fontSize: 13, color: "#94a3b8" }}>
        G02 — dữ liệu tải trực tiếp từ API. Không hiển thị điểm số nội bộ; scoping theo khoa/lớp chưa
        có vì <code>ReviewCase</code> công khai (H06a) hiện chưa mang field cohort/department.
      </p>
    </main>
  );
}

function ListBody({ response, onOpenCase }: { response: CaseListResponse; onOpenCase: (caseId: string) => void }) {
  if (response.state === "error") {
    return (
      <Notice tone="error">
        Không tải được danh sách tín hiệu từ nguồn dữ liệu.{" "}
        {response.problem?.code === "upstream_unavailable" ? "Máy chủ tạm thời không phản hồi." : ""} Bấm “Tải lại” để thử lại.
      </Notice>
    );
  }

  if (response.state === "empty") {
    return <Notice tone="info">Chưa có tín hiệu mới trong kỳ dữ liệu này. Không có tín hiệu mới không đồng nghĩa mọi sinh viên đều ổn định.</Notice>;
  }

  return (
    <>
      {response.state === "stale" && (
        <Notice tone="warning">
          Dữ liệu có thể đã cũ — snapshot chưa được cập nhật gần đây. Danh sách dưới đây vẫn hiển thị nhưng không được coi là mới nhất.
        </Notice>
      )}
      <section style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#f8fafc", textAlign: "left" }}>
              <th style={th}>Mã SV</th>
              <th style={th}>Trạng thái case</th>
              <th style={th}>Mức ưu tiên rà soát</th>
              <th style={th}>Yếu tố đóng góp</th>
              <th style={th}>Giới hạn dữ liệu</th>
            </tr>
          </thead>
          <tbody>
            {response.items.map((c) => (
              <tr key={c.case_id} onClick={() => onOpenCase(c.case_id)} style={{ borderTop: "1px solid #e2e8f0", cursor: "pointer" }} title="Mở chi tiết case">
                <td style={{ ...td, color: "#1d4ed8", fontWeight: 500 }}>{c.student_ref}</td>
                <td style={td}><CaseStateBadge state={c.case_state} /></td>
                <td style={td}><BandBadge band={c.review_priority_band} /></td>
                <td style={td}>{c.contributing_factors.map((f) => f.code).join(", ") || "—"}</td>
                <td style={{ ...td, maxWidth: 300 }}><LimitationsList limitations={c.limitations} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

function Notice({ tone, children }: { tone: "info" | "warning" | "error"; children: React.ReactNode }) {
  const styles: Record<typeof tone, CSSProperties> = {
    info: { background: "#f8fafc", border: "1px solid #e2e8f0", color: "#475569" },
    warning: { background: "#fffbeb", border: "1px solid #fde68a", color: "#92400e" },
    error: { background: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b" },
  };
  return (
    <div style={{ ...styles[tone], padding: "0.9rem 1.1rem", borderRadius: 8, fontSize: 14, marginBottom: "1rem" }}>
      {children}
    </div>
  );
}

function ListSkeleton() {
  return (
    <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: "1.5rem", display: "grid", gap: 10 }} aria-busy="true" aria-label="Đang tải danh sách">
      {[0, 1, 2].map((i) => (
        <div key={i} style={{ height: 16, borderRadius: 4, background: "#f1f5f9", width: `${70 - i * 10}%` }} />
      ))}
    </div>
  );
}

const th: CSSProperties = { padding: "12px 16px", fontSize: 13, color: "#64748b" };
const td: CSSProperties = { padding: "13px 16px", fontSize: 14, verticalAlign: "top" };
const retryBtn: CSSProperties = { padding: "3px 10px", borderRadius: 6, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", color: "#475569", fontSize: 12 };
