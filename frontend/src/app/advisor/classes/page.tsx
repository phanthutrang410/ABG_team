"use client";

import { AdvisorClassesWorkspace } from "@/components/AdvisorClassesWorkspace";
import { AIThinkingOverlay } from "@/components/AIThinkingOverlay";
import { AppShell } from "@/components/AppShell";
import { useSession } from "@/lib/session";

export default function AdvisorClassesPage() {
  const { account, ready } = useSession();
  if (!ready) return <AIThinkingOverlay />;

  return (
    <AppShell role="gvcn" title="Lớp & sinh viên" subtitle="Tra cứu roster trong phạm vi lớp phụ trách; chỉ case đã bàn giao mới có trạng thái hỗ trợ.">
      <AdvisorClassesWorkspace accountId={account?.id ?? "gvcn"} />
    </AppShell>
  );
}
