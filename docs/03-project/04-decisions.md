# Quyết định

1. **ML vs LLM** — Model ghi mức độ ưu tiên; LLM chỉ giải thích, không bịa xác suất.
2. **Privacy** — Chỉ tín hiệu không xâm phạm (xem [Ethics](../02-product/05-ethics.md)).
3. **Care** — Handoff cho người; không workflow phạt tự động.
4. **Fairness** — Metric nhóm là MVP, không phải nice-to-have.
5. **Stack** — FastAPI + Next.js; lấy *ý tưởng* từ EduInsight local, không vendor cả repo cũ vào bài nộp.
6. **LLM primary** — FPT AI Inference (`mkp-api.fptcloud.com`, OpenAI SDK + đổi `base_url`). Backup: OpenAI/Gemini. Agent tool-calling ưu tiên `Qwen/Qwen3-32B`. Deploy BE trên AWS (không dùng Render).
7. **Primary system user** — Ban Lãnh đạo Khoa/Trường rà soát và phê duyệt chuyển tiếp; GVCN/cố vấn nhận case đã duyệt và thực hiện chăm sóc.
8. **Product language** — Score chỉ là giá trị nội bộ; UI dùng “mức độ ưu tiên rà soát” và trạng thái case, không gắn nhãn sinh viên.
9. **48h signal scope** — Chỉ điểm và chuyên cần theo thời gian; các tín hiệu LMS/tín chỉ/CLB/thư viện/campus trong brief là hậu MVP và phải qua privacy/fairness review.
10. **Brief interpretation** — Các xung đột và khoảng trống được ghi tại [Truy vết yêu cầu](../01-requirements/03-traceability.md); không tự biến đề xuất trong brief thành feature đã cam kết.
11. **D5 AI log** — Thủ công 48h: mỗi người tự ghi `manifest.csv` + link online; evidence thô (nếu có) nộp Drive, không commit. Không dùng git history thay nhật ký AI. [`.ai-log/README.md`](../../.ai-log/README.md).
