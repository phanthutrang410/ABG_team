import type { ReactNode } from "react";

/**
 * Presentational primitives shared by the advisor case queue — the local demo
 * (`AdvisorWorkspace`) and the server-backed real-data view
 * (`AdvisorServerWorkspace`). Pure/stateless: no data source, no RBAC decision,
 * so both branches render an identical shell.
 */

export type Filter =
  | "all"
  | "needs_action"
  | "follow_up_in_progress"
  | "monitoring"
  | "resolved";

export const FILTERS: { id: Filter; label: string }[] = [
  { id: "all", label: "Tất cả" },
  { id: "needs_action", label: "Cần tiếp nhận" },
  { id: "follow_up_in_progress", label: "Đang hỗ trợ" },
  { id: "monitoring", label: "Đang theo dõi" },
  { id: "resolved", label: "Đã hoàn tất" },
];

export type StatTone = "red" | "amber" | "sky" | "emerald";

export const STAT_CARDS: {
  id: Exclude<Filter, "all">;
  label: string;
  sub: string;
  tone: StatTone;
  icon: ReactNode;
}[] = [
  { id: "needs_action", label: "Cần tiếp nhận", sub: "Cần xác nhận", tone: "red", icon: <InboxIcon /> },
  { id: "follow_up_in_progress", label: "Đang hỗ trợ", sub: "Đã tiếp nhận", tone: "amber", icon: <HandsIcon /> },
  { id: "monitoring", label: "Đang theo dõi", sub: "Có thời hạn", tone: "sky", icon: <EyeIcon /> },
  { id: "resolved", label: "Đã hoàn tất", sub: "Vòng hoàn tất", tone: "emerald", icon: <CheckIcon /> },
];

const TONE: Record<StatTone, { iconWrap: string; num: string; activeRing: string }> = {
  red: { iconWrap: "bg-red-50 text-red-600", num: "text-red-600", activeRing: "border-red-300 ring-2 ring-red-100" },
  amber: { iconWrap: "bg-amber-50 text-amber-600", num: "text-amber-600", activeRing: "border-amber-300 ring-2 ring-amber-100" },
  sky: { iconWrap: "bg-sky-50 text-sky-600", num: "text-sky-600", activeRing: "border-sky-300 ring-2 ring-sky-100" },
  emerald: { iconWrap: "bg-emerald-50 text-emerald-600", num: "text-emerald-600", activeRing: "border-emerald-300 ring-2 ring-emerald-100" },
};

export function Hero({ total }: { total: number }) {
  return (
    <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-red-600 to-red-700 p-6 text-white shadow-sm">
      <div className="relative z-10 max-w-2xl">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-red-100">Không gian cố vấn</p>
        <h2 className="mt-2 text-2xl font-bold leading-tight">Case đã được giao cho tôi</h2>
        <p className="mt-3 text-sm leading-6 text-red-50">
          Chỉ hiển thị lý do bàn giao và dữ liệu tối thiểu để bắt đầu hỗ trợ.
          <br className="hidden sm:block" />
          Không có bảng xếp hạng, raw score hay case chưa được phê duyệt.
        </p>
      </div>
      <span className="absolute right-5 top-5 z-10 inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold text-white ring-1 ring-inset ring-white/25">
        <ShieldIcon />
        {total} case pseudonymous
      </span>
      <span aria-hidden className="pointer-events-none absolute -right-2 bottom-2 z-0 text-white/15">
        <HeartHandsIcon />
      </span>
    </section>
  );
}

export function StatCard({
  card,
  count,
  active,
  onSelect,
}: {
  card: (typeof STAT_CARDS)[number];
  count: number;
  active: boolean;
  onSelect: () => void;
}) {
  const tone = TONE[card.tone];
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={active}
      className={`group flex items-center justify-between gap-3 rounded-2xl border bg-white px-4 py-4 text-left shadow-sm transition-colors ${
        active ? tone.activeRing : "border-slate-200 hover:border-slate-300"
      }`}
    >
      <div className="flex items-center gap-3">
        <span className={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl ${tone.iconWrap}`}>{card.icon}</span>
        <div>
          <p className={`text-2xl font-bold leading-none ${tone.num}`}>{count}</p>
          <p className="mt-1.5 text-sm font-semibold text-slate-800">{card.label}</p>
          <p className="text-[11px] text-slate-400">{card.sub}</p>
        </div>
      </div>
      <span aria-hidden className="text-slate-300 transition-transform group-hover:translate-x-0.5">›</span>
    </button>
  );
}

export function DataPoint({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-white px-3 py-2">
      <dt className="text-[11px] text-slate-400">{label}</dt>
      <dd className="mt-0.5 text-sm font-bold text-slate-800">{value}</dd>
    </div>
  );
}

export function ActionButton({
  label,
  help,
  onClick,
  primary = false,
  disabled = false,
}: {
  label: string;
  help: string;
  onClick: () => void;
  primary?: boolean;
  disabled?: boolean;
}) {
  return (
    <div>
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        className={`w-full rounded-lg px-3 py-2.5 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-60 ${
          primary ? "bg-red-600 text-white hover:bg-red-700" : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
        }`}
      >
        {label}
      </button>
      <p className="mt-1.5 text-[11px] leading-4 text-slate-400">{help}</p>
    </div>
  );
}

export function defaultMonitorDate(): string {
  const date = new Date();
  date.setDate(date.getDate() + 14);
  return date.toISOString().slice(0, 10);
}

export function formatDate(value: string): string {
  return new Date(value).toLocaleDateString("vi-VN");
}

export function formatDateTime(value: string): string {
  return new Date(value).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/* ---------- Icons (line style, inherit currentColor) ---------- */

const statSvg = {
  width: 22,
  height: 22,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

function InboxIcon() {
  return (
    <svg {...statSvg}>
      <path d="M22 12h-6l-2 3h-4l-2-3H2" />
      <path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
    </svg>
  );
}

function HandsIcon() {
  return (
    <svg {...statSvg}>
      <path d="M20 11a2 2 0 0 0-2-2h-3l-1.5-5.5a1.5 1.5 0 0 0-3 .3V9" />
      <path d="M4 13a2 2 0 0 1 2-2h2l2 4h4a2 2 0 0 1 0 4H9l-3-2H4z" />
    </svg>
  );
}

function EyeIcon() {
  return (
    <svg {...statSvg}>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg {...statSvg}>
      <circle cx="12" cy="12" r="9" />
      <path d="m8.5 12 2.5 2.5 4.5-5" />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

export function BellIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
      <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
    </svg>
  );
}

function HeartHandsIcon() {
  return (
    <svg width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 21s-6.5-4-9-8.5a4.2 4.2 0 0 1 7.2-4.2L12 9l1.8-.7A4.2 4.2 0 0 1 21 12.5C18.5 17 12 21 12 21z" fill="currentColor" fillOpacity="0.35" />
    </svg>
  );
}
