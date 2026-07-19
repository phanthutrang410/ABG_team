"use client";

import type { CSSProperties } from "react";
import { useGlobalAgentOptional } from "@/components/GlobalAgentProvider";

/**
 * Floating circular Global Agent launcher — fixed bottom-right on every
 * AppShell page. Replaces the topbar stick button; Escape returns focus here.
 */

export function AgentFab() {
  const agent = useGlobalAgentOptional();
  if (!agent) return null;

  return (
    <button
      ref={(el) => {
        agent.launcherRef.current = el;
      }}
      type="button"
      onClick={agent.openDrawer}
      className="ss-agent-fab"
      style={{
        ...fab,
        // Stay mounted while drawer is open so Escape can restore focus.
        opacity: agent.open ? 0 : 1,
        pointerEvents: agent.open ? "none" : "auto",
        visibility: agent.open ? "hidden" : "visible",
      }}
      tabIndex={agent.open ? -1 : 0}
      aria-haspopup="dialog"
      aria-expanded={agent.open}
      title="Trợ lý AI — chỉ giải thích dữ liệu"
      aria-label="Trợ lý AI — chỉ giải thích dữ liệu"
    >
      <span className="ss-agent-fab-ring" aria-hidden />
      <span className="ss-agent-fab-ring ss-agent-fab-ring--delay" aria-hidden />
      <span
        className="ss-agent-fab-avatar"
        style={{
          backgroundImage: "url(/assets/branding/edusignal-ai-robot.png)",
        }}
        aria-hidden
      />
      {agent.busy && (
        <span className="ss-agent-fab-busy" aria-hidden>
          <span className="ss-typing-dot" />
          <span className="ss-typing-dot" />
          <span className="ss-typing-dot" />
        </span>
      )}
    </button>
  );
}

const fab: CSSProperties = {
  position: "fixed",
  right: 24,
  bottom: 24,
  zIndex: 35,
  width: 64,
  height: 64,
  borderRadius: 999,
  border: "2px solid #fecaca",
  background: "linear-gradient(145deg, #ffffff 0%, #fef2f2 100%)",
  boxShadow: "0 10px 28px rgba(185, 28, 28, 0.22), 0 2px 8px rgba(15, 23, 42, 0.08)",
  cursor: "pointer",
  padding: 0,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  overflow: "visible",
  transition: "opacity 0.18s ease",
};
