"use client";

import { useEffect, type CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { roleHome, useSession } from "@/lib/session";
import { ROLE_ICON, ROLE_LABEL, type Role } from "@/lib/types";

/** Chọn vai khi tài khoản có nhiều vai (ui-design-spec §2). */
export default function SelectRolePage() {
  const { account, chooseRole, ready } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (ready && !account) router.replace("/login");
  }, [ready, account, router]);

  if (!account) return null;

  function go(role: Role) {
    chooseRole(role);
    router.push(roleHome(role));
  }

  return (
    <main style={{ maxWidth: 440, margin: "3rem auto", padding: "0 1.5rem" }}>
      <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: "1.75rem" }}>
        <p style={{ margin: 0, color: "#64748b", fontSize: 13 }}>Chào {account.name}</p>
        <h1 style={{ margin: "0.25rem 0 1rem", fontSize: 22 }}>Chọn vai để tiếp tục</h1>
        <div style={{ display: "grid", gap: 8 }}>
          {account.roles.map((r) => (
            <button key={r} onClick={() => go(r)} style={btn}>
              <span style={{ fontSize: 20 }}>{ROLE_ICON[r]}</span>
              <span style={{ fontWeight: 600 }}>{ROLE_LABEL[r]}</span>
            </button>
          ))}
        </div>
        <p style={{ margin: "1.25rem 0 0", fontSize: 12, color: "#94a3b8" }}>
          Tính năng hiển thị theo quyền của vai bạn chọn; đổi vai ở góc phải màn hình.
        </p>
      </div>
    </main>
  );
}

const btn: CSSProperties = { display: "flex", alignItems: "center", gap: 12, textAlign: "left", padding: "14px 16px", borderRadius: 8, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", fontSize: 15 };
