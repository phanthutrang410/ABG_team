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
| 03 | [Sprint](03-project/03-sprint.md) | Board 48 giờ: docs/contract do Hoàng sở hữu; build H/M/G/T; QA/release/presentation giang/Hải từ P2 |
| 04 | [Quyết định](03-project/04-decisions.md) | Các quyết định sản phẩm/kỹ thuật ngắn |
| 05 | [Nhật ký](03-project/05-worklog.md) | Nhật ký điều phối theo thời gian |
| 07 | [Release evidence](03-project/07-release-evidence.md) | Checklist bằng chứng CP1 / CP2 / nộp cuối / Demo Day |
| 08 | [Stories — giang](03-project/08-stories-giang.md) | P2+ UAT/review và asset slide/mô tả, không sửa docs nguồn |
| 09 | [Stories — Văn Hải](03-project/09-stories-van-hai.md) | P2+ QA `V07` (checklist+output), rehearsal/video/`V06`; **không** nộp CP2 |
| 10 | [D3 GitHub / PII-secret scan](03-project/10-d3-github-pii-secret-scan.md) | Evidence CP2: repo public + scan; SĐT đã redact |
| 12 | [H15 attendance approval prep](03-project/12-h15-attendance-approval-prep.md) | Prep only: chase checklist + amendment outline; H15 vẫn BLOCKED → data-owner |
| 13 | [H12b asset / claim-copy skeleton](03-project/13-h12b-asset-copy-skeleton.md) | Banner + claim matrix cho Hạ Giang D1; attendance = MVP; forecast/fusion = research/blocked |
| 16 | [Stories — Thu Trang](03-project/16-stories-thu-trang.md) | `V05` nộp Checkpoint 2 sau `D4r`; lane Agent xem Sprint §7 |

## 4. Engineering

| # | Tài liệu | Mục đích |
|:-:|:---------|:---------|
| 01 | [FPT AI API — lịch sử](04-engineering/01-fpt-ai-api.md) | Provider guide của H23–H26; build mới theo Decision #22 |
| 03 | [EPU reference — catalog trường](04-engineering/03-epu-reference-data-fields.md) | Các trường đang có trong EPU reference (V59, profile, transcript v5); cơ sở chọn/loại nguồn, không phải SIS production |
| 04 | [Hợp đồng tích hợp EPU](04-engineering/04-epu-data-integration-contract.md) | H10: nguồn không synthetic, taxonomy, pseudonym custody, data gate, schema chuẩn hóa |
| 05 | [Kiến trúc hệ thống tối thiểu](04-engineering/05-system-architecture.md) | Container, luồng dữ liệu, care/state boundary MVP; SoT mỏng cho H06b/H10/H07 |
| 06 | [Deploy / ops runbook](04-engineering/06-deploy-runbook.md) | Env, CORS, seed, health, smoke, rollback — **draft from arch; finalize at D4**; no secrets |
| 07 | [Persistence schema MVP](04-engineering/07-mvp-persistence-schema.md) | Thiết kế DB `dwh` versioned, mapping metadata legacy và gate import đã duyệt cho H19/H20 |
| 08 | [Data/ML scoring & fairness](04-engineering/08-data-ml-scoring-fairness-contract.md) | H10: features hai nhánh, coverage/`insufficient_data`, threshold, evaluation, fairness fail-closed |
| 08b | [Agent grounding & guardrails](04-engineering/08-agent-grounding-guardrails.md) | H11b canonical: I/O, 7 refusals, adversarial; runtime pointer `POST …/explanation` (khác số với Data-ML `08-`) |
| 09 | [Synthetic Data/ML contract (superseded)](04-engineering/09-synthetic-data-ml-fairness-contract-superseded.md) | Lịch sử synthetic — không dùng cho MVP path |
| 10 | [FE/Agent integration contract](04-engineering/10-fe-agent-integration-contract.md) | H11a/H11b schema + current delta: case-local `AgentPanel` có; Global Agent chưa ship |
| 11 | [Advisor-batch mail draft](04-engineering/11-advisor-batch-mail-draft.md) | FR-12: `GET /advisor-handoff-drafts` (H22 Done); G06 FE Copy/`mailto:` |
| 12 | [Agent runtime integration & hardening — lịch sử](04-engineering/12-agent-runtime-integration-plan.md) | H23–H26 Done (backend HTTP; mocked FPT); không phải provider/Global Agent target |
| 13 | [Weekly snapshot + Global Agent target architecture](04-engineering/13-weekly-snapshot-global-agent-architecture.md) | OpenAI target, mock feed tuần, durable delta/report, global shell, tool/RBAC và backlog H29–D6 |

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
