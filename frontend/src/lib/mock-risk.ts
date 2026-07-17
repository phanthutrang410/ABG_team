export type RiskStudent = {
  studentId: string;
  classId: string;
  riskScore: number;
  label: string;
  topFactor: string;
};

/** Mock until H02 API is wired (G02). */
export const MOCK_RISK_LIST: RiskStudent[] = [
  {
    studentId: "SYN0003",
    classId: "10A1",
    riskScore: 0.78,
    label: "Cần quan tâm",
    topFactor: "Xu hướng điểm danh giảm",
  },
  {
    studentId: "SYN0012",
    classId: "10A2",
    riskScore: 0.71,
    label: "Cần quan tâm",
    topFactor: "Điểm dao động mạnh",
  },
  {
    studentId: "SYN0027",
    classId: "11B1",
    riskScore: 0.65,
    label: "Theo dõi thêm",
    topFactor: "Điểm trung bình giảm 3 tuần",
  },
];
