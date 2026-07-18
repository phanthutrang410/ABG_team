"use client";

/**
 * Shared pager for the advisor demo lists (Case của tôi, Lớp & sinh viên, Lịch theo dõi).
 *
 * Presentational only: the parent owns `page` state and slices its data with
 * `paginateAdvisorQueue`, then passes the resolved bounds here. `noun` labels the
 * range summary in Vietnamese (e.g. "case", "sinh viên", "kết quả").
 */
export function QueuePagination({
  start,
  end,
  total,
  page,
  totalPages,
  noun,
  onChange,
}: {
  start: number;
  end: number;
  total: number;
  page: number;
  totalPages: number;
  noun: string;
  onChange: (page: number) => void;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-5 py-3 text-xs text-slate-500">
      <span>
        Hiển thị <span className="font-semibold text-slate-700">{start + 1}–{end}</span> trên {total} {noun}
      </span>
      <nav className="flex items-center gap-1" aria-label="Phân trang">
        <PageButton label="‹" ariaLabel="Trang trước" disabled={page <= 1} onClick={() => onChange(page - 1)} />
        {Array.from({ length: totalPages }, (_, index) => index + 1).map((n) => (
          <PageButton key={n} label={String(n)} ariaLabel={`Trang ${n}`} active={n === page} onClick={() => onChange(n)} />
        ))}
        <PageButton label="›" ariaLabel="Trang sau" disabled={page >= totalPages} onClick={() => onChange(page + 1)} />
      </nav>
    </div>
  );
}

function PageButton({
  label,
  ariaLabel,
  active = false,
  disabled = false,
  onClick,
}: {
  label: string;
  ariaLabel: string;
  active?: boolean;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      aria-current={active ? "page" : undefined}
      className={`flex h-8 min-w-8 items-center justify-center rounded-lg border px-2 text-xs font-semibold transition-colors ${
        active
          ? "border-red-600 bg-red-600 text-white"
          : "border-slate-200 bg-white text-slate-600 hover:border-red-200 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-200 disabled:hover:text-slate-600"
      }`}
    >
      {label}
    </button>
  );
}
