import type { ReasonCodeWithCopy } from "@/lib/copy";

/** Public-safe band codes (Data-ML §4). No raw model_score on UI. */
export type ReviewPriorityBand = "uu_tien_som" | "can_ra_soat";

export type MockReviewRow = {
  studentId: string;
  classId: string;
  reviewPriorityBand: ReviewPriorityBand;
  topFactor: string;
  reasonCodes: ReasonCodeWithCopy[];
};

/** Neutral band labels for shell display — not Data-ML §6 copy keys. */
export const REVIEW_PRIORITY_BAND_LABEL: Record<ReviewPriorityBand, string> = {
  uu_tien_som: "Ưu tiên sớm",
  can_ra_soat: "Cần rà soát",
};

/**
 * Mock until H02/G02 wire ReviewCase API.
 * Term-only evidence; attendance fail-closed (H15). No raw riskScore.
 */
export const MOCK_REVIEW_LIST: MockReviewRow[] = [
  {
    studentId: "SYN0003",
    classId: "10A1",
    reviewPriorityBand: "uu_tien_som",
    topFactor: "Điểm theo học kỳ giảm so với kỳ trước",
    reasonCodes: ["partial_term_only", "attendance_source_unapproved"],
  },
  {
    studentId: "SYN0012",
    classId: "10A2",
    reviewPriorityBand: "uu_tien_som",
    topFactor: "Điểm theo học kỳ dao động giữa các kỳ",
    reasonCodes: ["partial_term_only", "attendance_source_unapproved"],
  },
  {
    studentId: "SYN0027",
    classId: "11B1",
    reviewPriorityBand: "can_ra_soat",
    topFactor: "Điểm trung bình học kỳ thấp hơn kỳ trước",
    reasonCodes: ["partial_term_only", "attendance_source_unapproved"],
  },
];
