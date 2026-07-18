"use client";

import { useEffect, useState, type CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { ScopeBanner } from "@/components/ScopeBanner";
import { BandBadge, CaseStateBadge } from "@/components/badges";
import { LimitationsList } from "@/components/LimitationsList";
import {
  CASE_LIST_EMPTY,
  CASE_LIST_ERROR,
  CASE_LIST_OK,
  CASE_LIST_STALE,
} from "@/lib/fixtures";
import type { CaseListResponse } from "@/lib/types";

/**
 * G05 — dashboard shell on validated H11a fixtures (public DTO only, no raw score).
 * G02 replaces DEMO_SCENARIOS/fetch with a live call to GET /review-cases; the
 * render below (ok/empty/stale/error/loading) is what that call must satisfy.
 */

type Scenario = "ok" | "empty" | "stale" | "error";
const SCENARIOS: Record<Scenario, CaseListResponse> = {
  ok: CASE_LIST_OK,
  empty: CASE_LIST_EMPTY,
  stale: CASE_LIST_STALE,
  error: CASE_LIST_ERROR,
};

export default function DashboardPage() {
  const router = useRouter();
  const [scenario, setScenario] = useState<Scenario>("ok");
  const [loading, setLoading] = useState(true);
  const [response, setResponse] = useState<CaseListResponse | null>(null);

  useEffect(() => {
    setLoading(true);
    const t = setTimeout(() => {
      setResponse(SCENARIOS[scenario]);
      setLoading(false);
    }, 350);
    return () => clearTimeout(t);
  }, [scenario]);

  return (
    <main style={{ maxWidth: 1000, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <header style={{ marginBottom: "1.25rem" }}>
        <p style={{ margin: 0, color: "#64748b", fontSize: 14 }}>Silent Shield · VAIC 2026</p>
        <h1 style={{ margin: "0.25rem 0 0", fontSize: 28 }}>Danh sách cần rà soát</h1>
        <p style={{ margin: "0.5rem 0 0", color: "#475569" }}>
          Gợi ý mức độ ưu tiên rà soát — không phải kết luận hay kỷ luật. Con người phê duyệt trước khi bàn giao.
        </p>
      </header>

      <ScopeBanner />

      <DemoStateSwitcher scenario={scenario} onChange={setScenario} />

      {loading ? (
        <ListSkeleton />
      ) : response ? (
        <ListBody response={response} onOpenCase={(id) => router.push(`/cases/${id}`)} />
      ) : null}

      <p style={{ marginTop: "1rem", fontSize: 13, color: "#94a3b8" }}>
        Bản G05 trên fixture đã validate (H11a) — sẽ nối <code>GET /review-cases</code> thật ở G02. Không hiển thị điểm số nội bộ.
      </p>
    </main>
  );
}

function ListBody({ response, onOpenCase }: { response: CaseListResponse; onOpenCase: (caseId: string) => void }) {
  if (response.state === "error") {
    return (
      <Notice tone="error">
        Không tải được danh sách tín hiệu. {response.problem?.code === "upstream_unavailable" ? "Nguồn dữ liệu tạm thời không phản hồi." : ""} Vui lòng thử lại sau.
      </Notice>
    );
  }

  if (response.state === "empty") {
    return <Notice tone="info">Chưa có tín hiệu mới trong kỳ dữ liệu này. Không có tín hiệu mới không đồng nghĩa mọi sinh viên đều ổn định.</Notice>;
  }

  return (
    <>
      {response.state === "stale" && (
        <Notice tone="warning">
          Dữ liệu có thể đã cũ — snapshot chưa được cập nhật gần đây. Danh sách dưới đây vẫn hiển thị nhưng không được coi là mới nhất.
        </Notice>
      )}
      <section style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#f8fafc", textAlign: "left" }}>
              <th style={th}>Mã SV</th>
              <th style={th}>Trạng thái case</th>
              <th style={th}>Mức ưu tiên rà soát</th>
              <th style={th}>Yếu tố đóng góp</th>
              <th style={th}>Giới hạn dữ liệu</th>
            </tr>
          </thead>
          <tbody>
            {response.items.map((c) => (
              <tr key={c.case_id} onClick={() => onOpenCase(c.case_id)} style={{ borderTop: "1px solid #e2e8f0", cursor: "pointer" }} title="Mở chi tiết case">
                <td style={{ ...td, color: "#1d4ed8", fontWeight: 500 }}>{c.student_ref}</td>
                <td style={td}><CaseStateBadge state={c.case_state} /></td>
                <td style={td}><BandBadge band={c.review_priority_band} /></td>
                <td style={td}>{c.contributing_factors.map((f) => f.code).join(", ") || "—"}</td>
                <td style={{ ...td, maxWidth: 300 }}><LimitationsList limitations={c.limitations} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

function DemoStateSwitcher({ scenario, onChange }: { scenario: Scenario; onChange: (s: Scenario) => void }) {
  const opts: { id: Scenario; label: string }[] = [
    { id: "ok", label: "Bình thường" },
    { id: "empty", label: "Trống" },
    { id: "stale", label: "Dữ liệu cũ" },
    { id: "error", label: "Lỗi tải" },
  ];
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: "1rem", fontSize: 12.5, color: "#64748b" }}>
      <span>Xem minh họa trạng thái (QA):</span>
      {opts.map((o) => (
        <button
          key={o.id}
          onClick={() => onChange(o.id)}
          style={{
            padding: "4px 10px",
            borderRadius: 999,
            border: "1px solid " + (scenario === o.id ? "#1d4ed8" : "#e2e8f0"),
            background: scenario === o.id ? "#eff6ff" : "#fff",
            color: scenario === o.id ? "#1d4ed8" : "#64748b",
            fontWeight: scenario === o.id ? 600 : 400,
            cursor: "pointer",
          }}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

function Notice({ tone, children }: { tone: "info" | "warning" | "error"; children: React.ReactNode }) {
  const styles: Record<typeof tone, CSSProperties> = {
    info: { background: "#f8fafc", border: "1px solid #e2e8f0", color: "#475569" },
    warning: { background: "#fffbeb", border: "1px solid #fde68a", color: "#92400e" },
    error: { background: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b" },
  };
  return (
    <div style={{ ...styles[tone], padding: "0.9rem 1.1rem", borderRadius: 8, fontSize: 14, marginBottom: "1rem" }}>
      {children}
    </div>
  );
}

function ListSkeleton() {
  return (
    <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: "1.5rem", display: "grid", gap: 10 }} aria-busy="true" aria-label="Đang tải danh sách">
      {[0, 1, 2].map((i) => (
        <div key={i} style={{ height: 16, borderRadius: 4, background: "#f1f5f9", width: `${70 - i * 10}%` }} />
      ))}
    </div>
  );
}

const th: CSSProperties = { padding: "12px 16px", fontSize: 13, color: "#64748b" };
const td: CSSProperties = { padding: "13px 16px", fontSize: 14, verticalAlign: "top" };
