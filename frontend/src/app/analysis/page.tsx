"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import ManagementWorkspace from "@/components/ManagementWorkspace";
import { resolveAnalysisGate } from "@/lib/advisor-routing";
import { useSession } from "@/lib/session";

/**
 * Ban quản lý tiếp tục dùng route Phân tích với dữ liệu API hiện có.
 * Link cũ của GVCN được giữ tương thích và chuyển vào hàng đợi đã gộp ở /advisor.
 * Không render ManagementWorkspace thoáng qua cho GVCN (H36 / G07).
 */
export default function AnalysisPage() {
  const { activeRole, ready } = useSession();
  const router = useRouter();
  const gate = resolveAnalysisGate(ready, activeRole);

  useEffect(() => {
    if (gate === "gvcn_redirect") {
      router.replace("/advisor#cases");
    }
  }, [gate, router]);

  if (gate === "loading") {
    return <div className="p-12 text-center text-slate-400">Đang tải…</div>;
  }

  if (gate === "gvcn_redirect") {
    return <div className="p-12 text-center text-slate-400">Đang mở hàng đợi case…</div>;
  }

  return <ManagementWorkspace />;
}
