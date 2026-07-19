import type { Metadata } from "next";
import "./globals.css";
import { GlobalAgentProvider } from "@/components/GlobalAgentProvider";
import { SessionProvider } from "@/lib/session";

export const metadata: Metadata = {
  title: "Silent Shield",
  description:
    "Tín hiệu cần rà soát từ điểm theo học kỳ và điểm danh theo thời gian. Con người duyệt trước bàn giao.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <SessionProvider>
          {/* Global shell persists; provider resets transient thread on route/role changes. */}
          <GlobalAgentProvider>{children}</GlobalAgentProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
