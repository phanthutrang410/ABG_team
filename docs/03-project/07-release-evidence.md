# Release Evidence Checklist

> **Owner tài liệu/evidence:** Hoàng. **Owner QA/submission từ P2:** Văn Hải. giang chuẩn bị asset slide/mô tả sau khi copy/evidence đã khóa.
>
> Chỉ tick khi có evidence thật. Nếu dependency chưa Done, ghi BLOCKED → ID trong cột Evidence.

## 1. Checkpoint 1: 18/7 11:00

> **H13 Done (18/7):** CP1 đã nộp form BTC. Nội dung 4 trường: [11-h13-cp1-btc-draft.md](11-h13-cp1-btc-draft.md). Receipt giữ ngoài repo (không commit PII/screenshot có identifier thừa).

| Mục | Owner | Task nguồn | Evidence | Status |
|:--|:--|:--|:--|:--|
| Tên dự án, track, mô tả, hướng tiếp cận | Hoàng | H13 | [11-h13-cp1-btc-draft.md](11-h13-cp1-btc-draft.md) · paste-ready ~04:25 18/7 | [x] |
| Đã nộp form/link BTC | Hoàng | H13 | Human submit 18/7 — form BTC ngoài repo | [x] |
| Xác nhận BTC đã nhận | Hoàng | H13 | Receipt giữ ngoài repo (owner custody) | [x] |

## 2. Checkpoint 2: 18/7 23:00

| Mục | Owner | Task nguồn | Evidence | Status |
|:--|:--|:--|:--|:--|
| Live URL hoạt động (smoke lần 1) | Hoàng | D4a (shell) | **D4a shell 2026-07-18 ~06:05 +07:** FE `http://52.74.255.88:3000` · API `http://52.74.255.88:8000/health` → `{"status":"ok","service":"silent-shield","database":false}` · CORS ACAO=`http://52.74.255.88:3000` · rollback: instance `i-0b0576945d080cb3f`, API digest `sha256:7a6ba16516bcc33beb58f4497f0583b220061e2f502f7ff913656319c523a23b`, FE digest `sha256:58ccf51321418291ba8ac44b9034328e56542963f3dadb3764ef8539554c5973` · runbook [06-deploy-runbook.md](../04-engineering/06-deploy-runbook.md) · **not D4b** product list→case | [x] shell / [ ] D4b |
| Smoke test ẩn danh độc lập lần 1 | Văn Hải | V07 |  | [ ] |
| Fix → redeploy → re-smoke | Hoàng | D4r |  | [ ] |
| GitHub public, PII/secret scan | Hoàng | D3 | [10-d3-github-pii-secret-scan.md](10-d3-github-pii-secret-scan.md) · https://github.com/phanthutrang410/ABG_team | [x] |
| BTC nhận 2 URL | Văn Hải | V05 |  | [ ] |
| Hoàng hoàn thiện evidence CP2 | Hoàng | H16 (sau V07, V05) |  | [ ] |

## 3. Đóng cổng nộp cuối: 19/7 11:00

| Mục | Owner | Task nguồn | Evidence | Status |
|:--|:--|:--|:--|:--|
| Slide + asset mô tả | giang | D1 |  | [ ] |
| Video ≤5 phút, đúng URL | Văn Hải | D2 |  | [ ] |
| GitHub public + README | Hoàng | D3, H09 |  | [ ] |
| Live URL smoke cuối | Hoàng | D4r, H16 |  | [ ] |
| AI collaboration log hoàn thiện | Hoàng | D5 |  | [ ] |
| Form cuối đã gửi | Văn Hải | V06 |  | [ ] |
| Xác nhận BTC đã nhận | Văn Hải | V06 |  | [ ] |

## 4. Demo Day: 19/7 15:30 (nếu vào Top 10)

| Mục | Owner | Task nguồn | Evidence | Status |
|:--|:--|:--|:--|:--|
| Script pitch 4 phút + Q&A 2 phút | Văn Hải | V02 |  | [ ] |
| Rehearsal live | Văn Hải | V02, D4r |  | [ ] |
| Live URL sẵn sàng | Hoàng | D4r |  | [ ] |

## 5. Quy ước

- Hoàng cập nhật Markdown/evidence chuẩn sau handoff QA; Văn Hải không tự sửa checklist.
- CP2: không nộp `V05` trước `D4r` xanh. `H16` phải khóa evidence CP2 sau `V07` + `V05` (và gap `A05` nếu có).
- Asset slide/mô tả không được thay đổi scope/copy canonical do Hoàng khóa (`H12a` runtime; `H12b` banner/asset).
- Nếu một mục bị block, ghi dependency cụ thể và báo owner, không dùng screenshot/mock thay thế.

## 5b. Source unlock (M05b + H15) — 18/7 ~07:05

| Mục | Owner | Task | Evidence | Status |
|:--|:--|:--|:--|:--|
| Semester approved (M05b) | Hoàng | M05b | [14-m05b…](14-m05b-semester-approval.md) · decision #18 · hash `34a53298…` / 460 · raw ngoài git | [x] |
| Attendance approved (H15) | Hoàng | H15 | [12-h15…](12-h15-attendance-approval-prep.md) · fixture `data/approved/attendance/mvp_attendance_over_time.json` · hash `f65573ad…` / 15 events | [x] |
| Source gate allowlist | Hoàng | H15/M05a | `mvp-attendance-over-time` in `SOURCE_ALLOWLIST`; `tests/test_source_gate.py` 26 pass | [x] |

## 5c. Agent runtime FR-08 (H23–H26) — 18/7 ~11:30

> Backend HTTP E2E only. **Không** claim FE Agent UI Done, production RBAC, hoặc live FPT smoke.

| Mục | Owner | Task | Evidence | Status |
|:--|:--|:--|:--|:--|
| Server-derived AgentContext | Hoàng | H23 | `backend/tests/test_h23_agent_context.py` · M02 factor `grade_trend_declining` / version `m02-baseline-0.1` · `provider_call_allowed` fail-closed | [x] |
| `POST /review-cases/{case_id}/explanation` | Hoàng | H24 | `backend/tests/test_h24_agent_api.py` · OpenAPI body ⊆ `{intent,question,locale}` · demo identity (not production RBAC) · zero model calls on refuse/stale/insufficient | [x] |
| Structured grounding + FPT harden | Hoàng | H25 | `backend/tests/test_h25_grounding.py` + `test_h25_fpt_transport.py` · no raw question in provider payload · plan allowlist · transport maps to `unavailable` | [x] |
| Mocked HTTP E2E M02→H02→context→fake FPT→POST | Hoàng | H26 | `backend/tests/test_h26_agent_e2e.py` · happy + adversarial + `model_unavailable` · health/OpenAPI surface | [x] |
| Targeted agent suite | Hoàng | H26 | `python -m pytest -q tests/test_h26_agent_e2e.py tests/test_h23_agent_context.py tests/test_h24_agent_api.py tests/test_h25_grounding.py tests/test_h25_fpt_transport.py tests/agent/` → **130 passed, 1 skipped** | [x] |
| Full verify | Hoàng | H26 | `.\scripts\verify.ps1` → **410 passed, 1 skipped** · Ruff clean · FE lint/build green · `git diff --check` clean | [x] |
| Live FPT smoke | Hoàng | H26 | **SKIP** — no approved key/deploy window this session; documented skip in `test_h26_live_fpt_smoke_skipped_by_default` | [ ] SKIP |
| FE Agent UI / production RBAC | — | — | Out of scope H23–H26; H11b still needs G05 consumer docs; UI is separate FE task | [ ] N/A |

## 6. Fill template (H05b)

Khi điền cột Evidence, dùng form trong [templates/release-evidence-item.template.md](templates/release-evidence-item.template.md). Checklist ở trên vẫn là nguồn trạng thái; template chỉ chuẩn hóa cách ghi bằng chứng.
