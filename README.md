# Silent Shield — VAIC 2026 (ABG)

Cảnh báo sớm thay đổi học tập cần được quan tâm từ tín hiệu không xâm phạm — giúp Ban Lãnh đạo ưu tiên rà soát và bàn giao cho người hỗ trợ, có fairness + privacy đo được.

## Docs

| File | Nội dung |
|:-----|:---------|
| [RULES.md](RULES.md) | Quy tắc chung, goal, scope và Definition of Done cho cả team |
| [AGENTS.md](AGENTS.md) | Luồng bắt buộc của agent: preflight, read router, contract, test, verify và handoff |
| [docs/README.md](docs/README.md) | Mục lục tài liệu có đánh số |
| [Quy chế VAIC](docs/01-requirements/01-vaic-rules.md) | Ràng buộc cuộc thi |
| [Problems Brief](docs/01-requirements/02-problems-brief.md) | Nguồn mô tả bài toán và giải pháp |
| [Truy vết yêu cầu](docs/01-requirements/03-traceability.md) | Ánh xạ brief và các độ lệch còn mở |
| [PRD](docs/02-product/04-prd.md) | Phạm vi MVP |
| [Danh mục tín hiệu](docs/02-product/06-signal-catalog.md) | Tín hiệu MVP và ứng viên mở rộng |
| [Hợp đồng dữ liệu EPU](docs/04-engineering/04-epu-data-integration-contract.md) | Data gate, chuẩn hóa và handoff fixture cho Hoàng |
| [Quyết định chọn đề](docs/03-project/01-topic-selection.md) | Cơ sở chọn Silent Shield |
| [Sprint](docs/03-project/03-sprint.md) | Board 48h |
| [Đội ngũ](docs/03-project/02-team.md) | Khảo sát và phân vai |

## Layout

```text
backend/     FastAPI
frontend/    Next.js (scaffold ở G01)
data/        Artifact cũ; không nạp synthetic, export EPU đã pseudonymize không commit raw/PII
docs/        Tài liệu team
scripts/     verify.ps1
```

`reference-Learning-Analytics-AI/` — local only (gitignored), lấy ý tưởng không copy nguyên repo.

## Team

| Workstream ID | Người | Lane |
|:------:|:------|:-----|
| H* | Hoàng | Canonical docs/contract, Backend, Deploy |
| M* | Khánh Duy | Data/ML, semester baseline, hybrid research |
| G* | Trường Giang | Frontend build |
| T* | Thu Trang | Agent build/guardrails |
| A* | Hạ Giang | P2+ UAT/review, slide + asset mô tả |
| V* | Văn Hải | P2+ QA release, rehearsal, submission |
| D* | Delivery asset | Owner được ghi theo từng task trên Sprint |

Owner thực tế và dependency luôn theo [Sprint](docs/03-project/03-sprint.md); không suy ra owner chỉ từ ID.

## Dev

```powershell
cd backend; pip install -e ".[dev]"; pytest -q
.\scripts\verify.ps1
```
