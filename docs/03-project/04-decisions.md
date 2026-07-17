# Quyết định

1. **ML vs LLM** — Model ghi mức độ ưu tiên; LLM chỉ giải thích, không bịa xác suất.
2. **Privacy** — Chỉ tín hiệu không xâm phạm (xem [Ethics](../02-product/05-ethics.md)).
3. **Care** — Handoff cho người; không workflow phạt tự động.
4. **Fairness** — Metric nhóm là MVP, không phải nice-to-have.
5. **Stack** — FastAPI + Next.js; lấy *ý tưởng* từ EduInsight local, không vendor cả repo cũ vào bài nộp.
6. **LLM primary** — FPT AI Inference (mkp-api.fptcloud.com, OpenAI SDK + đổi base_url). Backup: OpenAI/Gemini. Agent tool-calling ưu tiên Qwen/Qwen3-32B. Deploy BE trên AWS (không dùng Render).
7. **Primary system user** — Ban Lãnh đạo Khoa/Trường rà soát và phê duyệt chuyển tiếp; GVCN/cố vấn nhận case đã duyệt và thực hiện chăm sóc.
8. **Product language** — Score chỉ là giá trị nội bộ; UI dùng “mức độ ưu tiên rà soát” và trạng thái case, không gắn nhãn sinh viên.
9. **48h signal scope** — MVP chỉ dùng feature điểm theo học kỳ, coverage và freshness. Điểm danh theo thời gian chỉ là hướng Post-MVP sau source approval, privacy review và contract update; LMS/tín chỉ/CLB/thư viện/campus cũng hậu MVP.
10. **Brief interpretation** — Các xung đột và khoảng trống được ghi tại [Truy vết yêu cầu](../01-requirements/03-traceability.md); không tự biến đề xuất trong brief thành feature đã cam kết.
11. **D5 AI log** — Thủ công 48h: mỗi người tự ghi manifest.csv + link online; evidence thô (nếu có) nộp Drive, không commit. Không dùng git history thay nhật ký AI. Xem [.ai-log/README.md](../../.ai-log/README.md).
12. **Nguồn EPU** — Dừng dùng/generate synthetic. Chỉ nạp export EPU đã qua source gate (owner, quyền sử dụng, hash, PII exclusion); chuẩn hóa theo [contract EPU](../04-engineering/04-epu-data-integration-contract.md). Thiếu coverage/nhóm audit/mapping thì trả insufficient_data, không bù bằng dữ liệu giả.
13. **Hybrid research gate** — Duy nghiên cứu feature semester + attendance forecasting ở M07. Chỉ khi Hoàng hoàn thiện H14/H15 từ export điểm danh được data owner phê duyệt mới mở M08/T04; không đưa research này vào CP2 hoặc gọi output công khai là dropout risk.
14. **Phân công 18/7** — Hoàng là owner duy nhất của docs/contract/evidence Markdown; build thuộc Hoàng, Duy, Giang và Trang. giang/Hải chỉ nhận P2/P3 QA, review, asset trình bày và submission theo Sprint.
