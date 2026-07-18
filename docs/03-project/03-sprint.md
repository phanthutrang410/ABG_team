# Sprint — Silent Shield (17–19/7/2026)

> Nguồn chuẩn: [Quy chế VAIC](../01-requirements/01-vaic-rules.md) · [PRD MVP](../02-product/04-prd.md) · [Process](../02-product/03-process.md) · [RULES.md](../../RULES.md).
>
> **Điều chỉnh phân công 18/7:** Hoàng là owner duy nhất hoàn thiện tài liệu/contract nguồn chuẩn. Build tập trung vào Hoàng, Khánh Duy, **Giang** (FE) và Thu Trang. **Hạ Giang** (board ID `giang`) và Văn Hải nhận task từ P2: QA/UAT/claim/slide skeleton và release smoke/submission — không sửa canonical docs/code.
>
> **Chặn phạm vi hybrid (forecasting):** Freeze hoàn toàn `M07`/`H14`/`M08`/`H17`/`T04` tới sau submission. Điểm danh theo thời gian **thuộc MVP** (sau `H15`); thiếu nguồn → `insufficient_data`; **không** thay bằng synthetic để claim E2E.
>
> **Realign chốt ~05:45 18/7:** Direction giữ nguyên (prototype care/review, không claim dự báo dropout đã chứng minh). Wave update: `H06a-r`/`H11a-r` Done; `H06b` harden landed; `D4a` Live shell Done; `G05`/`T03` unblocked. Chi tiết §1.2 + board §3.

**Quy ước tên:** **Giang** = Nguyễn Trường Giang (frontend). **Hạ Giang** = Trần Hạ Giang (UAT / claim-copy / slide skeleton; board ID `giang`). Không viết tắt “giang” khi phân công miệng — luôn dùng **Hạ Giang** vs **Giang**. ID task ổn định; cột Owner là nguồn phân công.

| Thành viên | Lane đang chịu trách nhiệm | Không chịu trách nhiệm |
|:--|:--|:--|
| Hoàng | Tất cả tài liệu/contract nguồn chuẩn; backend/API; deploy; tài liệu release | Không tự viết model/fusion của Duy |
| Khánh Duy | Data/ML, source validation, baseline semester model | Không hoàn thiện Markdown contract/PRD; không làm hybrid tới sau submission |
| Giang | Frontend integration và UI | Không tự chốt copy/contract |
| Thu Trang | Agent adapter, grounding/refusal tests | Không tự tính/sửa mức ưu tiên |
| Hạ Giang (`giang`) | UAT, claim-copy review, slide + asset skeleton/mô tả | Không sửa canonical docs hoặc code; không nhầm với Giang (FE) |
| Văn Hải | QA release, smoke độc lập, script/video/submission, AI-log rà | Không sửa canonical docs, deploy hoặc code |

## 1. Cổng BTC và gate nội bộ

| Cổng BTC | Deadline | Deliverable | Gate nội bộ |
|:--|:--:|:--|:--|
| Checkpoint 1 | 11:00 T7 18/7 | Tên, track, mô tả ngắn, hướng tiếp cận | P1 |
| Checkpoint 2 | 23:00 T7 18/7 | Live URL + GitHub public | P2 |
| Đóng cổng | 11:00 CN 19/7 | Slide, video ≤5 phút, GitHub, Live URL, mô tả, AI log | P3 |
| Demo Day (nếu Top 10) | 15:30 CN 19/7 | Pitch 4′ + Q&A 2′ | Rehearsal P3 |

| Gate | Thời gian | Focus | Exit criteria | Trạng thái |
|:--|:--|:--|:--|:--|
| P0 | 17/7 11:00–15:00 | Scaffold | Health, FE shell | [x] (M01 Done — PR #16) |
| P0.5 | kế hoạch 17/7 22:30–18/7 00:30 | Contract lock | `H05a` + `M04` Done; schema/code chỉ theo contract | **[x] Done** — `H05a` + `M04` + `H10` (mốc cũ đã trễ) |
| P1 | recovery 18/7 sáng → CP1 | Vertical slice | Baseline điểm theo kỳ + điểm danh theo thời gian + CP1 | Mở — `M05b`/`H15` Done; còn `M06`… |
| P2 | 18/7 11:00–23:00 | Rubric + live | UI/API/test + QA→fix→re-smoke + CP2 | **D4b Done** — còn V07+A05→D4r→V05 |
| P3 | 18/7 23:00–19/7 11:00 | Release | Docs cuối, slide/video, AI log, form nộp | Chưa |

### 1.1 Recovery P0.5 → P1 (chốt lúc ~02:03 +07)

| Việc | Owner | Mục tiêu mới | Ghi chú |
|:--|:--|:--|:--|
| `H05a` minimum contract/state | Hoàng | ASAP · trước 03:30 | **Done** — mở `H06b`/`H07` |
| `M04` handoff Data/ML | Khánh Duy | ASAP · trước 03:30 | **Done** — [handoff](10-m04-data-ml-handoff.md) |
| `H10` contract EPU/decision | Hoàng | ngay sau `H05a`+`M04` · ~04:00 | **Done** (mốc 02:00 đã trễ) — EPU + Data-ML + decision #17 |
| `H05b` AI-log + release template | Hoàng | sau `H05a` · trước V08 | **Done** — mở `V08` |
| CP1 (`H13`) | Hoàng | 11:00 | **Done** — form BTC đã nộp; không claim hybrid |

Deadline cũ P0.5 00:30 / `H10` 02:00 chỉ còn giá trị lịch sử. Board dưới dùng mốc recovery + realign §1.2.

### 1.2 Realign execution (chốt ~05:45 +07 18/7)

Baseline khóa sau review progress/direction. **Không đổi** product direction; **đổi** thứ tự/DoD/dependency.

| # | Quyết định |
|:--|:--|
| 1 | `H06a` → **REOPEN** semantic (coverage/band/factors/`dataset_version` khớp Data-ML §3; regression tests) |
| 2 | `H11a` → **REVALIDATE** (`H06a-r` xong); tạm chặn consumer cuối `G05`/`T03` tới khi revalidate Done |
| 3 | `D3` giữ **Done** — residual Git history accept cho CP2; trước final: quyết định clean submission repo **hoặc** history remediation có phê duyệt |
| 4 | Ba nhánh song song: **Data** `M05a→M05b→M06→H20→H08→M02`; **Profile** `M01→H18`; **Contract safety** `H06a-r→H11a-r` |
| 5 | `T03` guard/refusal chạy sau `H11a-r` — **không** cần chờ live API (`H02`) |
| 6 | Tách `D4a` deploy shell / `D4b` product smoke; `A05` là đầu vào **bắt buộc** của `D4r` |
| 7 | Go/no-go nguồn (~07:00–08:00): fail → chỉ demo `insufficient_data` + fail-closed workflow; **cấm** synthetic thay E2E |
| 8 | Freeze hybrid/forecast/Post-MVP; **V08** + AI log backfill và release skeleton chạy ngay |

**Bổ sung board:** Critical path Data hoàn tất tới `M02` (sau `H20`+`H08` **Done**) — Profile `M01`+`H18` **Done**; `M05a`/`H06c`/`M05b`/`H15`/`M06`/`H20`/`H08`/`M02`/`M03`/`H02`/`H04`/`H13` **Done** (decision #18). `H06b` = **Done — transition core** + deploy-blocker harden. `T02` = core/library Done; runtime FR-08 theo `H23`–`H26`. Stretch FR-12: `H21` Done → `H22`/`G06`. `V08` defer (decision #19).

**Owner ngay:** Hoàng — **`D4b`/`H11b`/`H22` Done**; `H27` deploy Vercel mở, đồng thời chờ `V07`+`A05` → `D4r`. Giang — **G05–G04 Done** (PR #23); stretch **`G06` unblocked** (sau H22). Thu Trang — T01–T03 + T02 core Done. Văn Hải — **`V07` mở** (sau D4b); `V08` defer gần CP2/D5. **Hạ Giang** — full **A05** UAT trên Live; slide skeleton. Khánh Duy — M07/M08 freeze.

## 2. Boundary bắt buộc cho ML, agent và hybrid

1. MVP ship baseline từ điểm theo học kỳ **và** điểm danh theo thời gian, kèm coverage và freshness. Không có chuỗi điểm danh đã duyệt thì nhánh attendance trả `insufficient_data`; không impute 0, không tạo tuần giả, không gọi đó là hybrid/forecast. Tín hiệu chuyên cần vẫn là phạm vi MVP (`H15` + feature), không Post-MVP.
2. Model/API giữ raw score nội bộ. Đầu ra công khai chỉ là `review_priority_band`, factors/evidence, coverage, freshness, data state, model version và calculated-at.
3. Agent chỉ giải thích output model/API đã được cấp quyền. Agent không tính/sửa score, không dự báo/khẳng định dropout cho một sinh viên, không suy luận nguyên nhân và không đổi trạng thái case.
4. Fairness chỉ có metric khi đủ audit group được phê duyệt, ground truth và mẫu số; nếu thiếu thì fail closed bằng `insufficient_data`.
5. `academic_status.is_dropout_outcome` chỉ evaluation nội bộ (M02/M03 test); **không** vào scoring features, public `ReviewCase`, hay agent context.
6. Case state machine theo [Process §4](../02-product/03-process.md): `New Signal` → `Pending Review` → `Approved for Follow-up` → `Assigned` → `Follow-up in Progress` → `Resolved`/`Monitoring` (hoặc `Dismissed` từ `Pending Review`). “Hoãn” = action giữ `Pending Review` + thời điểm xem lại; **không** phải state riêng. Thiếu `advisor_ref` → dừng handoff, đưa mapping-repair queue — không handoff chỉ vì đã approve.

## 3. Board chuẩn — task / depends / status

Mỗi task có một owner. Nếu dependency chưa Done, status ghi `BLOCKED → ID`; không tự tạo fixture, fallback hoặc contract thay thế. Chi tiết outcome, gate, DoD nằm ở mục 4–9.

**Critical path MVP (realign §1.2 — còn lại sau P0.5):**

```text
Data:     M05a ✓ → M05b ✓ → M06 ✓ → H20 ✓ → H08 ✓ → M02 ✓ ┐
Profile:  M01 ✓ → H18 ✓ ───────────────────────────────────┼→ H02 ✓ → G02 ✓ → D4b ✓
Attendance: H15 ✓ (mvp-attendance-over-time) ───────────────┘
Contract: H06a-r ✓ → H11a-r ✓ → (G05 ✓ ∥ T03 ✓)
Deploy:   (H07 ✓ ∥ D3 ✓) → D4a ✓ → D4b ✓ → V07 + A05 → D4r → V05
```

`H02`/`G05`/`G02`/`G03`/`G04`/`D4b` **Done**. `H11a-r` **Done REVALIDATE**. `M05b`/`H15` **Done** — decision #18. `M03` **Done** (fail-closed, catalog rỗng).

**Release loop bắt buộc:** `D4a` ✓ → `D4b` ✓ → `V07` **và** `A05` ghi defect → owner fix → `D4r` → mới `V05`. Không nộp CP2 trong cửa sổ 10 phút sau smoke đầu.

**Freeze tới sau submission:** `M07` → `H14` → `M08` → `H17` → `T04`. `H15` **Done** (team-provisioned allowlist).

### Hoàng

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| H01 | Backend health + DB stub | — | [x] |
| H05a | Minimum contract/state (arch, PRD/thuật ngữ, Process state/care) | — | [x] Done — arch + Process §4 + thuật ngữ MVP |
| H05b | AI-log template + release-evidence template | H05a | [x] Done — templates + pointers; không rewrite policy |
| H10 | Contract EPU/Data-ML + decision từ M04 | H05a, M04 | [x] Done — EPU + [08 Data-ML](../04-engineering/08-data-ml-scoring-fairness-contract.md) + decision #17 · mốc 02:00 đã trễ |
| H06a | Pydantic internal/public envelopes | H10 | [x] **Done** (`H06a-r`) — semantic reopen landed; 42 contract tests |
| H06b | Transition API theo Process state machine | H05a | [x] **Done — transition core** (giữ lịch sử); deploy-blocker harden landed (seed-only create, server actor, no public `advisor_ref`; 21 tests) — public shell |
| H11a | Integration contract tối thiểu cho G05/T03 | H06a | [x] **Done REVALIDATE** (`H11a-r`) — 19 integration tests; unlocks G05/T03 |
| H11b | Docs agent/FE hoàn thiện sau build | H11a, G05, T03, H26 | [x] **Done** — arch §6 + guardrails + FE integration after-build; no FE Agent UI overclaim |
| H07 | Deployment/runbook docs | H05a | [x] Done — runbook draft; finalize Live/smoke/rollback tại D4a/D4b |
| H19 | MVP persistence schema versioned + legacy mapping | H10 | [x] Done — Alembic 7 bảng `dwh` + 4 migrate tests; schema doc |
| H20 | Transactional approved-fixture import vào `dwh` | H19, M06 | [x] **Done** — `app/dwh` import_gate/importer/cli; attendance + semester paths; tests `test_h20_*` |
| H08 | `dwh` → normalized internal DTO read adapter | H20, H06a | [x] **Done** — `app/dwh/read_adapter.py` + `NormalizedStudentRecord`; unlocks M02/H03 |
| H18 | Quarantine legacy ML synthetic khỏi API/MVP path | M01 | [x] **Done** — API/MVP quarantine tests; leftover `early_warning` gỡ; mở khóa blocker H18 trên H02 |
| H14 | Decision/contract research forecast/fusion từ M07 | M07 | [ ] BLOCKED → M07 · **FREEZE** tới sau submission |
| H02 | API list/detail ReviewCase public | H06a, M02, H18 | [x] **Done** - GET /review-cases list/detail; review_projection + review_router; tests/test_h02_review_case_api.py |
| H13 | Nội dung + nộp Checkpoint 1 | H05a, H10 | [x] **Done** — form BTC nộp 18/7; draft [11-h13…](11-h13-cp1-btc-draft.md); evidence §1 |
| H03 | Care workflow API + advisor_ref gate | H05a, H06b, H08 | [x] **Done** — assign resolves via H08; client `advisor_ref` ignored; unlocks G03 |
| H04 | Threshold/config API (public semantics) | M03 | [x] **Done** - /config/thresholds(+impact) + /fairness/report; threshold_public; tests/test_h04_threshold_fairness_api.py |
| H12a | Runtime privacy/care copy (UI/agent) | H05a, H10 | [x] Done — 4 copy keys Data-ML §6; bỏ “Điểm rủi ro” trên FE |
| H12b | Post-MVP banner + asset copy | H12a | [x] Done — banner + skeleton [13-h12b-asset-copy-skeleton.md](13-h12b-asset-copy-skeleton.md) |
| H21 | Research advisor-batch mail draft tool/contract | H13 | [x] **Done** — [11-advisor…](../04-engineering/11-advisor-batch-mail-draft.md) + decision #20; Option A = core |
| H22 | API bundle draft theo `advisor_ref` (no send) | H21, H03, H02 | [x] **Done** — `GET /advisor-handoff-drafts`; mapping_repair bucket; `test_h22_*` (8); unlock G06 |
| H23 | Server-derived AgentContext + contract reconciliation | H11a, H02, M02, T02, H12a | [x] **Done** — `context_service` + `AgentCommand` + `provider_call_allowed`; `test_h23_agent_context.py` |
| H24 | `POST /review-cases/{case_id}/explanation` + runtime wiring | H23 | [x] **Done** — router/runtime DI; OpenAPI min body; mocked HTTP; demo identity ≠ production RBAC; `test_h24_agent_api.py` |
| H25 | Structured grounding + FPT/provider hardening | H24, T02 | [x] **Done** — structured plan + VI renderer + FPT transport harden; `test_h25_grounding.py` + `test_h25_fpt_transport.py` |
| H26 | Agent HTTP E2E + runtime/release evidence | H24, H25 | [x] **Done** — `test_h26_agent_e2e.py` mocked M02→HTTP; full verify 410 pass / 1 skip (live FPT SKIP); [evidence §5c](07-release-evidence.md); unlock H11b runtime side |
| H27 | Deploy frontend production lên Vercel | D3, D4b | [ ] **IN PROGRESS** — URL `https://abg-team.vercel.app`; same-origin rewrite → EC2 API; login OK; data path fix deploying; chưa thay Live URL nộp trước V07/A05 re-smoke |
| D3 | GitHub public + PII/secret scan | — | [x] Done — tree sạch; **residual history accept CP2**; trước final: clean submission repo hoặc purge có phê duyệt |
| D4a | Deploy infrastructure / Live shell (health + rollback sẵn) | H07, D3 | [x] **Done** — Live shell: API http://52.74.255.88:8000/health · FE http://52.74.255.88:3000 · EC2 i-0b0576945d080cb3f (**NOT** D4b) |
| D4b | Product smoke list→case trên Live URL | D4a, H02, G02 | [x] **Done** — 2026-07-18 ~13:05 +07: health `database:true`; `GET /review-cases` state=ok n=50; detail `rc-s-00518c9485a9` band=`can_ra_soat`; FE `/login` `/dashboard` 200; no forbidden fields; images `:d4b` + Postgres import |
| D4r | Fix từ QA → redeploy → re-smoke | D4b, V07, A05 | [ ] BLOCKED → V07, **A05** · D4b Done |
| H16 | Acceptance matrix + release evidence | A05, V07, V05 | [ ] BLOCKED → A05, V07, V05 |
| H09 | README + verify/known-limit note cuối | H02, D4r, H16 | [ ] BLOCKED → D4r, H16 · H02 Done |
| D5 | AI collaboration log từ V08 | V08 | [ ] BLOCKED → V08 · V08 **defer** gần CP2/D5 |
| H15 | Attendance source approval + amendment (**MVP**) | H10 + approval artifact | [x] **Done** — decision #18; fixture `mvp-attendance-over-time`; [12-h15…](12-h15-attendance-approval-prep.md) |
| H17 | Post-MVP hybrid public API/envelope (forecast/fusion) | H14, M08 | [ ] BLOCKED → H14, M08 · **FREEZE** |

### Khánh Duy

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| M01 | Quarantine/remove legacy ML synthetic (reopen) | — | [x] **Done** — PR #16 (`1046ffe`); guard `tests/test_m01_legacy_quarantine.py`; mở `H18` |
| M04 | Handoff kỹ thuật Data/ML cho Hoàng | — | [x] Done — [handoff](10-m04-data-ml-handoff.md); khóa bởi H10 |
| H06c | FairnessReport schema + fail-closed fixture | H10 | [x] **Done** — PR #17; fail-closed fixture |
| M05a | Build semester source gate (code/tests) | H10 | [x] **Done** — PR #17; `app/ml/source_gate` + tests |
| M05b | Approved source available (artifact duyệt) | M05a + approval | [x] **Done** — [14-m05b…](14-m05b-semester-approval.md); team approver (decision #18) |
| M06 | Fixture 4 bảng domain + manifests + quality tests | M05b | [x] **Done** — `app/ml/domain` transform + quality report; attendance manifest/DQR committed; `tests/test_m06_domain_fixture.py` (46); mở `H20` |
| M02 | Baseline semester ML | M06, H06a, H08 | [x] **Done** — `app/ml/scoring` (trend/volatility/attendance-trend + model_score/band/factors); `tests/test_m02_baseline_scoring.py` (28); mở `H02` |
| M07 | Nghiên cứu hybrid (research-only) | M02, H02, H13 | [ ] **FREEZE** tới sau submission |
| M03 | Fairness gate FPR/ΔFPR/N | M02, H06c | [x] **Done** — `app/ml/fairness/gate.py` fail-closed (catalog rỗng → `insufficient_data`); `tests/test_m03_fairness_gate.py` (15) |
| M08 | Attendance forecast + gated fusion (Post-MVP) | H15, M02, H14 | [ ] **FREEZE** tới sau submission |

### Giang

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| G01 | FE shell + list mock | — | [x] (mock tạm; G05 phải thay) |
| G05 | Thay mock bằng public DTO/fixture đã validate | H11a | [x] **Done** — types/fixtures; xóa mock-review-list; AI-log G05; PR #23 path |
| G02 | Dashboard → cohort → case dùng API | G05, H02 | [x] **Done** — `lib/api.ts` → `/review-cases`; fail-closed `upstream_unavailable`; AI-log G02 |
| G03 | Care UI review/handoff | H03, H12a | [x] **Done** — `CareActions.tsx` Process §4; AI-log G03 |
| G04 | Fairness/privacy/threshold panel | H04, H12a | [x] **Done** — login/role + Fairness/Threshold panels; AI-log G04; PR #23 |
| G06 | FE filter theo advisor + Copy/`mailto:` draft lô | H22, G05 | [ ] **TODO** — unblocked (H22+G05 Done); stretch FR-12; không block D4b |

### Thu Trang

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| T03 | Agent interface + fixture + refusal/adversarial | H11a | [x] **Done** — output contract `backend/app/agent/schemas.py` consume `AgentContextResponse` (H11a); 6 fixtures + 12 ca adversarial (phủ 7 refusal + ok/insufficient/unavailable); 26 tests xanh `backend/tests/agent/`; forbidden-field scan `assert_no_forbidden_keys`; không vỡ contract tests của H06a/H11a/H06c |
| T01 | Agent stub từ fixture, refusal tests xanh | T03, H06a | [x] **Done** — stub deterministic `backend/app/agent/stub.py` + guardrail classifier `guardrails.py` (mock model, không LLM); 12/12 ca adversarial pass + determinism + grounding-only-case-codes; 16 tests mới (`tests/agent/test_agent_stub.py`), tổng agent 42 xanh; output quét `assert_no_forbidden_keys` |
| T02 | Agent grounded explanation core/library | T01, H02, H12a | [x] **Done — core/library only**: FPT text adapter + mocked grounding tests; context service/HTTP/provider runtime và FR-08 E2E theo `H23`–`H26` |
| T04 | Agent adapter hybrid (Post-MVP) | H17 | [ ] **FREEZE** tới sau submission |

### Hạ Giang (`giang`)

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| A05 | UAT / claim-copy review → gap cho Hoàng | H02, G02, H03, G03, M03, H04, G04, H26, D4b, H12a | [ ] **TODO** — unblocked (deps Done kể cả D4b); full UAT trên Live; **bắt buộc trước D4r** |
| D1 | Asset slide + mô tả dự án nộp | V02, H12b, H16, D4r | [ ] BLOCKED → V02… · **skeleton slide/claim matrix chạy ngay** (chưa screenshot thiếu evidence) |

### Văn Hải

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| V07 | QA release + smoke độc lập (lần 1) | D3, D4b | [ ] **TODO** — unblocked (D4b Done); incognito smoke; defect → D4r |
| V05 | Nộp Checkpoint 2 | D3, D4r, V07 | [ ] BLOCKED → D3, D4r, V07 |
| V02 | Script demo 4′ + Q&A 2′, rehearsal | D4r, G02, H26, G03, G04, H12a | [ ] BLOCKED → D4r… · chỉ claim Agent runtime sau H26; UI Agent cần consumer FE riêng |
| D2 | Video ≤5 phút đúng Live URL | D1, D4r | [ ] BLOCKED → D1, D4r |
| V08 | Rà AI log → gap cho Hoàng | H05b | [ ] **DEFER** gần CP2 / trước D5 — log một thể (decision #19); không làm ngay |
| V06 | Nộp cuối + lưu xác nhận BTC | D1, D2, D3, D4r, D5, H09, H16 | [ ] BLOCKED → D1…H16 |

---

## 4. Hoàng — chi tiết task

**Lane:** docs/contract nguồn chuẩn, backend/API, deploy, release evidence.
**Read first:** PRD §§4–8, Ethics, Process §4, decisions, [EPU contract](../04-engineering/04-epu-data-integration-contract.md), [Data-ML](../04-engineering/08-data-ml-scoring-fairness-contract.md).
**Không làm:** tự viết model/fusion của Duy.

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| H01 | P0 | Backend health + DB stub | `backend/tests/test_health.py` — **Done** |
| H05a | Recovery · ASAP 03:30 | Minimum contract/state: architecture, PRD/thuật ngữ, Process state/care boundary | Docs không mâu thuẫn PRD/Ethics/Process; đủ để mở `H06b`/`H10`/`H07` — **Done:** [arch](../04-engineering/05-system-architecture.md), Process §4, banner BRD/scope, decision #15 |
| H05b | P1 · sau H05a | AI-log template + release-evidence template | Template sẵn; không chặn API/schema — **Done:** `.ai-log/templates/*`, [release-evidence template](templates/release-evidence-item.template.md); pointer [AI-log README](../../.ai-log/README.md) + [07-release-evidence](07-release-evidence.md) |
| H10 | Recovery · ~04:00 (mốc 02:00 đã trễ) | Hoàn thiện contract EPU/Data-ML và decision từ M04 | **Done:** [EPU](../04-engineering/04-epu-data-integration-contract.md), [Data-ML](../04-engineering/08-data-ml-scoring-fairness-contract.md), decision #17; source gate ≠ approved; MVP điểm + điểm danh; `insufficient_data`; cấm synthetic; outcome nội bộ only |
| H06a | P1 · **Done** (`H06a-r`) | Pydantic internal/public envelopes — semantic Data-ML §3 | **Done:** semantic reopen landed; coverage/band/factors/`dataset_version`; 42 contract tests |
| H06b | P1 · sau H05a | Transition API đúng Process | **Done — transition core** (giữ lịch sử): `backend/app/cases/*`. **Deploy-blocker harden landed:** seed-only create, server actor, no public `advisor_ref` (21 tests) — public shell |
| H11a | P1 · **Done REVALIDATE** | Integration contract tối thiểu | **Done (`H11a-r`):** 19 integration tests; unlocks G05/T03 |
| H11b | P2 · sau G05 · T03+H26 Done | Docs agent/FE hoàn thiện | **Done** — arch §6 + [guardrails](../04-engineering/08-agent-grounding-guardrails.md) + [doc 10](../04-engineering/10-fe-agent-integration-contract.md); FR-08 = backend HTTP only |
| H07 | P1 · sau H05a | Deployment/runbook: env, CORS, seed, health, smoke, rollback | Runbook không secret — **Done:** [06-deploy-runbook](../04-engineering/06-deploy-runbook.md) draft từ arch; linked docs index + arch; Live URL/smoke/rollback finalize tại `D4a`/`D4b` |
| H19 | P1 · sau H10 | Thiết kế persistence MVP versioned: mapping metadata legacy DWH → schema `dwh` mới và migration DB rỗng | **Done:** [Schema persistence](../04-engineering/07-mvp-persistence-schema.md); Alembic 7 bảng `dwh` + `tests/test_dwh_migrate.py` (4); không copy schema/row legacy/PII; attendance table rỗng tới `H15` |
| H20 | P1 · sau H19+M06 | Nạp transactional fixture M06 đã được duyệt vào `dwh` | **Done:** CLI `python -m app.dwh.cli`; gate fail → zero write; default `data/approved/` (attendance + semester domain package); optional raw via `SILENT_SHIELD_SEMESTER_SOURCE_PATH`; readiness không PII; `tests/test_h20_import_gates.py` + `tests/test_h20_import.py` |
| H08 | P1 · sau H20+H06a | `dwh` → `NormalizedStudentRecord`/`ScoringFeatures` read adapter | **Done:** `app/dwh/read_adapter.py` + `app/contracts/normalized.py`; provenance fail-closed; không chiếu outcome; `mapping_repair` khi thiếu `advisor_ref`; không cross-join nguồn; `tests/test_h08_read_adapter.py` — mở M02/H03 |
| H18 | P1 · sau M01 | Quarantine legacy `EarlyWarning*` / synthetic attendance-week / synth group khỏi API/MVP path | **Done:** `tests/test_h18_api_mvp_quarantine.py` (6) + leftover `early_warning` gỡ; OpenAPI/ReviewCase không raw risk; **không** cấm chuỗi điểm danh đã duyệt qua `H15` |
| H14 | Post-CP2 | Decision/contract research forecasting/fusion từ M07 | Tách `TermEvidence`/`AttendanceForecastEvidence`; ready/`insufficient_data` |
| H02 | P1 · sau M02+H18 | API list/detail chỉ `ReviewCase` public | **Done:** app/cases/review_projection.py + review_router.py; GET /review-cases H11a envelopes; no model_score/PII; tests/test_h02_review_case_api.py |
| H13 | P1 · 11:00 | Nộp Checkpoint 1 | **Done** — form BTC nộp 18/7; [draft](11-h13-cp1-btc-draft.md) + evidence §1; không claim forecast/hybrid |
| H21 | P2 · sau H13 | Research tool/contract soạn mail theo GV | **Done:** [11-advisor-batch-mail-draft](../04-engineering/11-advisor-batch-mail-draft.md) + decision #20; Option A = core; không SMTP |
| H22 | P2 stretch · sau H21 | API `AdvisorHandoffDraftBundle` theo `advisor_ref` | **Done:** `GET /advisor-handoff-drafts`; draft-only; mapping_repair; forbidden-field tests; unlock G06 |
| H23 | P2 · **Done** | Server-derived AgentContext + contract reconciliation | **Done:** `build_agent_context` / `AgentCommand` / state-intent matrix; M02 codes+version; fail-closed for H24 zero-call rule; `test_h23_agent_context.py` |
| H24 | P2 · **Done** | Agent command API + production wiring | **Done:** `POST /review-cases/{case_id}/explanation`; server context; OpenAPI min fields; mocked HTTP; demo identity only — not production RBAC; `test_h24_agent_api.py` |
| H25 | P2 · **Done** | Context-bound output + provider hardening | **Done:** no raw question to FPT; structured plan + backend VI render; transport/host/size/secret guards; `test_h25_*` |
| H26 | P2 · **Done** | Agent runtime E2E + release evidence | **Done:** mocked HTTP E2E `test_h26_agent_e2e.py`; `verify.ps1` 410 passed / 1 skipped; live FPT SKIP; FR-08 claimable at **backend HTTP** level; FE UI still separate; `H11b` **Done** |
| H27 | P2 · 2–4h · sau D3+D4b | Deploy frontend production lên Vercel | **IN PROGRESS:** `https://abg-team.vercel.app`; same-origin rewrite in `frontend/next.config.js` → Live API; login OK; data path fix; chưa flip submission URL trước V07+A05 |
| H03 | P2 · sau H08 | Care workflow API | **Done:** approve/dismiss/defer + assign-handoff; H08 `advisor_ref`/`mapping_repair` gate; client ref ignored; `tests/test_h03_care_workflow.py` — mở G03 |
| H04 | P2 · sau M03 | Threshold/config API public semantics | **Done:** app/contracts/threshold_public.py + app/config_api/router.py; impact aggregates only; fairness MVP insufficient_data; tests/test_h04_threshold_fairness_api.py |
| H12a | P2 · ~15:00 (trước T02/G03/G04) | Runtime privacy/care copy cho UI/agent | **Done:** `frontend/src/lib/copy.ts` 4 keys Data-ML §6; mock list không “Điểm rủi ro”; mở `H12b` / giảm blocker `G03`/`G04`/`T02` |
| H12b | P2 · sau H12a · ~19:00 | Banner + asset copy | **Done:** banner + skeleton [13-h12b-asset-copy-skeleton.md](13-h12b-asset-copy-skeleton.md); forecast/fusion = research/blocked; điểm danh theo thời gian = MVP |
| D3 | P2 · ~20:30 | GitHub public, PII/secret scan | **Done** tree + [scan notes](10-d3-github-pii-secret-scan.md); residual history **accept CP2**; trước final: clean submission repo hoặc purge có phê duyệt |
| D4a | P2 · sớm sau H07+D3 | Live shell: deploy infra, health, rollback sẵn | **Done** — Live shell: API http://52.74.255.88:8000/health · FE http://52.74.255.88:3000 · EC2 i-0b0576945d080cb3f (**NOT** D4b) |
| D4b | P2 · sau H02+G02 | Product smoke list→case ẩn danh trên Live | **Done** 2026-07-18 ~13:05 +07: health `database:true`; list state=ok n=50; detail `rc-s-00518c9485a9` / `can_ra_soat`; FE login+dashboard 200; CORS OK; no PII/score leak; [evidence](07-release-evidence.md) §2 |
| D4r | P2 · sau V07+A05 | Owner fix → redeploy → re-smoke | **A05 bắt buộc** cùng V07 trước D4r; cửa sổ fix ≥45–60 phút trước V05; D4b Done |
| H16 | P3 · sau V05 | Acceptance matrix + release evidence | Phụ thuộc **A05 + V07 + V05**; mỗi FR/CP2 item có evidence hoặc limitation |
| H09 | P3 · 09:00 | README + verify/known-limit | Khớp deploy và scope thật |
| D5 | P3 · 10:00 | AI collaboration log từ V08 | Gap có owner; sạch PII/secret |
| H15 | P1 · MVP | Attendance source approval + amendment contract | **Done** decision #18: [12-h15…](12-h15-attendance-approval-prep.md) + fixture `mvp-attendance-over-time`; team approver |
| H17 | Post-MVP · **FREEZE** | Hybrid forecast/fusion public API theo H14 | Không làm tới sau submission |

**Verify:** link/traceability, contract test, docs khớp code/public DTO.

---

## 5. Khánh Duy — chi tiết task

**Lane:** Data/ML, source validation, baseline semester.
**Read first:** PRD §§4,7–8; signal catalog; Ethics §§5–6; [EPU contract](../04-engineering/04-epu-data-integration-contract.md); [Data-ML](../04-engineering/08-data-ml-scoring-fairness-contract.md); ML tests gần nhất.
**Không làm:** hoàn thiện Markdown contract/PRD; dùng legacy synthetic đã liệt kê; hybrid/`M07`/`M08` tới sau submission; đưa `is_dropout_outcome`/group attr vào scoring.

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| M01 | P0→P1 | Quarantine/remove legacy ML synthetic: attendance tuần, synth socioeconomic/ethnicity, raw risk path trong `early_warning` | **Done** PR #16: module/CSV/generator gỡ; `tests/test_m01_legacy_quarantine.py`; mở `H18` |
| M04 | Recovery · ASAP 03:30 | Handoff Data/ML: semester + attendance-over-time baseline, source/quality gate, threshold/FPR, giới hạn forecast/fusion | **Done:** [10-m04…](10-m04-data-ml-handoff.md); **không** đồng nghĩa dữ liệu đã được duyệt |
| H06c | P1 · sau H10 | `FairnessReport` schema + fail-closed fixture | **Done** PR #17 |
| M05a | P1 · sau H10 | **Build** source gate: register, hash/count, PII exclusion, fail-closed khi thiếu approval | **Done** PR #17 |
| M05b | P1 · sau M05a | **Approved source available** | **Done** [14-m05b…](14-m05b-semester-approval.md); team approver (decision #18) |
| M06 | P1 · sau M05b | Fixture: bảng domain điểm + ttendance_event (H15) + source_manifest + data_quality_report | **Done:** pp/ml/domain (models/transform/attendance) — deterministic, pseudonymous, fail-closed PII/token, không cross-join, is_dropout_outcome chỉ evaluation; field khớp cột dwh (H20/H08); attendance source_manifest/data_quality_report + semester domain under data/approved/ (WIP path; raw V59 ngoài git); 	ests/test_m06_domain_fixture.py (46). Không commit raw/PII |
| M02 | P1 · baseline | Baseline ML: trend/volatility điểm + chuyên cần theo thời gian (khi có) + factors + coverage | **Done:** ackend/app/ml/scoring/{models,estimator}.py — OLS grade_trend_slope/grade_volatility/ttendance_trend_slope (pure, no DB), compute_model_score/and_for_score (uncalibrated 	hr-epu-0.1-uncalibrated wiring threshold), contributing_factors (machine codes only); không dùng is_dropout_outcome; không cross-join nhánh; ackend/tests/test_m02_baseline_scoring.py (28 tests: determinism, boundary field-forbid, monotonic sweep, band mapping, factor-materiality property) |
| M07 | **FREEZE** | Nghiên cứu forecast/fusion | Không tranh slot MVP; chỉ sau submission |
| M03 | P2 | Fairness gate FPR/ΔFPR/N hoặc `insufficient_data` | **Done:** `backend/app/ml/fairness/gate.py` — `APPROVED_AUDIT_ATTRIBUTES` catalog rỗng ⇒ `build_fairness_report` luôn `insufficient_data(no_approved_audit_attribute)` trên MVP path; formula FPR/TPR/selection_rate + small-N (`n_label_neg<10`) + ΔFPR + flag đã build/test cho nhánh `ok` tương lai (audit attribute monkeypatch trong test — không phải dữ liệu MVP); `backend/tests/test_m03_fairness_gate.py` (15 tests) |
| M08 | **FREEZE** | Attendance forecasting + gated fusion | Post-MVP; không làm tới sau submission |

### M07 — yêu cầu handoff hybrid (sau submission)

Chỉ chạy sau submission / khi unfreeze. So sánh semester feature vs forecast attendance: data readiness, window, timestamp order, horizon, label cutoff/no leakage, missingness, nghỉ có phép, gated/late fusion. Chỉ đề xuất:

- `TermEvidence` và `AttendanceForecastEvidence` tách riêng; coverage, freshness, provenance, `model_version`, `calculated_at`, ready/`insufficient_data`.
- Fusion chỉ khi cả hai branch qua gate; absence không zero-impute, không đổi priority.
- Public/agent chỉ `review_priority_band`, factors/evidence, limitations.

**Verify:** determinism, missing/stale, formula/denominator, PII/source gate.

---

## 6. Giang — chi tiết task

**Lane:** Frontend integration và UI (**Giang** = Nguyễn Trường Giang — không nhầm Hạ Giang).
**Read first:** PRD §5; Ethics; H11a-r (không bắt đầu trên H11a cũ).
**Không làm:** tự chốt copy/contract; raw score; “Điểm rủi ro”; synthetic/legacy attendance mock sau G05.

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| G01 | P0 | FE shell + list mock tạm | Smoke — **Done** (mock phải bị G05 thay) |
| G05 | P1 · sau H11a-r | Thay hẳn mock synthetic/K-12 bằng public DTO + fixture đã validate | **Done** — types/fixtures/limitations; xóa mock-review-list; AI-log G05 |
| G02 | P1 · sau H02 | Dashboard → cohort → case dùng API | **Done** — `lib/api.ts` live `/review-cases`; fail-closed; AI-log G02 |
| G03 | P2 · sau H12a | Care UI theo Process states + defer = giữ Pending | **Done** — `CareActions.tsx`; AI-log G03 |
| G04 | P2 · sau H12a | Fairness/privacy/threshold panel | **Done** — login/role + Fairness/Threshold; AI-log G04; PR #23 |
| G06 | P2 stretch · sau H22 | Filter theo advisor + Copy/`mailto:` bản nháp lô | FR-12; draft-only; **TODO** unblocked (H22 Done); không block D4b (D4b Done) |

**Verify:** lint, production build, behavior smoke. Chỉ public DTO.

---

## 7. Thu Trang — chi tiết task

**Lane:** Agent adapter, grounding/refusal tests.
**Read first:** PRD §5.4/FR-08; Ethics §8; H11a-r / H12a.
**Không làm:** tự tính/sửa mức ưu tiên; score/dropout conclusion; hybrid T04 tới sau submission.

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| T03 | P1 · **Done** | Agent interface, fixture, refusal/adversarial | **Done:** `AgentExplanation` contract consume H11a envelope; 12 ca adversarial (7 refusal + ok/insufficient/unavailable, chống over-refusal); evidence `backend/tests/agent/` (26 tests) + `backend/tests/fixtures/agent/` + [doc 08](../04-engineering/08-agent-grounding-guardrails.md); mocked-only, không live call |
| T01 | P1 · **Done** | Agent stub từ fixture | **Done:** stub deterministic (guardrails-first → context-status fail-closed → grounded assembly); 12/12 adversarial + determinism + grounding tests xanh; evidence `backend/app/agent/stub.py`, `guardrails.py`, `backend/tests/agent/test_agent_stub.py` |
| T02 | P2 · **Done core/library** | Grounded explanation adapter từ safe context | **Done:** FPT text adapter + mocked grounding; chỉ band/factors/coverage/limits. **Không** claim server context/HTTP/runtime E2E — theo `H23`–`H26` |
| T04 | **FREEZE** | Agent adapter hybrid | Chỉ sau submission + H17 |

**Verify:** grounding/refusal/adversarial mocked tests.

---

## 8. Hạ Giang (`giang`) — chi tiết task

**Owner:** Trần Hạ Giang — UAT / claim-copy / slide skeleton. **Không** nhầm với Giang (FE).
**Bắt đầu skeleton ngay; full UAT từ P2/Live.** Story: [08-stories-giang.md](08-stories-giang.md).

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| A05 | P2 · song song V07; **bắt buộc trước D4r** | UAT/claim-copy review | **Unblocked** sau D4b; full UAT trên Live; gap → Hoàng/`D4r`; không sửa docs/code |
| D1 | P3 · 09:00 | Asset slide + mô tả | Skeleton/claim matrix **ngay**; finalize URL/screenshot sau D4r + H12b/H16 |

**A05:** list→case→review/handoff trên Live URL; rà care/privacy/fairness/claim; gửi Hoàng + **bắt buộc feed `D4r`**.

**D1:** chỉ copy/screenshot từ `H12b`/`H16` và Live URL đã `D4r`; điểm danh theo thời gian = MVP; forecast/fusion chỉ Post-MVP/research nếu chưa Done.

---

## 9. Văn Hải — chi tiết task

**Bắt đầu từ P2; V08 defer gần CP2/D5 (decision #19).** Story: [09-stories-van-hai.md](09-stories-van-hai.md). Evidence: [07-release-evidence.md](07-release-evidence.md).

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| V07 | P2 · sau D4b | QA release + smoke độc lập lần 1 | **Unblocked**; incognito; ghi defect cho owner/`D4r`; không tự sửa |
| V05 | P2 · sau D4r | Nộp Checkpoint 2 | **Chỉ sau `D4r` xanh**; BTC nhận 2 URL + xác nhận |
| V02 | P3 · 08:00 | Script 4′ + Q&A 2′, rehearsal | Script skeleton sớm; Live sau `D4r` |
| D2 | P3 · 09:30 | Video ≤5 phút | Đúng Live URL sau `D4r` |
| V08 | **DEFER** · gần CP2 / trước D5 | Rà AI log một thể | Depends `H05b`; thu thập manifest + link **một lần**; gap → Hoàng/`D5`; CP2 không phụ thuộc V08 |
| V06 | P3 · 10:30 | Nộp cuối | Sau evidence `H16` đã khóa CP2+final |

---

## 10. Quy ước, rủi ro và việc làm ngay

| Quy ước / risk | Cách xử lý |
|:--|:--|
| Realign §1.2 | Board này là SoT execution; không giữ snapshot “H11a mở G05/T03” cũ |
| H06a/H11a semantic | `H06a-r` + `H11a-r` **Done**; `G05`/`T03` **Done** |
| H06b ≠ deploy-ready (lịch sử) | Transition-core Done; deploy-blocker harden landed (seed-only create / server actor / no public `advisor_ref`) |
| Critical path song song | Data/API/FE critical path tới **D4b Done**; còn `V07`+`A05`→`D4r`→`V05` |
| Source gate ≠ approved data | `M05b`/`H15` Done (decision #18); Live import LF hashes `73274079…` / `78d7153f…` |
| D3 residual history | Accept CP2; quyết định clean submission trước final |
| Release dồn muộn | Slide/script skeleton **ngay**; `V08` AI log **một thể** gần CP2/D5 (decision #19) |
| Advisor mail draft | Stretch `H21`→`H22`✓→`G06` (FR-12); **không** block G02/D4b; draft-only |
| Agent runtime overclaim | `H23`–`H26` Done = FR-08 **backend HTTP** E2E (mocked FPT); **không** claim FE Agent UI / production RBAC / live FPT; `H11b` **Done** |
| Hybrid | FREEZE `M07`/`H14`/`M08`/`H17`/`T04` tới sau submission |
| FE scoping gap (G02) | `ReviewCase` public thiếu `cohort`/`department`/`class_code` — FE chưa scoping khoa/lớp; **decision cần Hoàng chốt** (mở rộng allowlist H11a hoặc chấp nhận giới hạn MVP); không tự thêm field |
| Giang vs Hạ Giang | Giang = FE; Hạ Giang = UAT/slide/claim |
| QA defects | V07 **và** A05 → owner fix → `D4r` → mới V05 |
| Vercel candidate (`H27`) | Hoàng deploy frontend; chỉ thay Live URL nộp sau HTTPS-safe API smoke và V07+A05 re-smoke trên đúng URL |

1. **Ngay:** Văn Hải — **V07** smoke độc lập. **Hạ Giang** — **A05** UAT trên Live. Giang — stretch `G06` nếu còn slot. Hoàng — chạy `H27` và chờ V07+A05 → `D4r`.
2. Critical path CP2: `D4b` ✓ → `V07`+`A05`→`D4r`→`V05`. Stretch mail: `H22`✓ → `G06` (FR-12).
3. Semester + attendance đã duyệt + **Live DB import**; `H20`/`H08`/`H02`/`H04`/`H13`/`G05`–`G04` Done. Legacy synthetic cấm vẫn fail-closed.
4. `D4a`/`D4b` **Done**; `D4r` chỉ sau V07 **và** A05.
5. Trước handoff: verify phù hợp; trước final: `scripts/verify.ps1`, `git diff --check`, `git status --short`.
