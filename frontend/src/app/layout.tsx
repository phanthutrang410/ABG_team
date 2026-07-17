import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Silent Shield",
  description: "Cảnh báo sớm — hỗ trợ học sinh cần quan tâm",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
