# Silent Shield — VAIC 2026 (ABG)

Cảnh báo sớm thay đổi học tập cần được quan tâm từ tín hiệu không xâm phạm — giúp Ban Lãnh đạo ưu tiên rà soát và bàn giao cho người hỗ trợ, có fairness + privacy đo được.

## Docs

| File | Nội dung |
|:-----|:---------|
| [AGENTS.md](AGENTS.md) | Goal, lane, do-not, verify (đọc trước khi code) |
| [docs/README.md](docs/README.md) | Mục lục tài liệu có đánh số |
| [Quy chế VAIC](docs/01-requirements/01-vaic-rules.md) | Ràng buộc cuộc thi |
| [Problems Brief](docs/01-requirements/02-problems-brief.md) | Nguồn mô tả bài toán và giải pháp |
| [Truy vết yêu cầu](docs/01-requirements/03-traceability.md) | Ánh xạ brief và các độ lệch còn mở |
| [PRD](docs/02-product/04-prd.md) | Phạm vi MVP |
| [Danh mục tín hiệu](docs/02-product/06-signal-catalog.md) | Tín hiệu MVP và ứng viên mở rộng |
| [Quyết định chọn đề](docs/03-project/01-topic-selection.md) | Cơ sở chọn Silent Shield |
| [Sprint](docs/03-project/03-sprint.md) | Board 48h |
| [Đội ngũ](docs/03-project/02-team.md) | Khảo sát và phân vai |

## Layout

```text
backend/     FastAPI
frontend/    Next.js (scaffold ở G01)
data/        Dữ liệu synthetic cho demo
docs/        Tài liệu team
scripts/     verify.ps1
```

`reference-Learning-Analytics-AI/` — local only (gitignored), lấy ý tưởng không copy nguyên repo.

## Team

| Prefix | Người | Lane |
|:------:|:------|:-----|
| H* | Hoàng | Agent, Backend, Deploy, PM KT |
| M* | Khánh Duy | ML + fairness |
| G* | Trường Giang | Data + FE |
| T* | Thu Trang | Hỗ trợ AI/Data |
| A* | Hạ Giang | BA + Pitch |
| V* | Văn Hải | Docs + demo script |
| D* | BTC nộp bài | Slide / video / live / AI log |

## Dev

```powershell
cd backend; pip install -e ".[dev]"; pytest -q
.\scripts\verify.ps1
```
