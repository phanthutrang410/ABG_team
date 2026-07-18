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
docker compose up -d db
cd backend; pip install -e ".[dev]"
# One-shot: 460 semester + 7360 linked attendance + ml_term_snapshot + attendance_week
python ..\scripts\bootstrap_d460.py
pytest -q
cd ..
.\scripts\verify.ps1
```

Requires `.env` from `.env.example` with `DATABASE_URL` and `LINKED_NAMESPACE_APPROVAL=approval:mvp-linked-v59-att:v1:acfb7d80dc3a`.

## Known limits (H09 / D460)

- **List ≠ 460:** `GET /review-cases` chỉ trả SV vượt ngưỡng ưu tiên rà soát (thường ~tens), không phải toàn bộ 460 đã import.
- **Local + Live API D460 Done:** semester 460 + attendance 7360 (hash `acfb7d80…`) + `materialize-ml` 460 + week rollup — [runbook §5.1](docs/04-engineering/06-deploy-runbook.md) · Live evidence [23-d460…](docs/03-project/23-d460-live-redeploy-evidence.md).
- **Auth (H39):** anon `/review-cases` → 401; demo seed `quanly`/`gvcn`/`demo` (password operator-only). List sau login ≈ tens (ngưỡng), không phải 460.
- **Vercel FE:** cần redeploy production để proxy `/auth/*` + login G07; API Live đã linked.
- Care case store: durable `app.review_case` trên Live `:d460`.
- Fairness nhóm: `insufficient_data` khi chưa có audit attribute được duyệt.
- Hybrid forecast (M07/M08): **FREEZE** — không ship.
- Agent Live: fail-closed `unavailable` nếu thiếu OpenAI key.