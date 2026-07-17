# Tài liệu Silent Shield

Tài liệu được tổ chức theo luồng từ **yêu cầu nguồn** đến **đặc tả sản phẩm**, **thực thi dự án** và **hướng dẫn kỹ thuật**.

```text
docs/
├── README.md
├── 01-requirements/  # Nguồn yêu cầu và truy vết
├── 02-product/       # Đặc tả sản phẩm đã diễn giải
├── 03-project/       # Quyết định chọn đề và điều phối thực thi
└── 04-engineering/   # Hướng dẫn, tài liệu kỹ thuật
```

## 1. Requirements và nguồn yêu cầu

Đọc nhóm này trước để phân biệt nội dung do cuộc thi/brief yêu cầu với quyết định do team diễn giải.

| # | Tài liệu | Vai trò |
|:-:|:---------|:--------|
| 01 | [Quy chế VAIC](01-requirements/01-vaic-rules.md) | Ràng buộc cuộc thi và bài nộp |
| 02 | [Problems Brief](01-requirements/02-problems-brief.md) | Nguồn mô tả bài toán và giải pháp đích |
| 03 | [Truy vết yêu cầu](01-requirements/03-traceability.md) | Ánh xạ brief sang product docs, ghi quyết định diễn giải và độ lệch với scaffold |

## 2. Product

Đây là các tài liệu vận hành đã được team chuẩn hóa từ nguồn yêu cầu.

| # | Tài liệu | Mục đích |
|:-:|:---------|:---------|
| 01 | [Bài toán](02-product/01-problem.md) | Bài toán, đầu ra, thuật ngữ và success metrics |
| 02 | [Các bên liên quan](02-product/02-stakeholders.md) | Vai trò, quyền quyết định và quyền dữ liệu |
| 03 | [Quy trình](02-product/03-process.md) | Rà soát, phê duyệt, bàn giao và phản hồi |
| 04 | [PRD](02-product/04-prd.md) | Phạm vi và acceptance của MVP 48 giờ |
| 05 | [Đạo đức và an toàn](02-product/05-ethics.md) | Privacy, care, fairness và false-alarm controls |
| 06 | [Danh mục tín hiệu](02-product/06-signal-catalog.md) | Tín hiệu MVP, ứng viên hậu MVP, coverage và buffer |
| 07 | [User research](02-product/07-user-research.md) | Pain point theo đối tượng, nguyên nhân gốc |
| 08 | [BRD](02-product/08-brd.md) | Yêu cầu nghiệp vụ (BR-01→08), business rules, phân quyền T1/T3/T2, nghiệm thu |
| 09 | [Scope & To-be](02-product/09-scope-to-be.md) | In/out-of-scope sản phẩm đích, quy trình to-be nghiệp vụ, dependency và rủi ro |

## 3. Project và delivery

| # | Tài liệu | Mục đích |
|:-:|:---------|:---------|
| 01 | [Quyết định chọn đề](03-project/01-topic-selection.md) | Phân tích các đề và lý do chọn Silent Shield |
| 02 | [Đội ngũ](03-project/02-team.md) | Khảo sát thành viên và cơ sở phân vai |
| 03 | [Sprint](03-project/03-sprint.md) | Board 48 giờ: 4 gate + P0.5, phân task 6 lane, Depends/Evidence, gắn cổng VAIC |
| 04 | [Quyết định](03-project/04-decisions.md) | Các quyết định sản phẩm/kỹ thuật ngắn |
| 05 | [Nhật ký](03-project/05-worklog.md) | Nhật ký điều phối theo thời gian |

## 4. Engineering

| # | Tài liệu | Mục đích |
|:-:|:---------|:---------|
| 01 | [FPT AI API](04-engineering/01-fpt-ai-api.md) | Gọi FPT AI bằng API tương thích OpenAI |
| 02 | [Harness Engineering](04-engineering/02-harness-engineering.html) | HTML snapshot tham khảo về harness engineering; không phải source of truth của sản phẩm |

`02-harness-engineering.html` là trang được lưu từ nguồn bên ngoài và có thể cần network hoặc asset gốc để render đầy đủ. Không dùng nội dung trong đó như requirement nếu chưa được đưa vào PRD/decision.

## Thứ tự ưu tiên khi có mâu thuẫn

1. [Quy chế VAIC](01-requirements/01-vaic-rules.md).
2. Các ràng buộc privacy, care và fairness trong [Problems Brief](01-requirements/02-problems-brief.md).
3. Quyết định diễn giải trong [Truy vết yêu cầu](01-requirements/03-traceability.md).
4. Phạm vi MVP trong [PRD](02-product/04-prd.md).
5. Task board và quyết định triển khai trong [Project](03-project/).

## Quy ước tổ chức

- Thư mục dùng dạng `NN-topic`; file trong mỗi nhóm dùng `NN-kebab-case.ext`.
- `01-requirements` chỉ chứa nguồn yêu cầu và traceability, không chứa kế hoạch triển khai.
- `02-product` chỉ chứa tài liệu sản phẩm đã diễn giải, không lưu nguyên bản nguồn.
- `03-project` chứa quyết định lịch sử, phân công, sprint và worklog.
- `04-engineering` chứa hướng dẫn kỹ thuật và reference; reference không tự động trở thành requirement.
- Dữ liệu sinh viên thật, secrets và tài liệu ngoài phạm vi Silent Shield không được đưa vào repo.
- Khi di chuyển tài liệu, phải cập nhật liên kết trong toàn repo và chạy `scripts/verify.ps1 -Quick`.

Điểm vào: mọi thành viên đọc [RULES.md](../RULES.md); AI agent phải đọc thêm [AGENTS.md](../AGENTS.md) trước mỗi task.
