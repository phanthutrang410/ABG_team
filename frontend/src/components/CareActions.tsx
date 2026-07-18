"use client";

import { useState, type CSSProperties } from "react";
import { postCaseTransition } from "@/lib/api";
import { CASE_STATE_LABEL, type CaseAction, type CaseState, type TransitionErrorBody } from "@/lib/types";

/**
 * G03 — Care workflow actions (H03: POST /cases/{id}/transitions).
 * Only Process §4 allowed actions per state; defer keeps pending_review + review_at;
 * assign never sends advisor_ref (server resolves via H08; 409 → mapping-repair notice).
 * Role gating (BLĐ vs CVHT) chưa có auth trong demo — ghi chú hiển thị.
 */

/** Mirror backend _ALLOWED (app/cases/domain.py) — UI never offers a forbidden action. */
const ACTIONS_BY_STATE: Partial<Record<CaseState, CaseAction[]>> = {
  new_signal: ["queue_for_review"],
  pending_review: ["approve", "dismiss", "defer"],
  approved_for_follow_up: ["assign"],
  assigned: ["accept"],
  follow_up_in_progress: ["resolve", "monitor"],
  monitoring: ["resolve"],
};

/**
 * Lý do loại chuẩn hóa (PRD §5.3). Machine code do FE đề xuất — backend nhận
 * free string; cần H12a chốt bộ code chính thức (ghi trong handoff).
 */
const DISMISS_REASONS: { code: string; label: string }[] = [
  { code: "data_error", label: "Dữ liệu sai" },
  { code: "excused_absence", label: "Nghỉ có phép" },
  { code: "already_supported", label: "Đã được hỗ trợ" },
  { code: "insufficient_evidence", label: "Không đủ căn cứ" },
];

const ACTION_LABEL: Record<CaseAction, string> = {
  queue_for_review: "Đưa vào hàng chờ duyệt",
  approve: "Duyệt chuyển tới người hỗ trợ",
  dismiss: "Loại tín hiệu (lưu lý do)",
  defer: "Hoãn (giữ Chờ duyệt)",
  assign: "Bàn giao cố vấn phụ trách",
  accept: "Xác nhận tiếp nhận",
  resolve: "Kết thúc vòng hỗ trợ",
  monitor: "Chuyển theo dõi có thời hạn",
};

type LogEntry = { label: string; detail?: string };

export function CareActions({
  caseId,
  caseState,
  onStateChange,
}: {
  caseId: string;
  caseState: CaseState;
  onStateChange: (next: CaseState) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mappingRepair, setMappingRepair] = useState(false);
  const [log, setLog] = useState<LogEntry[]>([]);
  const [dismissReason, setDismissReason] = useState(DISMISS_REASONS[0].code);
  const [deferDate, setDeferDate] = useState("");
  const [monitorDate, setMonitorDate] = useState("");

  const allowed = ACTIONS_BY_STATE[caseState] ?? [];

  async function run(action: CaseAction) {
    setBusy(true);
    setError(null);
    setMappingRepair(false);

    const payload: Parameters<typeof postCaseTransition>[1] = { action };
    if (action === "dismiss") payload.reason_code = dismissReason;
    if (action === "defer") {
      if (!deferDate) {
        setError("Chọn ngày xem lại trước khi hoãn.");
        setBusy(false);
        return;
      }
      payload.review_at = `${deferDate}T00:00:00Z`;
    }
    if (action === "monitor") {
      if (!monitorDate) {
        setError("Chọn thời hạn theo dõi trước.");
        setBusy(false);
        return;
      }
      payload.monitoring_until = `${monitorDate}T00:00:00Z`;
    }

    const result = await postCaseTransition(caseId, payload);
    setBusy(false);

    if (result.ok) {
      const reasonLabel = DISMISS_REASONS.find((r) => r.code === result.data.reason_code)?.label;
      setLog((l) => [
        {
          label: ACTION_LABEL[action],
          detail:
            action === "defer" && result.data.review_at
              ? `xem lại: ${result.data.review_at.slice(0, 10)}`
              : action === "dismiss" && reasonLabel
                ? `lý do: ${reasonLabel}`
                : undefined,
        },
        ...l,
      ]);
      onStateChange(result.data.state);
      return;
    }

    setError(describeError(result.error));
    if (result.error?.mapping_repair_queued) setMappingRepair(true);
  }

  return (
    <aside style={panel}>
      <h2 style={h2}>HÀNH ĐỘNG RÀ SOÁT</h2>
      <p style={{ margin: "0 0 0.75rem", fontSize: 12.5, color: "#94a3b8" }}>
        Trạng thái: <strong style={{ color: "#334155" }}>{CASE_STATE_LABEL[caseState]}</strong> · quyền
        Ban quản lý (demo chưa gắn đăng nhập)
      </p>

      {allowed.length === 0 && (
        <p style={{ margin: 0, fontSize: 13, color: "#64748b", fontStyle: "italic" }}>
          Case ở trạng thái kết thúc — chỉ mở case mới khi có thay đổi đáng kể.
        </p>
      )}

      <div style={{ display: "grid", gap: 10 }}>
        {allowed.includes("queue_for_review") && (
          <button style={btnPrimary} disabled={busy} onClick={() => run("queue_for_review")}>
            → {ACTION_LABEL.queue_for_review}
          </button>
        )}

        {allowed.includes("approve") && (
          <button style={{ ...btnPrimary, borderColor: "#86efac", background: "#f0fdf4" }} disabled={busy} onClick={() => run("approve")}>
            ✓ {ACTION_LABEL.approve}
          </button>
        )}

        {allowed.includes("dismiss") && (
          <div style={group}>
            <label style={lbl}>
              Lý do loại (chuẩn hóa)
              <select value={dismissReason} onChange={(e) => setDismissReason(e.target.value)} style={input}>
                {DISMISS_REASONS.map((r) => (
                  <option key={r.code} value={r.code}>{r.label}</option>
                ))}
              </select>
            </label>
            <button style={btn} disabled={busy} onClick={() => run("dismiss")}>
              ✕ {ACTION_LABEL.dismiss}
            </button>
          </div>
        )}

        {allowed.includes("defer") && (
          <div style={group}>
            <label style={lbl}>
              Ngày xem lại
              <input type="date" value={deferDate} onChange={(e) => setDeferDate(e.target.value)} style={input} />
            </label>
            <button style={btn} disabled={busy} onClick={() => run("defer")}>
              ⏸ {ACTION_LABEL.defer}
            </button>
          </div>
        )}

        {allowed.includes("assign") && (
          <button style={{ ...btnPrimary, borderColor: "#93c5fd", background: "#eff6ff" }} disabled={busy} onClick={() => run("assign")}>
            → {ACTION_LABEL.assign}
          </button>
        )}

        {allowed.includes("accept") && (
          <button style={btnPrimary} disabled={busy} onClick={() => run("accept")}>
            ✓ {ACTION_LABEL.accept}
          </button>
        )}

        {allowed.includes("resolve") && (
          <button style={btn} disabled={busy} onClick={() => run("resolve")}>
            ✓ {ACTION_LABEL.resolve}
          </button>
        )}

        {allowed.includes("monitor") && (
          <div style={group}>
            <label style={lbl}>
              Theo dõi đến ngày
              <input type="date" value={monitorDate} onChange={(e) => setMonitorDate(e.target.value)} style={input} />
            </label>
            <button style={btn} disabled={busy} onClick={() => run("monitor")}>
              👁 {ACTION_LABEL.monitor}
            </button>
          </div>
        )}
      </div>

      {busy && <p style={{ margin: "0.75rem 0 0", fontSize: 13, color: "#64748b" }}>Đang gửi…</p>}

      {mappingRepair ? (
        <div style={noticeWarn}>
          Chưa xác định được cố vấn phụ trách — bàn giao tạm dừng, case đã vào hàng chờ sửa mapping.
          Không bàn giao chỉ vì đã duyệt.
        </div>
      ) : error ? (
        <div style={noticeErr}>{error}</div>
      ) : null}

      {log.length > 0 && (
        <div style={{ marginTop: "0.9rem" }}>
          <div style={{ fontSize: 12, color: "#64748b", marginBottom: 4 }}>Hành động phiên này</div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: "#334155", display: "grid", gap: 3 }}>
            {log.map((e, i) => (
              <li key={i}>
                {e.label}
                {e.detail && <span style={{ color: "#94a3b8" }}> · {e.detail}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      <p style={{ margin: "0.9rem 0 0", fontSize: 12, color: "#94a3b8" }}>
        Máy chỉ gợi ý — con người quyết định. Bàn giao do hệ thống tra cố vấn từ nguồn đã duyệt;
        không nhập tay danh tính.
      </p>
    </aside>
  );
}

function describeError(err: TransitionErrorBody | null): string {
  if (!err) return "Máy chủ không phản hồi — hành động chưa được ghi nhận. Thử lại sau.";
  switch (err.code) {
    case "missing_advisor_ref":
      return "Chưa xác định cố vấn phụ trách cho sinh viên này.";
    case "missing_review_at":
      return "Hoãn cần kèm ngày xem lại.";
    case "missing_reason":
      return "Loại tín hiệu cần chọn lý do chuẩn hóa.";
    case "terminal_state":
      return "Case đã kết thúc — không thể thao tác thêm.";
    case "forbidden_transition":
      return "Hành động này không hợp lệ ở trạng thái hiện tại.";
    case "agent_forbidden":
      return "Agent không được phép đổi trạng thái case.";
    default:
      return `Không thực hiện được (${err.code}). Trạng thái hiện tại: ${err.state}.`;
  }
}

const panel: CSSProperties = { background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: "1.1rem 1.35rem", alignSelf: "start" };
const h2: CSSProperties = { margin: "0 0 0.4rem", fontSize: 13, color: "#64748b", letterSpacing: 0.3 };
const btn: CSSProperties = { display: "block", width: "100%", padding: "9px 13px", borderRadius: 8, border: "1px solid #e2e8f0", background: "#fff", fontSize: 13.5, cursor: "pointer", textAlign: "left" };
const btnPrimary: CSSProperties = { ...btn, fontWeight: 600 };
const group: CSSProperties = { display: "grid", gap: 6 };
const lbl: CSSProperties = { display: "grid", gap: 4, fontSize: 12.5, color: "#475569" };
const input: CSSProperties = { padding: "6px 9px", borderRadius: 6, border: "1px solid #e2e8f0", fontSize: 13, fontFamily: "inherit" };
const noticeWarn: CSSProperties = { marginTop: "0.75rem", padding: "0.7rem 0.9rem", borderRadius: 8, background: "#fffbeb", border: "1px solid #fde68a", color: "#92400e", fontSize: 13 };
const noticeErr: CSSProperties = { marginTop: "0.75rem", padding: "0.7rem 0.9rem", borderRadius: 8, background: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b", fontSize: 13 };
