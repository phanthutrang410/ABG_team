"use client";

import { useEffect, useId, useRef, useState, type CSSProperties, type FormEvent } from "react";
import { useGlobalAgent } from "@/components/GlobalAgentProvider";

/**
 * Right-rail Global Agent drawer (doc 13 §9.3).
 * Escape + focus return; aria-live=polite; no localStorage.
 */

export function AgentDrawer() {
  const {
    open,
    busy,
    messages,
    lastUiActions,
    closeDrawer,
    sendQuestion,
    applyUiAction,
  } = useGlobalAgent();
  const [draft, setDraft] = useState("");
  const panelId = useId();
  const titleId = useId();
  const liveId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        closeDrawer();
      }
    };
    document.addEventListener("keydown", onKey);
    const t = window.setTimeout(() => inputRef.current?.focus(), 40);
    return () => {
      document.removeEventListener("keydown", onKey);
      window.clearTimeout(t);
    };
  }, [open, closeDrawer]);

  useEffect(() => {
    if (!open) return;
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, open, busy]);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;
    setDraft("");
    void sendQuestion(text);
  }

  const latestAssistant = [...messages].reverse().find((m) => m.role === "assistant");

  return (
    <>
      <div
        aria-hidden={!open}
        onClick={closeDrawer}
        style={{
          ...scrim,
          opacity: open ? 1 : 0,
          pointerEvents: open ? "auto" : "none",
        }}
      />

      <aside
        id={panelId}
        role="complementary"
        aria-labelledby={titleId}
        aria-hidden={!open}
        style={{
          ...rail,
          transform: open ? "translateX(0)" : "translateX(100%)",
          visibility: open ? "visible" : "hidden",
        }}
      >
        <header style={header}>
          <div style={{ minWidth: 0 }}>
            <p id={titleId} style={{ margin: 0, fontSize: 15, fontWeight: 700, color: "#0f172a" }}>
              Trợ lý AI — chỉ giải thích dữ liệu
            </p>
            <p style={{ margin: "2px 0 0", fontSize: 12, color: "#94a3b8" }}>
              Không chẩn đoán · không tự gửi · con người quyết định
            </p>
          </div>
          <button type="button" onClick={closeDrawer} style={closeBtn} aria-label="Đóng trợ lý AI">
            ×
          </button>
        </header>

        <div
          id={liveId}
          ref={listRef}
          aria-live="polite"
          aria-relevant="additions"
          style={thread}
        >
          {messages.length === 0 && (
            <p style={{ margin: 0, fontSize: 13.5, color: "#64748b", lineHeight: 1.55 }}>
              Hỏi về tín hiệu trên màn hình hiện tại, hoặc nhờ mở báo cáo / danh sách rà soát / bản nháp
              thông báo. Trợ lý chỉ điều hướng trong phạm vi đã được cấp.
            </p>
          )}
          {messages.map((m) => (
            <div
              key={m.id}
              style={{
                display: "flex",
                justifyContent: m.role === "user" ? "flex-end" : "flex-start",
              }}
            >
              <div style={m.role === "user" ? bubbleUser : bubbleAssistant}>
                {m.text}
              </div>
            </div>
          ))}
          {busy && (
            <div style={{ display: "flex", justifyContent: "flex-start" }}>
              <div style={{ ...bubbleAssistant, color: "#94a3b8" }} aria-hidden>
                Đang xử lý…
              </div>
            </div>
          )}
        </div>

        {lastUiActions.length > 0
          && (latestAssistant?.status === "ok" || latestAssistant?.status === "unavailable")
          && (
          <div style={actionsRow} aria-label="Hành động gợi ý">
            {lastUiActions.map((action) => (
              <button
                key={action.key}
                type="button"
                onClick={() => applyUiAction(action)}
                style={actionChip}
              >
                {action.label_vi}
              </button>
            ))}
          </div>
        )}

        <form onSubmit={onSubmit} style={composer}>
          <input
            ref={inputRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            maxLength={500}
            disabled={busy}
            placeholder="Hỏi EduSignal AI…"
            aria-label="Câu hỏi cho trợ lý AI"
            style={input}
          />
          <button type="submit" disabled={busy || !draft.trim()} style={sendBtn} aria-label="Gửi câu hỏi">
            Gửi
          </button>
        </form>
      </aside>
    </>
  );
}

const scrim: CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(15, 23, 42, 0.28)",
  zIndex: 40,
  transition: "opacity 0.2s ease",
};

const rail: CSSProperties = {
  position: "fixed",
  top: 0,
  right: 0,
  bottom: 0,
  width: "min(400px, 100vw)",
  background: "#fff",
  borderLeft: "1px solid #e2e8f0",
  boxShadow: "-12px 0 32px rgba(15, 23, 42, 0.12)",
  zIndex: 50,
  display: "flex",
  flexDirection: "column",
  transition: "transform 0.22s ease",
};

const header: CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "space-between",
  gap: 12,
  padding: "16px 18px",
  borderBottom: "1px solid #f1f5f9",
};

const closeBtn: CSSProperties = {
  width: 32,
  height: 32,
  borderRadius: 8,
  border: "1px solid #e2e8f0",
  background: "#fff",
  color: "#64748b",
  fontSize: 20,
  lineHeight: 1,
  cursor: "pointer",
  flexShrink: 0,
};

const thread: CSSProperties = {
  flex: 1,
  overflowY: "auto",
  padding: "16px 18px",
  display: "flex",
  flexDirection: "column",
  gap: 10,
  background: "#f8fafc",
};

const bubbleUser: CSSProperties = {
  maxWidth: "88%",
  background: "#dc2626",
  color: "#fff",
  fontSize: 13.5,
  lineHeight: 1.5,
  padding: "10px 14px",
  borderRadius: "16px 16px 4px 16px",
};

const bubbleAssistant: CSSProperties = {
  maxWidth: "92%",
  background: "#fff",
  color: "#334155",
  fontSize: 13.5,
  lineHeight: 1.55,
  padding: "10px 14px",
  borderRadius: "16px 16px 16px 4px",
  border: "1px solid #fbeaea",
};

const actionsRow: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 8,
  padding: "10px 18px",
  borderTop: "1px solid #f1f5f9",
  background: "#fff",
};

const actionChip: CSSProperties = {
  border: "1px solid #fecaca",
  background: "#fef2f2",
  color: "#b91c1c",
  fontSize: 12.5,
  fontWeight: 600,
  borderRadius: 999,
  padding: "6px 12px",
  cursor: "pointer",
};

const composer: CSSProperties = {
  display: "flex",
  gap: 8,
  padding: "12px 14px 16px",
  borderTop: "1px solid #e2e8f0",
  background: "#fff",
};

const input: CSSProperties = {
  flex: 1,
  minWidth: 0,
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid #e2e8f0",
  fontSize: 13.5,
  fontFamily: "inherit",
};

const sendBtn: CSSProperties = {
  padding: "10px 16px",
  borderRadius: 10,
  border: "none",
  background: "#dc2626",
  color: "#fff",
  fontWeight: 600,
  fontSize: 13.5,
  cursor: "pointer",
  flexShrink: 0,
};
