"use client";

import { useState, type CSSProperties } from "react";
import { postAgentExplanation } from "@/lib/api";
import type { AgentExplanation, RefusalReason } from "@/lib/types";

/**
 * FR-08 FE consumer — panel "Giải thích của AI" trên trang chi tiết case.
 * Gọi POST /review-cases/{id}/explanation (H24); server dựng context, browser
 * chỉ gửi intent/question/locale. Mọi chữ hiển thị là bản render từ backend
 * (vi_renderer catalog) — FE không tự viết lời giải thích, không fallback.
 */

const DEFAULT_QUESTION = "Vì sao case này cần rà soát?";

/** Copy VI cho mã refusal — giải thích vì sao AI từ chối, không lặp yêu cầu. */
const REFUSAL_LABEL: Record<RefusalReason, string> = {
  invent_or_compute_score: "AI không tự tính hay suy ra điểm số.",
  diagnose_mental_health: "AI không chẩn đoán sức khỏe hoặc tâm lý.",
  speculate_protected_or_personal_cause: "AI không suy đoán nguyên nhân cá nhân/nhạy cảm.",
  decide_contact_discipline_or_status: "AI không quyết định hành động. Con người là người đưa ra quyết định.",
  auto_send_or_notify: "AI không tự gửi tin nhắn hay thông báo.",
  access_data_out_of_scope: "Yêu cầu nằm ngoài phạm vi dữ liệu được cấp.",
  reveal_raw_score_or_weights: "AI không tiết lộ điểm thô hay trọng số của mô hình.",
};

export function AgentPanel({ caseId }: { caseId: string }) {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<AgentExplanation | null | "transport_error">(null);

  async function ask() {
    setBusy(true);
    const r = await postAgentExplanation(caseId, {
      intent: "explain_case",
      question: question.trim() || DEFAULT_QUESTION,
    });
    setResult(r ?? "transport_error");
    setBusy(false);
  }

  return (
    <section style={panel}>
      <h2 style={h2}>GIẢI THÍCH CỦA AI (căn cứ dữ liệu)</h2>

      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={DEFAULT_QUESTION}
          maxLength={500}
          style={input}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !busy) ask();
          }}
        />
        <button style={askBtn} disabled={busy} onClick={ask}>
          {busy ? "…" : "Hỏi"}
        </button>
      </div>

      {result === "transport_error" && (
        <div style={quiet}>Máy chủ tạm thời không phản hồi. Chưa có giải thích, vui lòng thử lại sau.</div>
      )}

      {result && result !== "transport_error" && (
        <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
          <div style={result.status === "ok" ? answerOk : quiet}>{result.answer_vi}</div>

          {result.status === "refused" && result.refusal_reason && (
            <div style={{ fontSize: 12.5, color: "#92400e" }}>
              {REFUSAL_LABEL[result.refusal_reason]}
            </div>
          )}

          {result.model_factors_used.length > 0 && (
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {result.model_factors_used.map((code) => (
                <code key={code} style={factorChip}>{code}</code>
              ))}
            </div>
          )}

          {result.limitations_vi && (
            <p style={{ margin: 0, fontSize: 12.5, color: "#64748b" }}>{result.limitations_vi}</p>
          )}

          <div style={humanNote}>
            <strong>Con người quyết định:</strong> {result.disclaimer_vi}
          </div>
        </div>
      )}
    </section>
  );
}

const panel: CSSProperties = { background: "#fff", border: "1px solid #e2e8f0", borderRadius: 16, padding: "1.25rem", boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)" };
const h2: CSSProperties = { margin: "0 0 0.6rem", fontSize: 13, color: "#64748b", letterSpacing: 0.3 };
const input: CSSProperties = { flex: 1, padding: "8px 11px", borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 13, fontFamily: "inherit", minWidth: 0 };
const askBtn: CSSProperties = { padding: "8px 16px", borderRadius: 8, border: "none", background: "#dc2626", color: "#fff", fontWeight: 600, fontSize: 13, cursor: "pointer" };
const answerOk: CSSProperties = { background: "#fef2f2", border: "1px solid #fee2e2", borderRadius: 10, padding: "0.8rem 1rem", fontSize: 13.5, color: "#7f1d1d", lineHeight: 1.55 };
const quiet: CSSProperties = { marginTop: 10, background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 10, padding: "0.8rem 1rem", fontSize: 13, color: "#475569", lineHeight: 1.5 };
const factorChip: CSSProperties = { fontSize: 11.5, background: "#f1f5f9", border: "1px solid #e2e8f0", borderRadius: 6, padding: "2px 7px", color: "#475569" };
const humanNote: CSSProperties = { background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 10, padding: "0.7rem 0.9rem", fontSize: 12.5, color: "#92400e", lineHeight: 1.5 };
