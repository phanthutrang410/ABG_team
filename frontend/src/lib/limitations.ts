import { COPY, copyForReasonCode, type CopyKey } from "@/lib/copy";

/**
 * G05 — resolve ReviewCase.limitations[] to VI text.
 * Entries are either a literal "copy.*" key or a machine reason_code (H11a §2,
 * "limitations[] (machine / copy keys)"). Does not add new copy strings —
 * only consumes COPY/REASON_CODE_TO_COPY_KEY (owned by H12a).
 */
export function resolveLimitation(entry: string): { text: string; known: boolean } {
  if (entry.startsWith("copy.") && entry in COPY) {
    return { text: COPY[entry as CopyKey], known: true };
  }
  const byReason = copyForReasonCode(entry);
  if (byReason) return { text: byReason, known: true };
  // No H12a copy for this machine code yet — show it verbatim, muted, not invented prose.
  return { text: entry, known: false };
}

export function resolveLimitations(entries: readonly string[]): { text: string; known: boolean }[] {
  const seen = new Set<string>();
  const out: { text: string; known: boolean }[] = [];
  for (const e of entries) {
    const r = resolveLimitation(e);
    if (!seen.has(r.text)) {
      seen.add(r.text);
      out.push(r);
    }
  }
  return out;
}
