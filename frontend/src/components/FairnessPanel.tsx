"use client";

import { useEffect, useState, type CSSProperties } from "react";
import { fetchFairnessReport } from "@/lib/api";
import { getCopy } from "@/lib/copy";
import type { FairnessReport } from "@/lib/types";

/**
 * G04 — FR-09 fairness panel wired to GET /fairness/report (H04/M03).
 * MVP path: status=insufficient_data (chưa có thuộc tính audit được phê duyệt)
 * → hiển thị lý do + điều kiện, KHÔNG vẽ chart trống hay số 0 gây hiểu nhầm.
 */
export function FairnessPanel() {
  const [report, setReport] = useState<FairnessReport | null | undefined>(undefined);

  useEffect(() => {
    const controller = new AbortController();
    fetchFairnessReport(controller.signal).then(setReport);
    return () => controller.abort();
  }, []);

  if (report === undefined) return <Skeleton label="Đang tải báo cáo fairness…" />;

  if (report === null) {
    return (
      <div style={noticeErr}>
        Không tải được báo cáo fairness. Máy chủ tạm thời không phản hồi.
      </div>
    );
  }

  if (report.status === "insufficient_data") {
    return (
      <section style={card}>
        <h2 style={{ margin: "0 0 0.5rem", fontSize: 16 }}>Kiểm toán công bằng: Chưa đủ điều kiện công bố</h2>
        <p style={{ margin: "0 0 0.75rem", fontSize: 14, color: "#334155", lineHeight: 1.6 }}>
          {report.reason_code === "no_approved_audit_attribute"
            ? getCopy("copy.fairness_no_approved_audit_attribute")
            : getCopy("copy.fairness_insufficient_group_data")}
        </p>
        <div style={{ padding: "0.75rem 1rem", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: 13, color: "#475569" }}>
          <strong>Điều kiện để có metric theo nhóm:</strong>
          <ul style={{ margin: "0.4rem 0 0", paddingLeft: 18, display: "grid", gap: 3 }}>
            <li>Thuộc tính kiểm toán được đơn vị quản lý dữ liệu phê duyệt</li>
            <li>Dữ liệu đối chiếu và mẫu số được xác định rõ ràng</li>
            <li>Cỡ mẫu mỗi nhóm đủ lớn (n ≥ {report.small_n_min_denominator ?? 10})</li>
          </ul>
        </div>
        <p style={{ margin: "0.75rem 0 0", fontSize: 12, color: "#94a3b8" }}>
          Fail-closed là hành vi đúng: không công bố số khi chưa đủ căn cứ, thay vì vẽ metric thiếu cơ sở.
          <br />Phiên bản phân tích {report.model_version} · quy tắc đối chiếu {report.label_rule_version} · cập nhật lúc {report.computed_at}
        </p>
      </section>
    );
  }

  // Nhánh ok (tương lai — khi có audit attribute được duyệt)
  return (
    <section style={card}>
      <h2 style={{ margin: "0 0 0.5rem", fontSize: 16 }}>
        FPR theo nhóm, thuộc tính: {report.audit_attribute}
      </h2>
      <div style={{ display: "grid", gap: "0.5rem" }}>
        {(report.groups ?? []).map((g) => (
          <div key={`${g.group_type}:${g.group}`} style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 14 }}>
            <span style={{ width: 90, color: "#334155" }}>{g.group}</span>
            {g.status === "insufficient_group_data" || g.fpr === null ? (
              <span style={{ fontStyle: "italic", color: "#64748b", fontSize: 13 }}>
                Cỡ mẫu quá nhỏ (n={g.n_label_neg}), chưa thể kết luận
              </span>
            ) : (
              <>
                <div style={{ flex: 1, maxWidth: 300, height: 14, background: "#eef2f7", borderRadius: 4, overflow: "hidden" }}>
                  <div style={{ width: `${Math.min(100, (g.fpr / 0.2) * 100)}%`, height: "100%", background: "#2a78d6", borderRadius: "0 4px 4px 0" }} />
                </div>
                <span style={{ width: 130, color: "#334155", fontVariantNumeric: "tabular-nums" }}>
                  {(g.fpr * 100).toFixed(1)}% <span style={{ color: "#94a3b8" }}>(n={g.n_label_neg})</span>
                </span>
              </>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

function Skeleton({ label }: { label: string }) {
  return (
    <div style={{ ...card, color: "#94a3b8", fontSize: 14 }} aria-busy="true">
      {label}
    </div>
  );
}

const card: CSSProperties = { background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: "1.25rem 1.5rem" };
const noticeErr: CSSProperties = { padding: "0.9rem 1.1rem", borderRadius: 8, background: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b", fontSize: 14 };
