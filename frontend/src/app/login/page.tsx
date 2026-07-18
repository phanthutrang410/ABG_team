"use client";

import { useEffect, useRef, useState, type CSSProperties, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { DEMO_ACCOUNTS, roleHome, useSession } from "@/lib/session";
import { ROLE_LABEL, type Role } from "@/lib/types";

/**
 * Đăng nhập DEMO: tài khoản + mật khẩu + captcha ảnh chống bot (ui-design-spec §3).
 * Xác thực client-side trên fixture — KHÔNG phải auth production (PRD §9).
 * Layout 2 cột theo mockup EduSignal 18/7: ảnh thương hiệu bên trái (ẩn dưới
 * 860px), form bên phải — ảnh nằm trong frontend/public/assets/branding/.
 */

const CAPTCHA_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; // bỏ ký tự dễ nhầm: O/0, I/1

function generateCaptchaText(length = 5) {
  let out = "";
  for (let i = 0; i < length; i++) out += CAPTCHA_CHARS[Math.floor(Math.random() * CAPTCHA_CHARS.length)];
  return out;
}

export default function LoginPage() {
  const { login, account, activeRole, ready, chooseRole, logout } = useSession();
  const router = useRouter();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [captchaInput, setCaptchaInput] = useState("");
  const [captchaText, setCaptchaText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [forgot, setForgot] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Sinh captcha ở client sau mount — tránh lệch hydration do Math.random chạy trên server.
  useEffect(() => {
    setCaptchaText(generateCaptchaText());
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !captchaText) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#fef2f2";
    ctx.fillRect(0, 0, w, h);

    for (let i = 0; i < 6; i++) {
      ctx.strokeStyle = `rgba(220, 38, 38, ${0.12 + Math.random() * 0.18})`;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(Math.random() * w, Math.random() * h);
      ctx.lineTo(Math.random() * w, Math.random() * h);
      ctx.stroke();
    }

    const charWidth = w / captchaText.length;
    ctx.textBaseline = "middle";
    ctx.textAlign = "center";
    ctx.font = "bold 26px sans-serif";
    for (let i = 0; i < captchaText.length; i++) {
      ctx.save();
      ctx.translate(charWidth * i + charWidth / 2, h / 2 + (Math.random() * 10 - 5));
      ctx.rotate(Math.random() * 0.5 - 0.25);
      ctx.fillStyle = i % 2 === 0 ? "#b91c1c" : "#7f1d1d";
      ctx.fillText(captchaText[i], 0, 0);
      ctx.restore();
    }

    for (let i = 0; i < 40; i++) {
      ctx.fillStyle = `rgba(185, 28, 28, ${Math.random() * 0.35})`;
      ctx.beginPath();
      ctx.arc(Math.random() * w, Math.random() * h, 1, 0, Math.PI * 2);
      ctx.fill();
    }
  }, [captchaText]);

  useEffect(() => {
    if (ready && account && activeRole) router.replace(roleHome(activeRole));
  }, [ready, account, activeRole, router]);

  useEffect(() => {
    // Nạp trước hai không gian làm việc để chuyển vai không giữ màn đăng nhập
    // trong lúc Next.js tải route đích.
    router.prefetch("/overview");
    router.prefetch("/analysis");
  }, [router]);

  function refreshCaptcha() {
    setCaptchaText(generateCaptchaText());
    setCaptchaInput("");
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (captchaInput.trim().toUpperCase() !== captchaText) {
      setError("Mã xác nhận chưa đúng. Vui lòng thử lại.");
      refreshCaptcha();
      return;
    }
    const acc = DEMO_ACCOUNTS.find((a) => a.id === username.trim().toLowerCase());
    if (!acc || acc.password !== password) {
      setError("Tài khoản hoặc mật khẩu không đúng.");
      refreshCaptcha();
      return;
    }
    login(acc.id);
    if (acc.roles.length === 1) router.replace(roleHome(acc.roles[0]));
  }

  function selectRole(role: Role) {
    chooseRole(role);
    router.replace(roleHome(role));
  }

  return (
    <main style={pageWrap}>
      {/* Ẩn panel ảnh dưới 860px — inline style không hỗ trợ @media nên cần thẻ style riêng. */}
      <style>{`@media (max-width: 860px) { .ss-login-visual { display: none; } }`}</style>
      <div className="ss-login-visual" style={leftPanel} role="presentation" />

      <div style={rightPanel}>
        <div style={{ width: "100%" }}>
          <div style={card}>
            {/* Giữ màn chọn vai cho đến khi route đích thay thế hoàn toàn trang
                hiện tại. Nếu activeRole cập nhật trước navigation, tuyệt đối
                không rơi ngược về form đăng nhập. */}
            {account ? (
              <div style={{ display: "grid", gap: 20 }}>
                <div style={{ textAlign: "center" }}>
                  <h1 style={{ margin: 0, fontSize: 30, fontWeight: 700, color: "#0f172a" }}>Chọn không gian làm việc</h1>
                  <p style={{ margin: "0.65rem 0 0", fontSize: 14.5, color: "#64748b", lineHeight: 1.55 }}>
                    Lựa chọn vai trò phù hợp để bắt đầu công việc của bạn.
                  </p>
                </div>

                <div style={{ display: "grid", gap: 10 }}>
                  {account.roles.map((role) => (
                    <button
                      key={role}
                      type="button"
                      onClick={() => selectRole(role)}
                      style={roleButton}
                      onMouseEnter={(e) => Object.assign(e.currentTarget.style, roleButtonHover)}
                      onMouseLeave={(e) => Object.assign(e.currentTarget.style, roleButton)}
                    >
                      <span style={roleIconBox} aria-hidden><RoleIcon role={role} /></span>
                      <span style={{ display: "grid", gap: 2, textAlign: "left" }}>
                        <strong style={{ fontSize: 15.5, color: "#0f172a" }}>{ROLE_LABEL[role]}</strong>
                        <span style={{ fontSize: 12.5, color: "#64748b" }}>
                          {role === "ban_quan_ly" ? "Theo dõi, phân tích và phê duyệt bàn giao" : "Tiếp nhận, theo dõi và hỗ trợ sinh viên"}
                        </span>
                      </span>
                      <span style={roleArrow} aria-hidden><ArrowRightIcon /></span>
                    </button>
                  ))}
                </div>

                <button type="button" onClick={logout} style={backButton}>
                  <ArrowLeftIcon /> Sử dụng tài khoản khác
                </button>
              </div>
            ) : (
              <>
                <h1 style={{ margin: "0 0 0.5rem", fontSize: 32, fontWeight: 700, color: "#0f172a", textAlign: "center" }}>Đăng nhập</h1>
                <p style={{ margin: "0 0 2rem", fontSize: 15.5, color: "#64748b", lineHeight: 1.55, textAlign: "center" }}>
                  Hệ thống hỗ trợ theo dõi và quan tâm sinh viên. Các chức năng được hiển thị theo vai trò của bạn.
                </p>

                <form onSubmit={submit} style={{ display: "grid", gap: 20 }}>
              <label style={lbl}>
                Tài khoản
                <div style={inputWrap}>
                  <span style={inputIcon} aria-hidden><PersonIcon /></span>
                  <input
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="vd: quanly"
                    autoComplete="username"
                    required
                    style={inputWithIcon}
                    onFocus={(e) => Object.assign(e.currentTarget.style, inputWithIconFocus)}
                    onBlur={(e) => Object.assign(e.currentTarget.style, inputWithIcon)}
                  />
                </div>
              </label>
              <label style={lbl}>
                Mật khẩu
                <div style={inputWrap}>
                  <span style={inputIcon} aria-hidden><LockIcon /></span>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    autoComplete="current-password"
                    required
                    style={inputWithIcon}
                    onFocus={(e) => Object.assign(e.currentTarget.style, inputWithIconFocus)}
                    onBlur={(e) => Object.assign(e.currentTarget.style, inputWithIcon)}
                  />
                </div>
              </label>
              <label style={lbl}>
                Mã xác nhận
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <canvas ref={canvasRef} width={190} height={58} style={captchaCanvas} aria-hidden />
                  <button type="button" onClick={refreshCaptcha} title="Đổi mã khác" style={ghostBtn}>
                    <RefreshIcon />
                  </button>
                </div>
                <div style={inputWrap}>
                  <span style={inputIcon} aria-hidden><ShieldIcon /></span>
                  <input
                    value={captchaInput}
                    onChange={(e) => setCaptchaInput(e.target.value)}
                    placeholder="Nhập mã trong ảnh"
                    autoComplete="off"
                    required
                    style={{ ...inputWithIcon, textTransform: "uppercase" }}
                    onFocus={(e) => Object.assign(e.currentTarget.style, inputWithIconFocus)}
                    onBlur={(e) => Object.assign(e.currentTarget.style, inputWithIcon)}
                  />
                </div>
              </label>

              {error && (
                <p role="alert" style={{ margin: 0, padding: "8px 12px", borderRadius: 8, background: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b", fontSize: 13 }}>
                  {error}
                </p>
              )}

              <button
                type="submit"
                style={primaryBtn}
                onMouseEnter={(e) => Object.assign(e.currentTarget.style, primaryBtnHover)}
                onMouseLeave={(e) => Object.assign(e.currentTarget.style, primaryBtn)}
              >
                Đăng nhập
                <ArrowRightIcon />
              </button>
              <button type="button" onClick={() => setForgot((f) => !f)} style={linkBtn}>Quên mật khẩu?</button>
              {forgot && (
                <p style={{ margin: 0, padding: "8px 12px", borderRadius: 8, background: "#f8fafc", border: "1px solid #e2e8f0", fontSize: 13, color: "#475569" }}>
                  Liên hệ quản trị hệ thống của trường để được cấp lại mật khẩu.
                </p>
              )}
                </form>
              </>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

function PersonIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11V7a4 4 0 018 0v4" />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}

function RefreshIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M23 4v6h-6M1 20v-6h6" />
      <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
    </svg>
  );
}

function ArrowRightIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  );
}

function ArrowLeftIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 12H5M12 19l-7-7 7-7" />
    </svg>
  );
}

function RoleIcon({ role }: { role: Role }) {
  if (role === "ban_quan_ly") {
    return (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="3" />
        <path d="M7 16v-3M12 16V8M17 16v-5" />
      </svg>
    );
  }
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="9" cy="8" r="3" />
      <path d="M3.5 20a5.5 5.5 0 0111 0M15.5 12.5l2 2 3.5-4" />
    </svg>
  );
}

const pageWrap: CSSProperties = { minHeight: "100vh", display: "flex", background: "#fff" };
const leftPanel: CSSProperties = {
  flex: "0 0 50%",
  minHeight: "100vh",
  backgroundImage: "url(/assets/branding/edusignal-login-panel.png)",
  backgroundSize: "cover",
  backgroundPosition: "center",
};
const rightPanel: CSSProperties = { flex: "0 0 50%", display: "flex", alignItems: "center", justifyContent: "center", padding: "3rem" };
const card: CSSProperties = { width: "100%", maxWidth: 600, background: "#fff", border: "1px solid #e2e8f0", borderRadius: 20, padding: "3.5rem", boxShadow: "0 8px 24px rgba(220, 38, 38, 0.06)" };
const lbl: CSSProperties = { display: "grid", gap: 8, fontSize: 15, color: "#475569", fontWeight: 500 };
const inputWrap: CSSProperties = { position: "relative", display: "flex", alignItems: "center" };
const inputIcon: CSSProperties = { position: "absolute", left: 16, display: "flex", color: "#dc2626", pointerEvents: "none" };
const inputWithIcon: CSSProperties = {
  width: "100%",
  padding: "16px 16px 16px 46px",
  borderRadius: 10,
  border: "1px solid #cbd5e1",
  fontSize: 17,
  fontFamily: "inherit",
  outline: "none",
  transition: "border-color 0.15s",
  boxSizing: "border-box",
};
const inputWithIconFocus: CSSProperties = { ...inputWithIcon, borderColor: "#dc2626" };
const captchaCanvas: CSSProperties = { borderRadius: 10, border: "1px solid #fecaca" };
const primaryBtn: CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 10,
  padding: "16px 18px",
  borderRadius: 10,
  border: "none",
  background: "#dc2626",
  color: "#fff",
  fontSize: 17,
  fontWeight: 600,
  cursor: "pointer",
  transition: "background 0.15s",
};
const primaryBtnHover: CSSProperties = { ...primaryBtn, background: "#b91c1c" };
const ghostBtn: CSSProperties = { padding: "0 18px", borderRadius: 10, border: "1px solid #cbd5e1", background: "#fff", cursor: "pointer", color: "#dc2626", display: "flex", alignItems: "center" };
const linkBtn: CSSProperties = { background: "none", border: "none", color: "#dc2626", fontSize: 15, cursor: "pointer", justifySelf: "start", padding: 0 };
const roleButton: CSSProperties = { width: "100%", display: "flex", alignItems: "center", gap: 14, padding: "16px", borderRadius: 12, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", boxShadow: "0 1px 2px rgba(15, 23, 42, 0.03)", transition: "border-color 0.15s, box-shadow 0.15s, transform 0.15s" };
const roleButtonHover: CSSProperties = { ...roleButton, borderColor: "#fca5a5", boxShadow: "0 6px 16px rgba(220, 38, 38, 0.08)", transform: "translateY(-1px)" };
const roleIconBox: CSSProperties = { width: 42, height: 42, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, borderRadius: 11, background: "#fef2f2", color: "#dc2626", border: "1px solid #fee2e2" };
const roleArrow: CSSProperties = { marginLeft: "auto", display: "flex", color: "#dc2626", flexShrink: 0 };
const backButton: CSSProperties = { display: "inline-flex", alignItems: "center", gap: 8, background: "none", border: "none", color: "#dc2626", fontSize: 14.5, fontWeight: 500, cursor: "pointer", justifySelf: "start", padding: 0 };
