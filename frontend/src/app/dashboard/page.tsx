import type { CSSProperties } from "react";
import { copyForReasonCodes } from "@/lib/copy";
import {
  MOCK_REVIEW_LIST,
  REVIEW_PRIORITY_BAND_LABEL,
} from "@/lib/mock-review-list";

export default function DashboardPage() {
  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <header style={{ marginBottom: "1.5rem" }}>
        <p style={{ margin: 0, color: "#64748b", fontSize: 14 }}>Silent Shield · VAIC 2026</p>
        <h1 style={{ margin: "0.25rem 0 0", fontSize: 28 }}>Danh sách cần rà soát</h1>
        <p style={{ margin: "0.5rem 0 0", color: "#475569" }}>
          Gợi ý ưu tiên rà soát — không phải kết luận kỷ luật. Dữ liệu demo synthetic.
        </p>
      </header>

      <section
        style={{
          background: "#fff",
          border: "1px solid #e2e8f0",
          borderRadius: 8,
          overflow: "hidden",
        }}
      >
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#f8fafc", textAlign: "left" }}>
              <th style={th}>Mã HS</th>
              <th style={th}>Lớp</th>
              <th style={th}>Ưu tiên rà soát</th>
              <th style={th}>Yếu tố chính</th>
              <th style={th}>Giới hạn dữ liệu</th>
            </tr>
          </thead>
          <tbody>
            {MOCK_REVIEW_LIST.map((row) => {
              const limitations = copyForReasonCodes(row.reasonCodes);
              return (
                <tr key={row.studentId} style={{ borderTop: "1px solid #e2e8f0" }}>
                  <td style={td}>{row.studentId}</td>
                  <td style={td}>{row.classId}</td>
                  <td style={td}>
                    <span style={badge}>
                      {REVIEW_PRIORITY_BAND_LABEL[row.reviewPriorityBand]}
                    </span>
                  </td>
                  <td style={td}>{row.topFactor}</td>
                  <td style={{ ...td, color: "#64748b", fontSize: 13, maxWidth: 280 }}>
                    {limitations.join(" ")}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      <p style={{ marginTop: "1rem", fontSize: 13, color: "#94a3b8" }}>
        P0 mock — sẽ nối API ReviewCase (public: review_priority_band) ở G02. Không hiển thị
        điểm số nội bộ.
      </p>
    </main>
  );
}

const th: CSSProperties = { padding: "12px 16px", fontSize: 13, color: "#64748b" };
const td: CSSProperties = { padding: "14px 16px", fontSize: 14 };
const badge: CSSProperties = {
  display: "inline-block",
  padding: "2px 8px",
  borderRadius: 999,
  background: "#fef3c7",
  color: "#92400e",
  fontSize: 12,
};
