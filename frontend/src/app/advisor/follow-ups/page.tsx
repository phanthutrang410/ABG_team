"use client";

import { AdvisorFollowUpsWorkspace } from "@/components/AdvisorFollowUpsWorkspace";
import { AppShell } from "@/components/AppShell";
import { useSession } from "@/lib/session";

export default function AdvisorFollowUpsPage() {
  const { account, ready } = useSession();
  if (!ready) return <div className="p-12 text-center text-slate-400">Đang tải…</div>;

  return (
    <AppShell role="gvcn" title="Lịch theo dõi" subtitle="Các mốc tiếp nhận, cập nhật hỗ trợ và kiểm tra lại được sắp theo thời gian.">
      <AdvisorFollowUpsWorkspace accountId={account?.id ?? "gvcn"} />
    </AppShell>
  );
}
