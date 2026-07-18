/**
 * Fail-closed empty state when advisor local demo fixtures are disabled.
 * Production / default path until G07 wires scoped server APIs (H36).
 */
export function AdvisorUnavailable({ surface }: { surface: string }) {
  return (
    <div
      id="cases"
      className="scroll-mt-5 rounded-2xl border border-slate-200 bg-white px-6 py-12 text-center shadow-sm"
      role="status"
      data-advisor-state="unavailable"
    >
      <p className="text-sm font-semibold text-slate-800">{surface} tạm thời không khả dụng</p>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">
        Hàng đợi GVCN cần API được scope phía server (H36). Frontend không fetch toàn bộ case rồi lọc
        client-side và không tự sinh fixture trên production. Bật{" "}
        <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">NEXT_PUBLIC_ADVISOR_LOCAL_DEMO=1</code>{" "}
        chỉ trên local/dev nếu cần prototype UI.
      </p>
    </div>
  );
}
