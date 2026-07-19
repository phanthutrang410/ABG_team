/**
 * Nhãn VI cho contributing-factor codes (M02) — fallback: hiển thị nguyên code.
 * Dùng chung dashboard + báo cáo tổng thể (plan.md §3.2); cùng bộ nhãn với
 * trang chi tiết case. Không tự thêm code ngoài catalog M02.
 */
export const FACTOR_LABEL: Record<string, string> = {
  gpa_below_target: "GPA kỳ gần nhất dưới mức tham chiếu",
  failed_credits_elevated: "Tín chỉ môn không đạt ở mức cao",
  grade_trend_declining: "Điểm trung bình giữa hai kỳ giảm",
  grade_volatility_elevated: "Độ phân tán điểm học phần cao",
  attendance_rate_below_target: "Tỷ lệ điểm danh thấp",
  attendance_trend_declining: "Chuyên cần giảm dần",
};
