"use client";

import { useEffect, useState } from "react";
import { fetchWeeklyBriefingLatest, fetchWeeklyReportLatest } from "@/lib/api";

/**
 * G08 — surface weekly report/briefing behind auth cookies.
 * Fail-closed: empty/null API → trung lập, không bịa aggregate.
 */
export function WeeklyBriefingPanel() {
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const [briefing, setBriefing] = useState<Record<string, unknown> | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const ac = new AbortController();
    Promise.all([
      fetchWeeklyReportLatest("semester", ac.signal),
      fetchWeeklyBriefingLatest("semester", ac.signal),
    ]).then(([r, b]) => {
      setReport(r && typeof r === "object" ? (r as Record<string, unknown>) : null);
      setBriefing(b && typeof b === "object" ? (b as Record<string, unknown>) : null);
      setLoaded(true);
    });
    return () => ac.abort();
  }, []);

  if (!loaded) {
    return <p style={{ color: "var(--ss-muted)", fontSize: 14 }}>Đang tải bản tin tuần…</p>;
  }

  if (!report && !briefing) {
    return (
      <section aria-label="Bản tin tuần">
        <h2 style={{ fontSize: 18, marginBottom: 8 }}>Bản tin tuần</h2>
        <p style={{ color: "var(--ss-muted)", fontSize: 14 }}>
          Chưa có báo cáo tuần sẵn sàng cho phiên đăng nhập hiện tại. Hệ thống không suy diễn số liệu.
        </p>
      </section>
    );
  }

  const aggregates =
    report && typeof report.aggregates === "object" && report.aggregates
      ? (report.aggregates as Record<string, unknown>)
      : null;
  const reportStatus = report && typeof report.status === "string" ? report.status : null;
  const message =
    briefing && typeof briefing.message_vi === "string"
      ? briefing.message_vi
      : briefing && typeof briefing.body_vi === "string"
        ? briefing.body_vi
        : null;

  if (reportStatus === "empty") {
    return (
      <section aria-label="Bản tin tuần" style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 18, marginBottom: 8 }}>Bản tin tuần</h2>
        <p style={{ color: "var(--ss-muted)", fontSize: 14 }}>
          Chưa có bản tin tuần vì workflow so sánh chưa tạo dữ liệu. Hệ thống không diễn giải các giá trị 0 như số liệu thực tế.
        </p>
      </section>
    );
  }

  return (
    <section aria-label="Bản tin tuần" style={{ marginBottom: 24 }}>
      <h2 style={{ fontSize: 18, marginBottom: 8 }}>Bản tin tuần</h2>
      {message ? (
        <p style={{ fontSize: 14, lineHeight: 1.5, whiteSpace: "pre-wrap" }}>{message}</p>
      ) : null}
      {aggregates ? (
        <ul style={{ fontSize: 13, color: "var(--ss-muted)", marginTop: 8 }}>
          {Object.entries(aggregates).map(([k, v]) => (
            <li key={k}>
              {k}: {String(v)}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
