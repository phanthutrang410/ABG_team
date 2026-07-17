import { getBannerCopy } from "@/lib/copy";

/** H12b — MVP vs research scope banner (dashboard shell). */
export function ScopeBanner() {
  return (
    <aside
      role="note"
      aria-label={getBannerCopy("banner.mvp_scope_title")}
      style={{
        marginBottom: "1.25rem",
        padding: "0.875rem 1rem",
        borderLeft: "3px solid #64748b",
        background: "#f8fafc",
        color: "#334155",
        fontSize: 14,
        lineHeight: 1.5,
      }}
    >
      <strong style={{ display: "block", marginBottom: 4, color: "#0f172a" }}>
        {getBannerCopy("banner.mvp_scope_title")}
      </strong>
      <p style={{ margin: "0 0 0.5rem" }}>{getBannerCopy("banner.mvp_scope_body")}</p>
      <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
        <li>{getBannerCopy("banner.attendance_mvp")}</li>
        <li>{getBannerCopy("banner.forecast_research_blocked")}</li>
      </ul>
    </aside>
  );
}
