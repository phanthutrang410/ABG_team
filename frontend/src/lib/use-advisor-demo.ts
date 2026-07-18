"use client";

import { useEffect, useState } from "react";
import {
  advisorDemoStorageKey,
  generateAdvisorDemoCases,
  type AdvisorDemoCase,
} from "@/lib/advisor-demo";

type StoredAdvisorDemo = {
  variant: number;
  cases: AdvisorDemoCase[];
};

const FALLBACK_NOW = new Date("2026-07-18T08:00:00+07:00");

/** Read-only view of the shared advisor demo store used by utility pages. */
export function useAdvisorDemoSnapshot(accountId: string): StoredAdvisorDemo & { ready: boolean } {
  const [snapshot, setSnapshot] = useState<StoredAdvisorDemo>(() => ({
    variant: 0,
    cases: generateAdvisorDemoCases(accountId, 0, FALLBACK_NOW),
  }));
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(advisorDemoStorageKey(accountId));
      if (raw) {
        const stored = JSON.parse(raw) as StoredAdvisorDemo;
        if (Number.isInteger(stored.variant) && Array.isArray(stored.cases) && stored.cases.length > 0) {
          setSnapshot(stored);
        }
      }
    } catch {
      // Corrupt demo storage is disposable; deterministic fallback remains safe.
    }
    setReady(true);
  }, [accountId]);

  return { ...snapshot, ready };
}
