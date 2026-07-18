"use client";

import { AdvisorWorkspace } from "@/components/AdvisorWorkspace";
import { AppShell } from "@/components/AppShell";
import { useSession } from "@/lib/session";

export default function AdvisorPage() {
  const { account, ready } = useSession();
  if (!ready) return <div className="p-12 text-center text-slate-400">Đang tải…</div>;

  return (
    <AppShell role="gvcn" title="Case của tôi" subtitle="Case đã được phê duyệt và bàn giao cho bạn xử lý.">
      <AdvisorWorkspace accountId={account?.id ?? "gvcn"} />
    </AppShell>
  );
}
