import { resolveLimitations } from "@/lib/limitations";

/** Renders ReviewCase.limitations[] via H12a copy; unmapped codes shown muted/verbatim. */
export function LimitationsList({ limitations }: { limitations: readonly string[] }) {
  if (limitations.length === 0) return null;
  const resolved = resolveLimitations(limitations);
  return (
    <ul style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 4, fontSize: 13 }}>
      {resolved.map((r, i) => (
        <li key={i} style={{ color: r.known ? "#475569" : "#94a3b8", fontStyle: r.known ? "normal" : "italic" }}>
          {r.known ? r.text : `Mã kỹ thuật chưa có bản dịch: ${r.text}`}
        </li>
      ))}
    </ul>
  );
}
