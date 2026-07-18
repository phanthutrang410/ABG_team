# Silent Shield — Team Rules

> Quy tắc chung cho mọi thành viên. AI agent phải đọc thêm [AGENTS.md](AGENTS.md) trước mỗi task để thực hiện đúng task loop, test, verify và handoff.

## 1. Nguồn chuẩn

Khi có mâu thuẫn, áp dụng theo thứ tự:

1. [Quy chế VAIC](docs/01-requirements/01-vaic-rules.md).
2. Privacy, care và fairness trong [Problems Brief](docs/01-requirements/02-problems-brief.md).
3. [Traceability](docs/01-requirements/03-traceability.md) và quyết định đã chốt.
4. [PRD MVP](docs/02-product/04-prd.md).
5. Engineering contract/ADR được duyệt.
6. [Sprint](docs/03-project/03-sprint.md) và task hiện hành.

Reference clone, mock, session handoff và root draft chỉ là ngữ cảnh, không phải requirement.

## 2. Goal và rubric bắt buộc

Demo live trước **11:00 19/7/2026**; nộp đủ slide, video ≤5 phút, GitHub, Live URL và AI log.

- **Privacy:** không giám sát chat/email/camera/mic; chỉ dùng bản trích xuất EPU đã được owner phê duyệt, pseudonymize và tối thiểu hóa trường dữ liệu.
- **Care:** không chẩn đoán, dán nhãn hoặc kỷ luật tự động; con người duyệt trước handoff.
- **Fairness:** chỉ công bố metric nhóm khi có thuộc tính audit được phê duyệt, ground truth, mẫu số và cỡ mẫu; nếu thiếu thì trả `insufficient_data`.
- **False alarm + explainability:** demo tác động ngưỡng và factors từ model/API.

## 3. Ranh giới sản phẩm

- MVP đại học dùng điểm theo học kỳ và điểm danh theo thời gian từ nguồn EPU/điểm danh đã duyệt; không tạo chuỗi chuyên cần/tuần để bù dữ liệu thiếu và không mở rộng Wellbeing, LMS/RAG, adaptive tutor, OCR/TTS hay career. **Ngoại lệ MVP demo (decision #18):** team approver có thể duyệt snapshot semester V59 ngoài git và một nguồn điểm danh allowlisted `mvp-attendance-over-time`; vẫn cấm legacy synthetic đã liệt kê và PII trong repo.
- Không đưa PII thật, thông tin liên hệ cá nhân không cần thiết, secrets hoặc raw AI sessions vào repo/evidence.
- Không commit `reference-Learning-Analytics-AI/`.
- Thuộc tính nhóm cho fairness chỉ được dùng khi đã có nguồn và phê duyệt riêng; luôn tách khỏi scoring, explanation và public case API.
- Model có thể giữ score nội bộ; UI/API nghiệp vụ chỉ hiển thị mức ưu tiên rà soát, không raw score/xác suất/trọng số.
- LLM chỉ giải thích output model/API; không tính/sửa score, đoán nguyên nhân, đổi trạng thái hoặc tự liên hệ.
- Coverage thấp/cũ phải trả `insufficient_data`; không biến thiếu dữ liệu thành “ổn định”.
- UI dùng tiếng Việt trung lập; không dùng màu làm tín hiệu duy nhất.

## 4. Quy ước làm việc

- Mỗi task có **một owner chịu trách nhiệm đầu ra**; không bắt buộc gán thêm người vào vai trò nghiệm thu độc lập. Board phải ghi outcome/artifact, dependency task ID, điều kiện bắt đầu, kiểm chứng và evidence/DoD để thay cho việc phụ thuộc vào tên người nghiệm thu.
- Task nên hoàn thành trong 2–4 giờ; task lớn hơn phải tách theo outcome/contract.
- Interface qua hai lane phải có schema + validated fixture + kiểm thử; task consumer chỉ được bắt đầu khi task provider đã Done và evidence đã có.
- Nếu chưa thể thực hiện vì đầu vào chưa hoàn tất, status phải ghi `BLOCKED → <task ID>`; không tự đổi contract, bịa fixture hay suy luận thay input.
- Không ghi đè thay đổi ngoài task, không dùng git destructive command.
- Branch: `feature/<task-id>-<short>`; commit: `feat:` / `fix:` / `docs:` / `test:` / `chore:` khi được giao commit.
- Không tự commit, push, merge, deploy hoặc submit nếu task chưa giao quyền.

## 5. Khi nào được coi là Done

- Acceptance/FR/rubric đạt bằng hành vi kiểm chứng được.
- Test phù hợp và verify đã chạy; mọi bước skip/fail được ghi rõ.
- Contract, producer, consumer và fixture liên quan đồng bộ.
- Evidence tồn tại, không chứa PII/secret; diff không có unrelated change.
- Sprint/worklog và AI log được cập nhật khi task yêu cầu.

Quick check: `.\scripts\verify.ps1 -Quick` · Full handoff/gate: `.\scripts\verify.ps1`.

Chi tiết luồng bắt buộc dành cho agent: [AGENTS.md](AGENTS.md).
