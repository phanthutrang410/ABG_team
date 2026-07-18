import type { Metadata } from "next";
import "./globals.css";
import { SessionProvider } from "@/lib/session";

export const metadata: Metadata = {
  title: "Silent Shield",
  description:
    "Tín hiệu cần rà soát từ điểm theo học kỳ và điểm danh theo thời gian — con người duyệt trước bàn giao",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        {/* FR-11: mục đích hỗ trợ, dữ liệu dùng, quyền quyết định của con người */}
        <div
          style={{
            padding: "6px 16px",
            background: "#eef2ff",
            borderBottom: "1px solid #e0e7ff",
            fontSize: 12.5,
            color: "#3730a3",
            textAlign: "center",
          }}
        >
          Hệ thống hỗ trợ rà soát và chăm sóc — không chẩn đoán, không dán nhãn, không kỷ luật tự
          động. Dữ liệu pseudonymized; con người duyệt trước mọi bàn giao.
        </div>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
