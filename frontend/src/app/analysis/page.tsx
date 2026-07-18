"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import ManagementWorkspace from "@/components/ManagementWorkspace";
import { useSession } from "@/lib/session";

/**
 * Ban quản lý tiếp tục dùng route Phân tích với dữ liệu API hiện có.
 * Link cũ của GVCN được giữ tương thích và chuyển vào hàng đợi đã gộp ở /advisor.
 */
export default function AnalysisPage() {
  const { activeRole, ready } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (ready && activeRole === "gvcn") router.replace("/advisor#cases");
  }, [activeRole, ready, router]);

  if (!ready) {
    return <div className="p-12 text-center text-slate-400">Đang tải…</div>;
  }

  if (activeRole === "gvcn") {
    return <div className="p-12 text-center text-slate-400">Đang mở hàng đợi case…</div>;
  }

  return <ManagementWorkspace />;
}
