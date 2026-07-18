"use client";

import { use, useCallback, useEffect, useState, type CSSProperties } from "react";
import Link from "next/link";
import { BandBadge, CaseStateBadge } from "@/components/badges";
import { LimitationsList } from "@/components/LimitationsList";
import { fetchReviewCase } from "@/lib/api";
import type { CaseDetailResponse } from "@/lib/types";

/**
 * G02 — case detail wired to live GET /review-cases/{caseId} (H02, H11a envelopes).
 * Display-only: review actions belong to G03, agent explain belongs to T02.
 */
export default function CaseDetailPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const [loading, setLoading] = useState(true);
  const [response, setResponse] = useState<CaseDetailResponse | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    const controller = new AbortController();
    fetchReviewCase(caseId, controller.signal).then((r) => {
      setResponse(r);
      setLoading(false);
    });
    return controller;
  }, [caseId]);

  useEffect(() => {
    const controller = load();
    return () => controller.abort();
  }, [load]);

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Link href="/dashboard" style={{ fontSize: 14 }}>← Danh sách tín hiệu</Link>
        <button onClick={() => load()} style={retryBtn}>↻ Tải lại</button>
      </div>

      {loading ? (
        <DetailSkeleton />
      ) : response ? (
        <Body response={response} />
      ) : null}

      <p style={{ marginTop: "1.25rem", fontSize: 12, color: "#94a3b8" }}>
        G02 — dữ liệu tải trực tiếp từ API. Hành động duyệt/loại/hoãn/bàn giao thuộc G03, giải thích agent thuộc T02.
      </p>
    </main>
  );
}

function Body({ response }: { response: CaseDetailResponse }) {
  if (response.state === "error") {
    return <Notice tone="error">Không tải được case này — máy chủ tạm thời không phản hồi. Bấm “Tải lại” để thử lại.</Notice>;
  }
  if (response.state === "empty") {
    return <Notice tone="info">Không tìm thấy case trong phạm vi được xem.</Notice>;
  }
  if (!response.case) return null;

  const c = response.case;
  return (
    <>
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap", margin: "12px 0 4px" }}>
        <h1 style={{ margin: 0, fontSize: 22 }}>Case {c.student_ref}</h1>
        <BandBadge band={c.review_priority_band} />
        <CaseStateBadge state={c.case_state} />
      </div>
      <p style={{ margin: "0 0 1.25rem", color: "#94a3b8", fontSize: 13 }}>
        model {c.model_version} · dataset {c.dataset_version} · tính lúc {c.calculated_at}
      </p>

      {response.state === "stale" && <Notice tone="warning">Dữ liệu có thể đã cũ — snapshot chưa được cập nhật gần đây.</Notice>}
      {response.state === "insufficient_data" && <Notice tone="warning">Chưa đủ dữ liệu để tạo mức ưu tiên rà soát cho case này.</Notice>}

      <section style={card}>
        <h2 style={h2}>YẾU TỐ ĐÓNG GÓP (từ model/API)</h2>
        {c.contributing_factors.length === 0 ? (
          <p style={{ margin: 0, fontSize: 14, color: "#64748b", fontStyle: "italic" }}>Không có yếu tố khi thiếu dữ liệu.</p>
        ) : (
          <ul style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 6, fontSize: 14 }}>
            {c.contributing_factors.map((f) => (
              <li key={f.code}>
                <code>{f.code}</code>
                {f.evidence_refs.length > 0 && <span style={{ color: "#94a3b8" }}> — {f.evidence_refs.join(", ")}</span>}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section style={{ ...card, marginTop: "1rem" }}>
        <h2 style={h2}>ĐỘ PHỦ DỮ LIỆU</h2>
        <ul style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 6, fontSize: 14 }}>
          <li>{c.coverage.n_valid_terms} học kỳ hợp lệ · {c.coverage.n_courses} học phần</li>
          <li>Kỳ gần nhất: {c.coverage.last_term_code ?? "—"}</li>
          <li>Trạng thái coverage: {c.coverage.status}</li>
        </ul>
      </section>

      <section style={{ ...card, marginTop: "1rem" }}>
        <h2 style={h2}>GIỚI HẠN DỮ LIỆU</h2>
        <LimitationsList limitations={c.limitations} />
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
    <div style={{ ...styles[tone], padding: "0.9rem 1.1rem", borderRadius: 8, fontSize: 14, margin: "12px 0" }}>
      {children}
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: "1.5rem", display: "grid", gap: 10, marginTop: 12 }} aria-busy="true" aria-label="Đang tải case">
      {[0, 1, 2].map((i) => (
        <div key={i} style={{ height: 16, borderRadius: 4, background: "#f1f5f9", width: `${70 - i * 10}%` }} />
      ))}
    </div>
  );
}

const card: CSSProperties = { background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: "1.1rem 1.35rem" };
const h2: CSSProperties = { margin: "0 0 0.6rem", fontSize: 13, color: "#64748b", letterSpacing: 0.3 };
const retryBtn: CSSProperties = { padding: "3px 10px", borderRadius: 6, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", color: "#475569", fontSize: 12 };
