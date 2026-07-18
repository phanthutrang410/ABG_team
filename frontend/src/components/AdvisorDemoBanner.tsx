export function AdvisorDemoBanner({ detail }: { detail: string }) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-950">
      <span className="rounded-full bg-amber-200 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide">
        Dữ liệu demo
      </span>
      <p className="min-w-[240px] flex-1 text-sm leading-5">{detail}</p>
      <span className="text-xs font-medium text-amber-800">Không ghi database · không phải RBAC backend</span>
    </div>
  );
}
