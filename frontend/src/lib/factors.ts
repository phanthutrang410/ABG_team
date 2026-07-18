/**
 * Nhãn VI cho contributing-factor codes (M02) — fallback: hiển thị nguyên code.
 * Dùng chung dashboard + báo cáo tổng thể (plan.md §3.2); cùng bộ nhãn với
 * trang chi tiết case. Không tự thêm code ngoài catalog M02.
 */
export const FACTOR_LABEL: Record<string, string> = {
  grade_trend_declining: "Kết quả học tập giảm",
  grade_volatility_elevated: "Điểm biến động giữa các kỳ",
  attendance_rate_below_target: "Tỷ lệ điểm danh thấp",
  attendance_trend_declining: "Chuyên cần giảm dần",
};
