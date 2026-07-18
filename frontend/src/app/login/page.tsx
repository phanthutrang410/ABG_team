"use client";

import { useEffect, useMemo, useState, type CSSProperties, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { DEMO_ACCOUNTS, roleHome, useSession } from "@/lib/session";
import { ROLE_ICON, ROLE_LABEL } from "@/lib/types";

/**
 * Đăng nhập DEMO: tài khoản + mật khẩu + captcha chống bot (ui-design-spec §3).
 * Xác thực client-side trên fixture — KHÔNG phải auth production (PRD §9).
 */
export default function LoginPage() {
  const { login, account, activeRole, ready } = useSession();
  const router = useRouter();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [captchaInput, setCaptchaInput] = useState("");
  const [seed, setSeed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [forgot, setForgot] = useState(false);

  const captcha = useMemo(() => {
    const a = 2 + ((seed * 7 + 3) % 8);
    const b = 1 + ((seed * 5 + 2) % 7);
    return { a, b, answer: a + b };
  }, [seed]);

  useEffect(() => {
    if (ready && account) router.replace(activeRole ? roleHome(activeRole) : "/select-role");
  }, [ready, account, activeRole, router]);

  function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (Number(captchaInput.trim()) !== captcha.answer) {
      setError("Mã xác nhận chưa đúng — vui lòng tính lại.");
      setSeed((s) => s + 1);
      setCaptchaInput("");
      return;
    }
    const acc = DEMO_ACCOUNTS.find((a) => a.id === username.trim().toLowerCase());
    if (!acc || acc.password !== password) {
      setError("Tài khoản hoặc mật khẩu không đúng.");
      setSeed((s) => s + 1);
      setCaptchaInput("");
      return;
    }
    login(acc.id);
    router.push(acc.roles.length === 1 ? roleHome(acc.roles[0]) : "/select-role");
  }

  return (
    <main style={{ maxWidth: 420, margin: "3rem auto", padding: "0 1.5rem" }}>
      <div style={card}>
        <p style={{ margin: 0, color: "#64748b", fontSize: 13 }}>Silent Shield</p>
        <h1 style={{ margin: "0.25rem 0 0.35rem", fontSize: 24 }}>Đăng nhập</h1>
        <p style={{ margin: "0 0 1.25rem", fontSize: 13, color: "#64748b" }}>
          Hệ thống hỗ trợ quan tâm sinh viên — tính năng hiển thị theo quyền của bạn.
        </p>

        <form onSubmit={submit} style={{ display: "grid", gap: 14 }}>
          <label style={lbl}>
            Tài khoản
            <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="vd: quanly" autoComplete="username" required style={input} />
          </label>
          <label style={lbl}>
            Mật khẩu
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" autoComplete="current-password" required style={input} />
          </label>
          <label style={lbl}>
            Mã xác nhận (chống bot): <strong style={{ color: "#1e293b" }}>{captcha.a} + {captcha.b} = ?</strong>
            <div style={{ display: "flex", gap: 8 }}>
              <input value={captchaInput} onChange={(e) => setCaptchaInput(e.target.value)} inputMode="numeric" placeholder="Kết quả" required style={{ ...input, flex: 1 }} />
              <button type="button" onClick={() => { setSeed((s) => s + 1); setCaptchaInput(""); }} title="Đổi phép tính" style={ghostBtn}>↻</button>
            </div>
          </label>

          {error && (
            <p role="alert" style={{ margin: 0, padding: "8px 12px", borderRadius: 8, background: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b", fontSize: 13 }}>
              {error}
            </p>
          )}

          <button type="submit" style={primaryBtn}>Đăng nhập</button>
          <button type="button" onClick={() => setForgot((f) => !f)} style={linkBtn}>Quên mật khẩu?</button>
          {forgot && (
            <p style={{ margin: 0, padding: "8px 12px", borderRadius: 8, background: "#f8fafc", border: "1px solid #e2e8f0", fontSize: 13, color: "#475569" }}>
              Liên hệ quản trị hệ thống của trường để đặt lại mật khẩu. (Demo — không gửi email thật.)
            </p>
          )}
        </form>
      </div>

      <div style={{ ...card, marginTop: "1rem", background: "#f8fafc" }}>
        <p style={{ margin: "0 0 6px", fontSize: 12, fontWeight: 600, color: "#64748b" }}>
          ⓘ Tài khoản demo (mật khẩu chung: <code>demo123</code>)
        </p>
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5, color: "#475569", display: "grid", gap: 2 }}>
          {DEMO_ACCOUNTS.map((a) => (
            <li key={a.id}>
              <code>{a.id}</code> — {a.roles.map((r) => `${ROLE_ICON[r]} ${ROLE_LABEL[r]}`).join(" · ")}
            </li>
          ))}
        </ul>
        <p style={{ margin: "8px 0 0", fontSize: 11.5, color: "#94a3b8" }}>
          Dữ liệu pseudonymized · con người duyệt trước mọi bàn giao · đăng nhập mô phỏng phía client cho demo.
        </p>
      </div>
    </main>
  );
}

const card: CSSProperties = { background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: "1.5rem" };
const lbl: CSSProperties = { display: "grid", gap: 6, fontSize: 13, color: "#475569", fontWeight: 500 };
const input: CSSProperties = { padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5e1", fontSize: 14, fontFamily: "inherit" };
const primaryBtn: CSSProperties = { padding: "11px 14px", borderRadius: 8, border: "none", background: "#1d4ed8", color: "#fff", fontSize: 14, fontWeight: 600, cursor: "pointer" };
const ghostBtn: CSSProperties = { padding: "0 14px", borderRadius: 8, border: "1px solid #cbd5e1", background: "#fff", fontSize: 16, cursor: "pointer", color: "#475569" };
const linkBtn: CSSProperties = { background: "none", border: "none", color: "#1d4ed8", fontSize: 13, cursor: "pointer", justifySelf: "start", padding: 0 };
