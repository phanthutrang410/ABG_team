"use client";

import { AdvisorWorkspace } from "@/components/AdvisorWorkspace";
import { AIThinkingOverlay } from "@/components/AIThinkingOverlay";
import { AppShell } from "@/components/AppShell";
import { useSession } from "@/lib/session";

export default function AdvisorPage() {
  const { account, ready } = useSession();
  if (!ready) return <AIThinkingOverlay />;

  return (
    <AppShell role="gvcn" title="Case của tôi" subtitle="Case đã được phê duyệt và bàn giao cho bạn xử lý.">
      <AdvisorWorkspace accountId={account?.id ?? "gvcn"} />
    </AppShell>
  );
}
