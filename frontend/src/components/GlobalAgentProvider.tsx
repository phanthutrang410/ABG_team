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
import { postAgentTurnStream } from "@/lib/api";
import {
  isSupportedAgentAction,
  navigateAgentRouteKey,
  resourceHandleFromPathname,
  surfaceFromPathname,
} from "@/lib/agent-routes";
import { useSession } from "@/lib/session";
import type { AgentTurnResponse, AgentUIAction } from "@/lib/types";

/**
 * Global Agent thread state (Workstream B / doc 13 §9).
 * Memory-only — no localStorage for chat PII. Reset on role, route, or resource
 * change so one case/page never becomes context for another.
 * Sends via POST /agent/turns/stream (SSE status + faux deltas + done).
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

export function GlobalAgentProvider({ children }: { children: ReactNode }) {
  const { activeRole } = useSession();
  const pathname = usePathname() ?? "/";
  const router = useRouter();

  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [lastUiActions, setLastUiActions] = useState<AgentUIAction[]>([]);
  const launcherRef = useRef<HTMLElement | null>(null);
  const activeRequestRef = useRef<AbortController | null>(null);

  const surface = surfaceFromPathname(pathname);
  const resourceHandle = resourceHandleFromPathname(pathname);
  const contextKey = [
    activeRole ?? "none",
    pathname,
    surface,
    resourceHandle ?? "none",
  ].join("|");
  const contextRef = useRef(contextKey);
  const contextReady = contextRef.current === contextKey;

  // Target architecture §9.3: no transient memory across role/page/resource.
  useEffect(() => {
    if (contextRef.current === contextKey) return;
    activeRequestRef.current?.abort();
    activeRequestRef.current = null;
    contextRef.current = contextKey;
    setMessages([]);
    setLastUiActions([]);
    setBusy(false);
    setOpen(false);
  }, [contextKey]);

  useEffect(
    () => () => {
      activeRequestRef.current?.abort();
    },
    [],
  );

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
      const assistantId = nextId("a");
      const placeholder: AgentMessage = {
        id: assistantId,
        role: "assistant",
        text: "",
      };
      setMessages((prev) => [...prev, userMsg, placeholder]);
      setBusy(true);
      setOpen(true);

      const controller = new AbortController();
      activeRequestRef.current?.abort();
      activeRequestRef.current = controller;
      const requestContextKey = contextKey;
      const isCurrentRequest = () =>
        !controller.signal.aborted && contextRef.current === requestContextKey;
      let finished = false;

      await postAgentTurnStream(
        {
          surface,
          resource_handle: resourceHandle,
          question: text,
        },
        {
          onDelta: (chunk) => {
            if (!isCurrentRequest()) return;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, text: m.text + chunk } : m,
              ),
            );
          },
          onDone: (result) => {
            if (!isCurrentRequest()) return;
            finished = true;
            // Never render a dead/unknown action chip. The backend registry is
            // broader than the currently shipped Overview route allowlist.
            const uiActions =
              result.status === "refused"
                ? []
                : result.ui_actions.filter(isSupportedAgentAction);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      text: result.answer_vi,
                      status: result.status,
                      uiActions,
                    }
                  : m,
              ),
            );
            setLastUiActions(uiActions);

            if (result.status === "ok" && result.selected_capability) {
              const selectedAction = uiActions.find(
                (a) => a.key === result.selected_capability,
              );
              // Auto-navigation requires the exact server-authorized card;
              // never reconstruct a route from selected_capability alone.
              if (
                selectedAction
                && navigateAgentRouteKey(router, selectedAction.route_key)
              ) {
                setOpen(true);
              }
            }
          },
          onError: (messageVi) => {
            if (!isCurrentRequest()) return;
            finished = true;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, text: messageVi, status: "error", uiActions: [] }
                  : m,
              ),
            );
            setLastUiActions([]);
          },
        },
        controller.signal,
      );

      if (activeRequestRef.current === controller) {
        activeRequestRef.current = null;
      }
      if (!isCurrentRequest()) return;

      if (!finished) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  text:
                    m.text.trim()
                    || "Máy chủ tạm thời không phản hồi. Chưa có câu trả lời từ trợ lý — vui lòng thử lại sau.",
                  status: "error",
                  uiActions: [],
                }
              : m,
          ),
        );
        setLastUiActions([]);
      }

      setBusy(false);
    },
    [busy, contextKey, resourceHandle, router, surface],
  );

  const value = useMemo<GlobalAgentCtx>(
    () => ({
      // Effects clear the backing state; these guards also prevent one paint
      // of the previous route/case thread before that effect commits.
      open: contextReady ? open : false,
      busy: contextReady ? busy : false,
      messages: contextReady ? messages : [],
      surface,
      lastUiActions: contextReady ? lastUiActions : [],
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
      contextReady,
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
