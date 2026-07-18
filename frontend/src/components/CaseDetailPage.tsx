"use client";

import { use, useCallback, useEffect, useState, type CSSProperties } from "react";
import Link from "next/link";
import { BandBadge, CaseStateBadge } from "@/components/badges";
import { AgentPanel } from "@/components/AgentPanel";
import { AppShell } from "@/components/AppShell";
import { CareActions } from "@/components/CareActions";
import { LimitationsList } from "@/components/LimitationsList";
import { fetchReviewCase } from "@/lib/api";
import { useSession } from "@/lib/session";
import type { CaseDetailResponse, CaseState } from "@/lib/types";

/**
 * G02+G03 — case detail on live GET /review-cases/{caseId} (H02) with the
 * care workflow panel (H03 transitions) + agent explanation (H24, FR-08).
 * Layout theo mockup 18/7, đã lược: chỉ hiển thị field thuộc public contract
 * (H11a allowlist) — không MSSV/khoa/khóa, không score, không mục chưa có API.
 */
export default function CaseDetailPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const { activeRole } = useSession();
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

  const handleStateChange = useCallback((next: CaseState) => {
    setResponse((prev) =>
      prev && prev.case ? { ...prev, case: { ...prev.case, case_state: next } } : prev,
    );
  }, []);

  return (
    <AppShell
      role={activeRole ?? "ban_quan_ly"}
      title="Chi tiết case"
      subtitle="Dữ liệu định danh giả và mức ưu tiên rà soát; con người phê duyệt trước mọi bàn giao."
    >
      <div style={{ maxWidth: 1080, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Link href="/analysis?tab=signals" style={{ fontSize: 14, color: "#2a78d6" }}>← Danh sách tín hiệu</Link>
          <button onClick={() => load()} style={retryBtn}>↻ Tải lại</button>
        </div>

        {loading ? (
          <DetailSkeleton />
        ) : response ? (
          <Body response={response} onStateChange={handleStateChange} />
        ) : null}
      </div>
    </AppShell>
  );
}

function Body({ response, onStateChange }: { response: CaseDetailResponse; onStateChange: (next: CaseState) => void }) {
  if (response.state === "error") {
    return <Notice tone="error">Không tải được case này. Máy chủ tạm thời không phản hồi, vui lòng bấm “Tải lại”.</Notice>;
  }
  if (response.state === "empty") {
    return <Notice tone="info">Không tìm thấy case trong phạm vi được xem.</Notice>;
  }
  if (!response.case) return null;

  const c = response.case;
  const insufficient = c.data_state === "insufficient_data";

  return (
    <>
      <header style={{ ...card, display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap", margin: "12px 0 16px" }}>
        <div style={avatar} aria-hidden>SV</div>
        <div style={{ flex: 1, minWidth: 220 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <h1 style={{ margin: 0, fontSize: 21 }}>{c.student_ref}</h1>
            <CopyButton text={c.student_ref} />
          </div>
          <p style={{ margin: "4px 0 0", color: "#94a3b8", fontSize: 12.5 }}>
            Mã định danh được bảo vệ · cập nhật lúc {c.calculated_at.slice(0, 16).replace("T", " ")} · phiên bản {c.model_version}
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <CaseStateBadge state={c.case_state} />
          <BandBadge band={c.review_priority_band} />
        </div>
      </header>

      {response.state === "stale" && <Notice tone="warning">Dữ liệu có thể đã cũ vì chưa được cập nhật gần đây.</Notice>}
      {response.state === "insufficient_data" && <Notice tone="warning">Chưa đủ dữ liệu để tạo mức ưu tiên rà soát cho case này.</Notice>}

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) minmax(300px, 420px)", gap: "1rem", alignItems: "start" }}>
        <div style={{ display: "grid", gap: "1rem" }}>
          <section style={card}>
            <h2 style={h2}>TIẾN TRÌNH RÀ SOÁT</h2>
            <StateTimeline state={c.case_state} />
          </section>

          <section style={card}>
            <h2 style={h2}>YẾU TỐ ĐÓNG GÓP</h2>
            {c.contributing_factors.length === 0 ? (
              <p style={{ margin: 0, fontSize: 14, color: "#64748b", fontStyle: "italic" }}>Không có yếu tố khi thiếu dữ liệu.</p>
            ) : (
              <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))" }}>
                {c.contributing_factors.map((f) => (
                  <div key={f.code} style={factorCard}>
                    <div style={{ fontSize: 13.5, fontWeight: 600, color: "#334155" }}>{factorLabel(f.code)}</div>
                    <div style={{ fontSize: 11.5, color: "#94a3b8", marginTop: 3 }}>
                      <code>{f.code}</code>
                      {f.evidence_refs.length > 0 && <> · {f.evidence_refs.join(", ")}</>}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <p style={{ margin: "10px 0 0", fontSize: 12, color: "#94a3b8" }}>
              Độ phủ: {c.coverage.n_valid_terms} học kỳ · {c.coverage.n_courses} học phần · kỳ gần nhất {c.coverage.last_term_code ?? "—"}
            </p>
          </section>

          <section style={card}>
            <h2 style={h2}>GIỚI HẠN DỮ LIỆU</h2>
            <LimitationsList limitations={c.limitations} />
          </section>
        </div>

        <div style={{ display: "grid", gap: "1rem" }}>
          {insufficient ? (
            <aside style={card}>
              <h2 style={h2}>THAO TÁC</h2>
              <p style={{ margin: 0, fontSize: 13, color: "#64748b", fontStyle: "italic" }}>
                Không đủ dữ liệu để tạo mức ưu tiên. Hệ thống chưa đề xuất hành động rà soát cho case này.
              </p>
            </aside>
          ) : (
            <CareActions caseId={c.case_id} caseState={c.case_state} onStateChange={onStateChange} />
          )}
          <AgentPanel caseId={c.case_id} />
        </div>
      </div>
    </>
  );
}

/* ---------- Timeline (chỉ từ case_state hiện tại — không bịa timestamp) ---------- */

const PIPELINE: CaseState[] = [
  "new_signal",
  "pending_review",
  "approved_for_follow_up",
  "assigned",
  "follow_up_in_progress",
];
const PIPELINE_LABEL: Record<string, string> = {
  new_signal: "Tín hiệu mới",
  pending_review: "Chờ duyệt",
  approved_for_follow_up: "Đã duyệt",
  assigned: "Đã bàn giao",
  follow_up_in_progress: "Đang hỗ trợ",
};

function StateTimeline({ state }: { state: CaseState }) {
  if (state === "dismissed") {
    return (
      <p style={{ margin: 0, fontSize: 13.5, color: "#64748b" }}>
        Tín hiệu đã được rà soát và <strong>loại</strong> kèm lý do chuẩn hóa. Case không được bàn giao.
      </p>
    );
  }
  const terminal = state === "resolved" || state === "monitoring";
  const currentIdx = terminal ? PIPELINE.length : PIPELINE.indexOf(state);

  return (
    <ol style={{ margin: 0, padding: 0, listStyle: "none", display: "grid", gap: 0 }}>
      {PIPELINE.map((s, i) => {
        const done = i < currentIdx;
        const current = i === currentIdx;
        return (
          <li key={s} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
              <span style={{ ...dot, ...(done ? dotDone : current ? dotCurrent : {}) }} />
              {i < PIPELINE.length - 1 && <span style={{ ...line, background: done ? "#2a78d6" : "#e2e8f0" }} />}
            </div>
            <div style={{ paddingBottom: i < PIPELINE.length - 1 ? 14 : 0 }}>
              <span style={{ fontSize: 13.5, fontWeight: current ? 700 : 500, color: done || current ? "#1e293b" : "#94a3b8" }}>
                {PIPELINE_LABEL[s]}
              </span>
              {current && <span style={nowChip}>Hiện tại</span>}
            </div>
          </li>
        );
      })}
      {terminal && (
        <li style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 2 }}>
          <span style={{ ...dot, ...dotCurrent }} />
          <span style={{ fontSize: 13.5, fontWeight: 700, color: "#1e293b" }}>
            {state === "resolved" ? "Đã kết thúc hỗ trợ" : "Đang theo dõi có thời hạn"}
          </span>
        </li>
      )}
    </ol>
  );
}

/* ---------- Nhãn VI cho factor codes M02 (fallback: hiện nguyên code) ---------- */

const FACTOR_LABEL: Record<string, string> = {
  grade_trend_declining: "Kết quả học tập giảm",
  grade_volatility_elevated: "Điểm biến động giữa các kỳ",
  attendance_rate_below_target: "Tỷ lệ điểm danh thấp",
  attendance_trend_declining: "Chuyên cần giảm dần",
};

function factorLabel(code: string): string {
  return FACTOR_LABEL[code] ?? code;
}

/* ---------- phụ trợ ---------- */

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      style={copyBtn}
      title="Sao chép mã"
      onClick={() => {
        navigator.clipboard?.writeText(text).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        });
      }}
    >
      {copied ? "✓ Đã chép" : "⧉"}
    </button>
  );
}

function Notice({ tone, children }: { tone: "info" | "warning" | "error"; children: React.ReactNode }) {
  const styles: Record<typeof tone, CSSProperties> = {
    info: { background: "#f8fafc", border: "1px solid #e2e8f0", color: "#475569" },
    warning: { background: "#fffbeb", border: "1px solid #fde68a", color: "#92400e" },
    error: { background: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b" },
  };
  return (
    <div style={{ ...styles[tone], padding: "0.9rem 1.1rem", borderRadius: 10, fontSize: 14, margin: "12px 0" }}>
      {children}
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div style={{ ...card, display: "grid", gap: 10, marginTop: 12 }} aria-busy="true" aria-label="Đang tải case">
      {[0, 1, 2].map((i) => (
        <div key={i} style={{ height: 16, borderRadius: 4, background: "#f1f5f9", width: `${70 - i * 10}%` }} />
      ))}
    </div>
  );
}

const card: CSSProperties = { background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: "1.1rem 1.35rem" };
const h2: CSSProperties = { margin: "0 0 0.75rem", fontSize: 13, color: "#64748b", letterSpacing: 0.3 };
const avatar: CSSProperties = { width: 46, height: 46, borderRadius: "50%", background: "#e0edfb", color: "#2a78d6", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 14, flexShrink: 0 };
const factorCard: CSSProperties = { border: "1px solid #eef2f7", background: "#f8fafc", borderRadius: 10, padding: "0.65rem 0.85rem" };
const dot: CSSProperties = { width: 12, height: 12, borderRadius: "50%", border: "2px solid #cbd5e1", background: "#fff", flexShrink: 0, marginTop: 3 };
const dotDone: CSSProperties = { border: "2px solid #2a78d6", background: "#2a78d6" };
const dotCurrent: CSSProperties = { border: "2px solid #2a78d6", background: "#fff", boxShadow: "0 0 0 3px #dbeafe" };
const line: CSSProperties = { width: 2, flex: 1, minHeight: 18, marginTop: 2 };
const nowChip: CSSProperties = { marginLeft: 8, fontSize: 11, background: "#eef2ff", color: "#3730a3", borderRadius: 999, padding: "1px 8px", fontWeight: 600 };
const copyBtn: CSSProperties = { border: "1px solid #e2e8f0", background: "#fff", borderRadius: 6, padding: "1px 8px", fontSize: 12, cursor: "pointer", color: "#64748b" };
const retryBtn: CSSProperties = { padding: "3px 10px", borderRadius: 6, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", color: "#475569", fontSize: 12 };
