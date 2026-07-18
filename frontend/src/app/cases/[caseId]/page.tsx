"use client";

import { use, type CSSProperties } from "react";
import Link from "next/link";
import { BandBadge, CaseStateBadge } from "@/components/badges";
import { LimitationsList } from "@/components/LimitationsList";
import { CASE_DETAIL_BY_ID, CASE_DETAIL_ERROR } from "@/lib/fixtures";
import type { CaseDetailResponse } from "@/lib/types";

/**
 * G05 — case detail on validated H11a fixtures. Display-only: no review actions
 * (approve/dismiss/defer/assign belongs to G03; agent explain belongs to T02).
 */
export default function CaseDetailPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const response: CaseDetailResponse = CASE_DETAIL_BY_ID[caseId] ?? CASE_DETAIL_ERROR;

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <Link href="/dashboard" style={{ fontSize: 14 }}>← Danh sách tín hiệu</Link>

      {response.state === "error" && (
        <Notice tone="error">Không tìm thấy case này trên dữ liệu mẫu, hoặc nguồn dữ liệu tạm thời không phản hồi.</Notice>
      )}
      {response.state === "empty" && <Notice tone="info">Không có case trong phạm vi được xem.</Notice>}

      {response.case && (
        <>
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap", margin: "12px 0 4px" }}>
            <h1 style={{ margin: 0, fontSize: 22 }}>Case {response.case.student_ref}</h1>
            <BandBadge band={response.case.review_priority_band} />
            <CaseStateBadge state={response.case.case_state} />
          </div>
          <p style={{ margin: "0 0 1.25rem", color: "#94a3b8", fontSize: 13 }}>
            model {response.case.model_version} · dataset {response.case.dataset_version} · tính lúc {response.case.calculated_at}
          </p>

          {response.state === "stale" && (
            <Notice tone="warning">Dữ liệu có thể đã cũ — snapshot chưa được cập nhật gần đây.</Notice>
          )}
          {response.state === "insufficient_data" && (
            <Notice tone="warning">Chưa đủ dữ liệu để tạo mức ưu tiên rà soát cho case này.</Notice>
          )}

          <section style={card}>
            <h2 style={h2}>YẾU TỐ ĐÓNG GÓP (từ model/API)</h2>
            {response.case.contributing_factors.length === 0 ? (
              <p style={{ margin: 0, fontSize: 14, color: "#64748b", fontStyle: "italic" }}>Không có yếu tố khi thiếu dữ liệu.</p>
            ) : (
              <ul style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 6, fontSize: 14 }}>
                {response.case.contributing_factors.map((f) => (
                  <li key={f.code}>
                    <code>{f.code}</code>
                    {f.evidence_refs.length > 0 && (
                      <span style={{ color: "#94a3b8" }}> — {f.evidence_refs.join(", ")}</span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section style={{ ...card, marginTop: "1rem" }}>
            <h2 style={h2}>ĐỘ PHỦ DỮ LIỆU</h2>
            <ul style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 6, fontSize: 14 }}>
              <li>{response.case.coverage.n_valid_terms} học kỳ hợp lệ · {response.case.coverage.n_courses} học phần</li>
              <li>Kỳ gần nhất: {response.case.coverage.last_term_code ?? "—"}</li>
              <li>Trạng thái coverage: {response.case.coverage.status}</li>
            </ul>
          </section>

          <section style={{ ...card, marginTop: "1rem" }}>
            <h2 style={h2}>GIỚI HẠN DỮ LIỆU</h2>
            <LimitationsList limitations={response.case.limitations} />
          </section>
        </>
      )}

      <p style={{ marginTop: "1.25rem", fontSize: 12, color: "#94a3b8" }}>
        Bản G05 hiển thị theo fixture đã validate — hành động duyệt/loại/hoãn/bàn giao thuộc G03, giải thích agent thuộc T02.
      </p>
    </main>
  );
}

function Notice({ tone, children }: { tone: "info" | "warning" | "error"; children: React.ReactNode }) {
  const styles: Record<typeof tone, CSSProperties> = {
    info: { background: "#f8fafc", border: "1px solid #e2e8f0", color: "#475569" },
    warning: { background: "#fffbeb", border: "1px solid #fde68a", color: "#92400e" },
    error: { background: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b" },
  };
  return (
    <div style={{ ...styles[tone], padding: "0.9rem 1.1rem", borderRadius: 8, fontSize: 14, margin: "12px 0" }}>
      {children}
    </div>
  );
}

const card: CSSProperties = { background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: "1.1rem 1.35rem" };
const h2: CSSProperties = { margin: "0 0 0.6rem", fontSize: 13, color: "#64748b", letterSpacing: 0.3 };
