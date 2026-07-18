"use client";

import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import { fetchThresholdImpact, fetchThresholds } from "@/lib/api";
import type { PublicThresholdConfig, ThresholdImpactResponse } from "@/lib/types";

/**
 * G04 — FR-10 threshold panel wired to GET /config/thresholds(+impact) (H04).
 * Chỉ hiển thị số đếm tổng hợp theo band (không score cá nhân). Đổi ngưỡng ở
 * đây là minh họa trade-off, không thay đổi kết luận về bất kỳ sinh viên nào.
 */
export function ThresholdPanel() {
  const [config, setConfig] = useState<PublicThresholdConfig | null | undefined>(undefined);
  const [tauCase, setTauCase] = useState(0.5);
  const [tauHigh, setTauHigh] = useState(0.75);
  const [impact, setImpact] = useState<ThresholdImpactResponse | null | undefined>(undefined);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchThresholds(controller.signal).then((cfg) => {
      setConfig(cfg);
      if (cfg) {
        setTauCase(cfg.tau_case);
        setTauHigh(cfg.tau_high);
      }
    });
    return () => controller.abort();
  }, []);

  const loadImpact = useCallback((tc: number, th: number) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setImpact(undefined);
      fetchThresholdImpact(tc, Math.max(tc, th)).then(setImpact);
    }, 350);
  }, []);

  useEffect(() => {
    if (config) loadImpact(tauCase, tauHigh);
  }, [config, tauCase, tauHigh, loadImpact]);

  if (config === undefined) return <div style={{ ...card, color: "#94a3b8" }}>Đang tải cấu hình ngưỡng…</div>;
  if (config === null) {
    return <div style={noticeErr}>Không tải được cấu hình ngưỡng — máy chủ tạm thời không phản hồi.</div>;
  }

  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      <section style={card}>
        <h2 style={{ margin: "0 0 0.25rem", fontSize: 16 }}>Ngưỡng tạo tín hiệu rà soát</h2>
        <p style={{ margin: "0 0 1rem", fontSize: 13, color: "#64748b" }}>
          Phiên bản đang dùng: <code>{config.threshold_config_version}</code> · model <code>{config.model_version}</code>.
          Kéo để xem trade-off giữa tải review và bỏ sót — thay đổi chỉ minh họa, không ghi cấu hình.
        </p>

        <div style={{ display: "grid", gap: 14, maxWidth: 460 }}>
          <label style={lbl}>
            Ngưỡng tạo case (τ_case): <strong style={{ fontVariantNumeric: "tabular-nums" }}>{tauCase.toFixed(2)}</strong>
            <input type="range" min={0} max={1} step={0.05} value={tauCase} onChange={(e) => setTauCase(Number(e.target.value))} aria-label="Ngưỡng tạo case" />
          </label>
          <label style={lbl}>
            Ngưỡng ưu tiên sớm (τ_high): <strong style={{ fontVariantNumeric: "tabular-nums" }}>{Math.max(tauCase, tauHigh).toFixed(2)}</strong>
            <input type="range" min={0} max={1} step={0.05} value={Math.max(tauCase, tauHigh)} onChange={(e) => setTauHigh(Number(e.target.value))} aria-label="Ngưỡng ưu tiên sớm" />
          </label>
        </div>
      </section>

      <section style={{ ...card, display: "grid", gap: "0.75rem" }}>
        <h3 style={{ margin: 0, fontSize: 14, color: "#64748b" }}>Tác động trên snapshot hiện tại (số đếm tổng hợp)</h3>
        {impact === undefined ? (
          <p style={{ margin: 0, fontSize: 14, color: "#94a3b8" }}>Đang tính…</p>
        ) : impact === null ? (
          <p style={{ margin: 0, fontSize: 14, color: "#991b1b" }}>Không tính được tác động — nguồn dữ liệu chưa sẵn sàng (fail-closed).</p>
        ) : (
          <>
            <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
              <Impact label="SV được chấm" value={impact.n_scored} />
              <Impact label="Cần rà soát" value={impact.n_can_ra_soat} />
              <Impact label="Ưu tiên sớm" value={impact.n_uu_tien_som} />
              <Impact label="Không tạo case" value={impact.n_no_case} />
            </div>
            <p style={{ margin: 0, fontSize: 13, color: "#64748b" }}>
              Siết ngưỡng → ít case cần review hơn nhưng dễ bỏ sót; nới ngưỡng → ngược lại. Không hiển thị điểm của từng sinh viên.
            </p>
          </>
        )}
      </section>
    </div>
  );
}

function Impact({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ flex: "1 1 130px", border: "1px solid #e2e8f0", borderRadius: 8, padding: "0.75rem 1rem", background: "#f8fafc" }}>
      <div style={{ fontSize: 12, color: "#64748b" }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color: "#1e293b", fontVariantNumeric: "tabular-nums" }}>{value}</div>
    </div>
  );
}

const card: CSSProperties = { background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: "1.25rem 1.5rem" };
const lbl: CSSProperties = { display: "grid", gap: 6, fontSize: 13, color: "#475569" };
const noticeErr: CSSProperties = { padding: "0.9rem 1.1rem", borderRadius: 8, background: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b", fontSize: 14 };
