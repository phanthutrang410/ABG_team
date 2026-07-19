"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { usePathname, useRouter } from "next/navigation";
import { postAgentTurn } from "@/lib/api";
import {
  navigateAgentRouteKey,
  resourceHandleFromPathname,
  routeKeyForCapability,
  surfaceFromPathname,
} from "@/lib/agent-routes";
import { useSession } from "@/lib/session";
import type { AgentTurnResponse, AgentUIAction } from "@/lib/types";

/**
 * Global Agent thread state (Workstream B / doc 13 §9).
 * Memory-only — no localStorage for chat PII. Reset on role change;
 * keep thread across route changes (provider lives above AppShell remounts).
 */

export type AgentMessageRole = "user" | "assistant";

export type AgentMessage = {
  id: string;
  role: AgentMessageRole;
  text: string;
  status?: AgentTurnResponse["status"] | "error";
  uiActions?: AgentUIAction[];
};

type GlobalAgentCtx = {
  open: boolean;
  busy: boolean;
  messages: AgentMessage[];
  surface: string;
  lastUiActions: AgentUIAction[];
  openDrawer: () => void;
  closeDrawer: () => void;
  sendQuestion: (question: string) => Promise<void>;
  applyUiAction: (action: AgentUIAction) => void;
  /** Ref of the control that opened the drawer — Escape returns focus here. */
  launcherRef: React.MutableRefObject<HTMLElement | null>;
};

const Ctx = createContext<GlobalAgentCtx | null>(null);

let messageSeq = 0;
function nextId(prefix: string): string {
  messageSeq += 1;
  return `${prefix}-${messageSeq}`;
}

/** Structured facts only (≤800) — not a raw chat dump. */
function buildThreadSummary(messages: AgentMessage[]): string | null {
  if (messages.length === 0) return null;
  const recent = messages.slice(-6);
  const parts = recent.map((m) => {
    const label = m.role === "user" ? "Q" : "A";
    const clipped = m.text.replace(/\s+/g, " ").trim().slice(0, 120);
    return `${label}: ${clipped}`;
  });
  const joined = parts.join(" | ");
  return joined.length > 800 ? joined.slice(0, 800) : joined;
}

export function GlobalAgentProvider({ children }: { children: ReactNode }) {
  const { activeRole } = useSession();
  const pathname = usePathname() ?? "/";
  const router = useRouter();

  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [lastUiActions, setLastUiActions] = useState<AgentUIAction[]>([]);
  const launcherRef = useRef<HTMLElement | null>(null);
  const roleRef = useRef(activeRole);

  const surface = surfaceFromPathname(pathname);
  const resourceHandle = resourceHandleFromPathname(pathname);

  // Reset thread on role change; keep across route changes.
  useEffect(() => {
    if (roleRef.current === activeRole) return;
    roleRef.current = activeRole;
    setMessages([]);
    setLastUiActions([]);
    setBusy(false);
    setOpen(false);
  }, [activeRole]);

  const openDrawer = useCallback(() => setOpen(true), []);
  const closeDrawer = useCallback(() => {
    setOpen(false);
    const el = launcherRef.current;
    if (el && typeof el.focus === "function") {
      queueMicrotask(() => el.focus());
    }
  }, []);

  const applyUiAction = useCallback(
    (action: AgentUIAction) => {
      // Reject unknown route_key — do not invent a URL.
      if (!navigateAgentRouteKey(router, action.route_key)) return;
      setOpen(true);
    },
    [router],
  );

  const sendQuestion = useCallback(
    async (question: string) => {
      const text = question.trim();
      if (!text || busy) return;

      const userMsg: AgentMessage = { id: nextId("u"), role: "user", text };
      setMessages((prev) => [...prev, userMsg]);
      setBusy(true);
      setOpen(true);

      const thread_summary = buildThreadSummary([...messages, userMsg]);
      const result = await postAgentTurn({
        surface,
        resource_handle: resourceHandle,
        question: text,
        thread_summary,
      });

      if (!result) {
        setMessages((prev) => [
          ...prev,
          {
            id: nextId("a"),
            role: "assistant",
            text: "Máy chủ tạm thời không phản hồi. Chưa có câu trả lời từ trợ lý — vui lòng thử lại sau.",
            status: "error",
          },
        ]);
        setLastUiActions([]);
        setBusy(false);
        return;
      }

      const assistantMsg: AgentMessage = {
        id: nextId("a"),
        role: "assistant",
        text: result.answer_vi,
        status: result.status,
        uiActions: result.status === "ok" ? result.ui_actions : [],
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setLastUiActions(result.status === "ok" ? result.ui_actions : []);

      if (result.status === "ok" && result.selected_capability) {
        const selectedAction = result.ui_actions.find((a) => a.key === result.selected_capability);
        const routeKey =
          selectedAction?.route_key
          ?? routeKeyForCapability(result.selected_capability)
          ?? null;
        if (routeKey && navigateAgentRouteKey(router, routeKey)) {
          setOpen(true);
        }
      }

      setBusy(false);
    },
    [busy, messages, resourceHandle, router, surface],
  );

  const value = useMemo<GlobalAgentCtx>(
    () => ({
      open,
      busy,
      messages,
      surface,
      lastUiActions,
      openDrawer,
      closeDrawer,
      sendQuestion,
      applyUiAction,
      launcherRef,
    }),
    [
      open,
      busy,
      messages,
      surface,
      lastUiActions,
      openDrawer,
      closeDrawer,
      sendQuestion,
      applyUiAction,
    ],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useGlobalAgent(): GlobalAgentCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useGlobalAgent must be used within GlobalAgentProvider");
  return ctx;
}

/** Safe for pages that may render outside the provider (e.g. login). */
export function useGlobalAgentOptional(): GlobalAgentCtx | null {
  return useContext(Ctx);
}
