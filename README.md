# Silent Shield — VAIC 2026 (ABG)

Cảnh báo sớm nguy cơ bỏ học / khủng hoảng từ tín hiệu không xâm phạm — hỗ trợ GV & tư vấn can thiệp, có fairness + privacy.

## Docs

| File | Nội dung |
|:-----|:---------|
| [AGENTS.md](AGENTS.md) | Goal, lane, do-not, verify (đọc trước khi code) |
| [docs/README.md](docs/README.md) | Mục lục |
| [docs/sprint.md](docs/sprint.md) | Board 48h |
| [docs/prd.md](docs/prd.md) | PRD ngắn |
| [docs/briefs-analysis.md](docs/briefs-analysis.md) | Chọn đề vs EduInsight |
| [docs/vaic-2026.md](docs/vaic-2026.md) | Quy chế cuộc thi |
| [docs/team-survey.md](docs/team-survey.md) | Khảo sát & phân vai |

## Layout

```text
backend/     FastAPI
frontend/    Next.js (scaffold ở G01)
data/        Synthetic K-12
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
