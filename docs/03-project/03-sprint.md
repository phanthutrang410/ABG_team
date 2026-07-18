# Sprint — Silent Shield (17–19/7/2026)

> Nguồn chuẩn: [Quy chế VAIC](../01-requirements/01-vaic-rules.md) · [PRD MVP](../02-product/04-prd.md) · [Process](../02-product/03-process.md) · [RULES.md](../../RULES.md).
>
> **Điều chỉnh phân công 18/7:** Hoàng là owner duy nhất hoàn thiện tài liệu/contract nguồn chuẩn. Build tập trung vào Hoàng, Khánh Duy, Giang và Thu Trang. **Hạ Giang** (board ID `giang`) và Văn Hải nhận task từ P2: QA/UAT/claim/slide skeleton và release smoke — không sửa canonical docs/code. **18/7 chiều:** `V05` nộp CP2 chuyển **Thu Trang**; Hải giữ `V07` (checklist chi tiết).
>
> **Đảo lane 18/7 tối (decision #24):** **Khánh Duy** = Frontend; **Giang** (Nguyễn Trường Giang) = Data/ML / model / predict. Task ID không đổi; Owner task mở theo lane mới. **Hạ Giang** không đổi.
>
> **Chặn phạm vi hybrid (forecasting):** Freeze hoàn toàn `M07`/`H14`/`M08`/`H17`/`T04` tới sau submission. Điểm danh theo thời gian **thuộc MVP** (sau `H15`); thiếu nguồn → `insufficient_data`; **không** thay bằng synthetic để claim E2E.
>
> **Realign chốt ~05:45 18/7:** Direction giữ nguyên (prototype care/review, không claim dự báo dropout đã chứng minh). Wave update: `H06a-r`/`H11a-r` Done; `H06b` harden landed; `D4a` Live shell Done; `G05`/`T03` unblocked. Chi tiết §1.2 + board §3.

**Quy ước tên:** **Giang** = Nguyễn Trường Giang (**ML / model / predict**). **Khánh Duy** = **Frontend**. **Hạ Giang** = Trần Hạ Giang (UAT / claim-copy / slide skeleton; board ID `giang`). Không viết tắt “giang” khi phân công miệng — luôn dùng **Hạ Giang** vs **Giang**. ID task ổn định; cột Owner là nguồn phân công.

| Thành viên | Lane đang chịu trách nhiệm | Không chịu trách nhiệm |
|:--|:--|:--|
| Hoàng | Tất cả tài liệu/contract nguồn chuẩn; backend/API; deploy; tài liệu release | Không tự viết model/fusion của Giang |
| Khánh Duy | Frontend integration và UI (`G06` Notify, attendance UI, `G07`–`G09`) | Không hoàn thiện Markdown contract/PRD; không tự chốt copy/contract |
| Giang | Data/ML, source validation, baseline/model/predict (open `M07`/`M08` khi unfreeze) | Không tự chốt copy/contract; không làm hybrid tới sau submission |
| Thu Trang | Agent adapter, grounding/refusal tests; **nộp Checkpoint 2 (`V05`)** | Không tự tính/sửa mức ưu tiên; không nộp CP2 trước `D4r` |
| Hạ Giang (`giang`) | UAT, claim-copy review, slide + asset skeleton/mô tả | Không sửa canonical docs hoặc code; không nhầm với Giang (ML) |
| Văn Hải | QA release (`V07`), script/video, nộp cổng cuối (`V06`), AI-log rà | Không sửa canonical docs, deploy hoặc code; **không** nộp CP2 (`V05` → Thu Trang) |

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
| P2 | 18/7 11:00–23:00 | Rubric + live | UI/API/test + QA→fix→re-smoke + CP2 | **V05 Done** — còn H16/H09/P3 |
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

**Owner ngay:** Hoàng — **`H16` mở** (sau V05 Done). **Thu Trang** — `V05` **Done** (CP2 đã nộp). **Khánh Duy** (FE) — `G06`/attendance UI. **Giang** (ML) — freeze. Văn Hải — V02/D2/V08. **Hạ Giang** — D1 slide theo Live URL đã nộp.

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

**Wave sau release — weekly snapshot + Global Agent:** `H28` **Done ở mức kiến trúc/decision only**; build chưa ship. Hoàng sở hữu backend/docs/security/deploy `H28a`, `H29–H38`, `D6`; full brief tại [Stories — Hoàng](17-stories-hoang-weekly-agent.md). Wave này **không block** critical path hiện tại `V07+A05→D4r→V05→H16/H09` và không được dùng để overclaim feature đã có.

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
| H11b | Docs agent/FE hoàn thiện sau build | H11a, G05, T03, H26 | [x] **Done — historical gate**; repo sau đó có case-local `AgentPanel`; Global Agent/weekly briefing vẫn chưa ship |
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
| H27 | Deploy frontend production lên Vercel | D3, D4b | [x] **Done** — `https://abg-team.vercel.app` · rewrite → EC2 API · smoke health+`/review-cases` state=ok n=50 · dpl `2JkMB2Lz…` · PR #26 · **chưa** flip Live URL nộp trước V07/A05 |
| H28 | Target architecture: weekly snapshot + OpenAI + Global Agent | H27 | [x] **Done — docs/decision only** · feature chưa ship · [doc 13](../04-engineering/13-weekly-snapshot-global-agent-architecture.md) |
| H28a | Readiness/decision lock cho delta, linked namespace, identity, retention, scheduler | H28 | [x] **Done** — Decision #23; Mode B namespace; EventBridge→worker; [brief](17-stories-hoang-weekly-agent.md#h28a) |
| H29 | Provider-neutral runtime + OpenAI Responses adapter | H28 | [x] **Done** — `OpenAIResponsesClient` + `store=false`; no FPT in `get_text_model`; `test_h29_openai_transport.py` · [brief](17-stories-hoang-weekly-agent.md#h29) |
| H30 | Snapshot v2 registry + workflow run/step ledger + active pointer | H28a, H19 | [x] **Done** — Alembic `20260718_h30_snapshot`; backfill from source_manifest · [brief](17-stories-hoang-weekly-agent.md#h30) |
| H31 | Stage/promote workflow service + CLI approved replay | H30, H20 | [x] **Done** — `WeeklyWorkflowService` + `cli weekly run`; idempotent replay · [brief](17-stories-hoang-weekly-agent.md#h31) |
| H32 | Canonical linked bundle + immutable signal observations | H31, H28a | [x] **Done — Mode B** — `weekly/observations.py`; combined → `linked_namespace_pending`; [brief](17-stories-hoang-weekly-agent.md#h32) |
| H33a | Durable case/event persistence; GET read-only | H32, H06b | [x] **Done — in-memory MVP** — `CaseRepository` one-active-episode; GET no write · [brief](17-stories-hoang-weekly-agent.md#h33a) |
| H33b | Deterministic delta + case reconcile | H33a, H28a | [x] **Done** — full delta matrix + reconcile no auto-close · [brief](17-stories-hoang-weekly-agent.md#h33b) |
| H36 | Production identity/RBAC/scope + access-audit foundation | H28a, H06b | [x] **Done** — `app/auth` principal/scope + access audit; unlocks G07 · [brief](17-stories-hoang-weekly-agent.md#h36) |
| H34a | Weekly report materializer + scoped APIs | H33b, H36 | [x] **Done** — materializer + `GET /weekly-reports/latest` · [brief](17-stories-hoang-weekly-agent.md#h34a) |
| H34b | Deterministic briefing + one-time receipt APIs | H34a, H36 | [x] **Done** — briefing + shown/ack; unlocks G08 · [brief](17-stories-hoang-weekly-agent.md#h34b) |
| H35 | Advisor draft v2 trên durable approved cases/report | H34a, H36, H22 | [x] **Done** — draft-only v2; unlocks G09 · [brief](17-stories-hoang-weekly-agent.md#h35) |
| H37 | Global Agent backend turn + strict capability registry | H29, H34b, H35, H36 | [x] **Done** — `POST /agent/turns`; unlocks T05 · [brief](17-stories-hoang-weekly-agent.md#h37) |
| H38 | Export report an toàn + watermark/access audit | H34a, H36 | [x] **Done** — aggregate/case export; no bulk ID · [brief](17-stories-hoang-weekly-agent.md#h38) |
| D6 | Scheduler/worker deploy + observability/retention/rollback | H31, H34b, H35, H37, H38 | [x] **Done — ops foundation** — kill switches + `scheduler_tick` + rollback stub; EventBridge deploy still manual · [brief](17-stories-hoang-weekly-agent.md#d6) |
| D3 | GitHub public + PII/secret scan | — | [x] Done — tree sạch; **residual history accept CP2**; trước final: clean submission repo hoặc purge có phê duyệt |
| D4a | Deploy infrastructure / Live shell (health + rollback sẵn) | H07, D3 | [x] **Done** — Live shell: API http://52.74.255.88:8000/health · FE http://52.74.255.88:3000 · EC2 i-0b0576945d080cb3f (**NOT** D4b) |
| D4b | Product smoke list→case trên Live URL | D4a, H02, G02 | [x] **Done** — 2026-07-18 ~13:05 +07: health `database:true`; `GET /review-cases` state=ok n=50; detail `rc-s-00518c9485a9` band=`can_ra_soat`; FE `/login` `/dashboard` 200; no forbidden fields; images `:d4b` + Postgres import |
| D4r | Fix từ QA → redeploy → re-smoke | D4b, V07, A05 | [x] **Done** — Vercel Live URL; API `:d4r`; advisor+explanation envelopes; evidence [07](07-release-evidence.md) |
| H16 | Acceptance matrix + release evidence | A05, V07, V05 | [ ] **TODO — unblocked** · V05 Done · A05+V07 Done ([18](18-v07-a05-smoke-uat-2026-07-18.md)) |
| H09 | README + verify/known-limit note cuối | H02, D4r, H16 | [ ] BLOCKED → H16 · D4r Done · H02 Done |
| D5 | AI collaboration log từ V08 | V08 | [ ] BLOCKED → V08 · V08 **defer** gần CP2/D5 |
| H15 | Attendance source approval + amendment (**MVP**) | H10 + approval artifact | [x] **Done** — decision #18; fixture `mvp-attendance-over-time`; [12-h15…](12-h15-attendance-approval-prep.md) |
| H17 | Post-MVP hybrid public API/envelope (forecast/fusion) | H14, M08 | [ ] BLOCKED → H14, M08 · **FREEZE** |

### Khánh Duy (FE — decision #24)

> Lane hiện tại: **Frontend**. Task `M*` Done bên dưới là lịch sử (làm khi còn lane ML); open ML → **Giang**.

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| G01 | FE shell + list mock | — | [x] (mock tạm; G05 phải thay) · historical FE trước #24 |
| G05 | Thay mock bằng public DTO/fixture đã validate | H11a | [x] **Done** — types/fixtures; xóa mock-review-list; AI-log G05; PR #23 path · historical |
| G02 | Dashboard → cohort → case dùng API | G05, H02 | [x] **Done** — `lib/api.ts` → `/review-cases`; fail-closed; AI-log G02 · historical |
| G03 | Care UI review/handoff | H03, H12a | [x] **Done** — `CareActions.tsx` Process §4; AI-log G03 · historical |
| G04 | Fairness/privacy/threshold panel | H04, H12a | [x] **Done** — login/role + Fairness/Threshold; AI-log G04; PR #23 · historical |
| G06 | FE filter theo advisor + Copy/`mailto:` draft lô | H22, G05 | [ ] **TODO — owner Duy** · unblocked (H22+G05 Done); stretch FR-12 |
| G07 | Authenticated layout + global Agent shell | H36 | [ ] **TODO — owner Duy** · unblocked (H36 Done) |
| G08 | Weekly briefing/report UI | H34b, G07 | [ ] BLOCKED → G07 · **owner Duy** |
| G09 | `/notify` advisor draft FE | H35, G07 | [ ] BLOCKED → G07 · **owner Duy** |

### Giang (ML — decision #24)

> Lane hiện tại: **Data/ML / model / predict**. Task `G*` Done là lịch sử FE trước #24; open FE → **Khánh Duy**.

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| M01 | Quarantine/remove legacy ML synthetic (reopen) | — | [x] **Done** — PR #16 · historical (Duy khi còn ML) |
| M04 | Handoff kỹ thuật Data/ML cho Hoàng | — | [x] Done — [handoff](10-m04-data-ml-handoff.md) · historical |
| H06c | FairnessReport schema + fail-closed fixture | H10 | [x] **Done** — PR #17 · historical |
| M05a | Build semester source gate (code/tests) | H10 | [x] **Done** — PR #17 · historical |
| M05b | Approved source available (artifact duyệt) | M05a + approval | [x] **Done** — [14-m05b…](14-m05b-semester-approval.md) · historical |
| M06 | Fixture 4 bảng domain + manifests + quality tests | M05b | [x] **Done** — `app/ml/domain` · historical |
| M02 | Baseline semester ML | M06, H06a, H08 | [x] **Done** — `app/ml/scoring` · historical |
| M07 | Nghiên cứu hybrid (research-only) | M02, H02, H13 | [ ] **FREEZE** · **owner Giang** tới sau submission |
| M03 | Fairness gate FPR/ΔFPR/N | M02, H06c | [x] **Done** — fairness gate · historical |
| M08 | Attendance forecast + gated fusion (Post-MVP) | H15, M02, H14 | [ ] **FREEZE** · **owner Giang** tới sau submission |

### Thu Trang

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| T03 | Agent interface + fixture + refusal/adversarial | H11a | [x] **Done** — output contract `backend/app/agent/schemas.py` consume `AgentContextResponse` (H11a); 6 fixtures + 12 ca adversarial (phủ 7 refusal + ok/insufficient/unavailable); 26 tests xanh `backend/tests/agent/`; forbidden-field scan `assert_no_forbidden_keys`; không vỡ contract tests của H06a/H11a/H06c |
| T01 | Agent stub từ fixture, refusal tests xanh | T03, H06a | [x] **Done** — stub deterministic `backend/app/agent/stub.py` + guardrail classifier `guardrails.py` (mock model, không LLM); 12/12 ca adversarial pass + determinism + grounding-only-case-codes; 16 tests mới (`tests/agent/test_agent_stub.py`), tổng agent 42 xanh; output quét `assert_no_forbidden_keys` |
| T02 | Agent grounded explanation core/library | T01, H02, H12a | [x] **Done — core/library only**: FPT text adapter + mocked grounding tests; context service/HTTP/provider runtime và FR-08 E2E theo `H23`–`H26` |
| T04 | Agent adapter hybrid (Post-MVP) | H17 | [ ] **FREEZE** tới sau submission |
| T05 | Agent tool/RBAC/adversarial e2e matrix | H29, H34b, H37, G07 | [ ] BLOCKED → G07 · (H29/H34b/H37 Done) |
| V05 | Nộp Checkpoint 2 (Live URL + GitHub → BTC) | D3, D4r, V07 | [x] **Done** — Thu Trang nộp CP2 18/7 tối · Live=`https://abg-team.vercel.app` · GitHub `phanthutrang410/ABG_team` · receipt ngoài repo |

### Hạ Giang (`giang`)

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| A05 | UAT / claim-copy review → gap cho Hoàng | H02, G02, H03, G03, M03, H04, G04, H26, D4b, H12a | [x] **Done** — [18](18-v07-a05-smoke-uat-2026-07-18.md); gaps feed D4r |
| D1 | Asset slide + mô tả dự án nộp | V02, H12b, H16, D4r | [ ] BLOCKED → V02… · **skeleton slide/claim matrix chạy ngay** (chưa screenshot thiếu evidence) |

### Văn Hải

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| V07 | QA release + smoke độc lập (lần 1) | D3, D4b | [x] **Done — PASS WITH MAJORS** · [18](18-v07-a05-smoke-uat-2026-07-18.md); defect → D4r |
| V02 | Script demo 4′ + Q&A 2′, rehearsal | D4r, G02, H26, G03, G04, H12a | [ ] BLOCKED → D4r… · case-local Agent chỉ claim theo Live evidence; Global Agent/weekly briefing cần G07+ và chưa ship |
| D2 | Video ≤5 phút đúng Live URL | D1, D4r | [ ] BLOCKED → D1, D4r |
| V08 | Rà AI log → gap cho Hoàng | H05b | [ ] **DEFER** gần CP2 / trước D5 — log một thể (decision #19); không làm ngay |
| V06 | Nộp cuối + lưu xác nhận BTC | D1, D2, D3, D4r, D5, H09, H16 | [ ] BLOCKED → D1…H16 |

---

## 4. Hoàng — chi tiết task

**Lane:** docs/contract nguồn chuẩn, backend/API, deploy, release evidence.
**Read first:** PRD §§4–8, Ethics, Process §4, decisions, [EPU contract](../04-engineering/04-epu-data-integration-contract.md), [Data-ML](../04-engineering/08-data-ml-scoring-fairness-contract.md).
**Không làm:** tự viết model/fusion của Giang.
**Next wave:** target architecture [doc 13](../04-engineering/13-weekly-snapshot-global-agent-architecture.md); full Task Brief `H28/H28a/H29–H38/D6` tại [Stories — Hoàng](17-stories-hoang-weekly-agent.md).

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| H01 | P0 | Backend health + DB stub | `backend/tests/test_health.py` — **Done** |
| H05a | Recovery · ASAP 03:30 | Minimum contract/state: architecture, PRD/thuật ngữ, Process state/care boundary | Docs không mâu thuẫn PRD/Ethics/Process; đủ để mở `H06b`/`H10`/`H07` — **Done:** [arch](../04-engineering/05-system-architecture.md), Process §4, banner BRD/scope, decision #15 |
| H05b | P1 · sau H05a | AI-log template + release-evidence template | Template sẵn; không chặn API/schema — **Done:** `.ai-log/templates/*`, [release-evidence template](templates/release-evidence-item.template.md); pointer [AI-log README](../../.ai-log/README.md) + [07-release-evidence](07-release-evidence.md) |
| H10 | Recovery · ~04:00 (mốc 02:00 đã trễ) | Hoàn thiện contract EPU/Data-ML và decision từ M04 | **Done:** [EPU](../04-engineering/04-epu-data-integration-contract.md), [Data-ML](../04-engineering/08-data-ml-scoring-fairness-contract.md), decision #17; source gate ≠ approved; MVP điểm + điểm danh; `insufficient_data`; cấm synthetic; outcome nội bộ only |
| H06a | P1 · **Done** (`H06a-r`) | Pydantic internal/public envelopes — semantic Data-ML §3 | **Done:** semantic reopen landed; coverage/band/factors/`dataset_version`; 42 contract tests |
| H06b | P1 · sau H05a | Transition API đúng Process | **Done — transition core** (giữ lịch sử): `backend/app/cases/*`. **Deploy-blocker harden landed:** seed-only create, server actor, no public `advisor_ref` (21 tests) — public shell |
| H11a | P1 · **Done REVALIDATE** | Integration contract tối thiểu | **Done (`H11a-r`):** 19 integration tests; unlocks G05/T03 |
| H11b | P2 · sau G05 · T03+H26 Done | Docs agent/FE hoàn thiện | **Done — historical gate** — arch §6 + [guardrails](../04-engineering/08-agent-grounding-guardrails.md) + [doc 10](../04-engineering/10-fe-agent-integration-contract.md); case-local `AgentPanel` được thêm sau, Global Agent chưa ship |
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
| H26 | P2 · **Done** | Agent runtime E2E + release evidence | **Done:** mocked HTTP E2E `test_h26_agent_e2e.py`; `verify.ps1` 410 passed / 1 skipped; live FPT SKIP; FR-08 backend evidence lịch sử; case-local UI thêm sau; Global Agent/OpenAI migration tách sang H28+ |
| H27 | P2 · 2–4h · sau D3+D4b | Deploy frontend production lên Vercel | **Done:** `https://abg-team.vercel.app`; same-origin rewrite → Live API; production smoke health + `/review-cases` ok n=50; PR #26; chưa flip submission URL trước V07+A05 |
| H28 | Next wave · docs · **Done** | Target architecture + OpenAI provider decision | **Done — docs only:** Decision #22 + [doc 13](../04-engineering/13-weekly-snapshot-global-agent-architecture.md); không claim feature ship; [full brief](17-stories-hoang-weekly-agent.md#h28) |
| H28a | Next wave · P0 · **Done** | Khóa readiness/decision cho build | **Done:** Decision #23 + arch §16 + runbook §12; Mode B linked pending; unlock H30/H36; [full brief](17-stories-hoang-weekly-agent.md#h28a) |
| H29 | Next wave · P0 · **Done** | OpenAI Responses provider migration | **Done:** provider-neutral `model.py`; `OpenAIResponsesClient`; Settings `OPENAI_*`; FPT inactive in factory; `test_h29_*` · [full brief](17-stories-hoang-weekly-agent.md#h29) |
| H30 | Next wave · P0 · **Done** | Snapshot v2 + workflow ledger DB | **Done:** Alembic `20260718_h30_snapshot`; multi-version + active pointer; [full brief](17-stories-hoang-weekly-agent.md#h30) |
| H31 | Next wave · P0 · **Done** | Stage/promote + approved replay CLI | **Done:** `WeeklyWorkflowService` + `cli weekly run`; idempotent; [full brief](17-stories-hoang-weekly-agent.md#h31) |
| H32 | Next wave · P0 · **Done Mode B** | Linked bundle → immutable observations | **Done Mode B:** `weekly/observations.py`; combined blocked; [full brief](17-stories-hoang-weekly-agent.md#h32) |
| H33a | Next wave · P0 · **Done** | Durable case/event persistence | **Done in-memory MVP:** `CaseRepository`; GET read-only; [full brief](17-stories-hoang-weekly-agent.md#h33a) |
| H33b | Next wave · P0 · **Done** | Delta/reconcile deterministic | **Done:** full matrix; no auto-close; [full brief](17-stories-hoang-weekly-agent.md#h33b) |
| H36 | Next wave · P0 · **Done** | Production identity/RBAC/access audit | **Done:** `app/auth`; unlocks G07; [full brief](17-stories-hoang-weekly-agent.md#h36) |
| H34a | Next wave · P1 · **Done** | Weekly report materializer/API | **Done:** materializer + scoped latest API; unlocks G08; [full brief](17-stories-hoang-weekly-agent.md#h34a) |
| H34b | Next wave · P1 · **Done** | Briefing deterministic + receipt | **Done:** shown/ack APIs; OpenAI-off OK; [full brief](17-stories-hoang-weekly-agent.md#h34b) |
| H35 | Next wave · P1 · **Done** | Advisor draft v2 | **Done:** durable approved/assigned; no send; unlocks G09; [full brief](17-stories-hoang-weekly-agent.md#h35) |
| H37 | Next wave · P1 · **Done** | Global Agent backend turn/tools | **Done:** `POST /agent/turns`; capability registry; unlocks T05; [full brief](17-stories-hoang-weekly-agent.md#h37) |
| H38 | Next wave · P1 · **Done** | Safe report export | **Done:** aggregate/case watermark; no bulk ID; [full brief](17-stories-hoang-weekly-agent.md#h38) |
| D6 | Release wave · P1 · **Done ops foundation** | Scheduler/worker ops gate | **Done foundation:** kill switches + scheduler_tick + rollback stub; live EventBridge still manual; [full brief](17-stories-hoang-weekly-agent.md#d6) |
| H03 | P2 · sau H08 | Care workflow API | **Done:** approve/dismiss/defer + assign-handoff; H08 `advisor_ref`/`mapping_repair` gate; client ref ignored; `tests/test_h03_care_workflow.py` — mở G03 |
| H04 | P2 · sau M03 | Threshold/config API public semantics | **Done:** app/contracts/threshold_public.py + app/config_api/router.py; impact aggregates only; fairness MVP insufficient_data; tests/test_h04_threshold_fairness_api.py |
| H12a | P2 · ~15:00 (trước T02/G03/G04) | Runtime privacy/care copy cho UI/agent | **Done:** `frontend/src/lib/copy.ts` 4 keys Data-ML §6; mock list không “Điểm rủi ro”; mở `H12b` / giảm blocker `G03`/`G04`/`T02` |
| H12b | P2 · sau H12a · ~19:00 | Banner + asset copy | **Done:** banner + skeleton [13-h12b-asset-copy-skeleton.md](13-h12b-asset-copy-skeleton.md); forecast/fusion = research/blocked; điểm danh theo thời gian = MVP |
| D3 | P2 · ~20:30 | GitHub public, PII/secret scan | **Done** tree + [scan notes](10-d3-github-pii-secret-scan.md); residual history **accept CP2**; trước final: clean submission repo hoặc purge có phê duyệt |
| D4a | P2 · sớm sau H07+D3 | Live shell: deploy infra, health, rollback sẵn | **Done** — Live shell: API http://52.74.255.88:8000/health · FE http://52.74.255.88:3000 · EC2 i-0b0576945d080cb3f (**NOT** D4b) |
| D4b | P2 · sau H02+G02 | Product smoke list→case ẩn danh trên Live | **Done** 2026-07-18 ~13:05 +07: health `database:true`; list state=ok n=50; detail `rc-s-00518c9485a9` / `can_ra_soat`; FE login+dashboard 200; CORS OK; no PII/score leak; [evidence](07-release-evidence.md) §2 |
| D4r | P2 · sau V07+A05 | Owner fix → redeploy → re-smoke | **Done** — Vercel=`https://abg-team.vercel.app`; API `:d4r` `sha256:2b01b24a…`; advisor 200; explanation `unavailable` fail-closed; bulk export ẩn |
| H16 | P3 · sau V05 | Acceptance matrix + release evidence | Phụ thuộc **A05 + V07 + V05**; mỗi FR/CP2 item có evidence hoặc limitation |
| H09 | P3 · 09:00 | README + verify/known-limit | Khớp deploy và scope thật |
| D5 | P3 · 10:00 | AI collaboration log từ V08 | Gap có owner; sạch PII/secret |
| H15 | P1 · MVP | Attendance source approval + amendment contract | **Done** decision #18: [12-h15…](12-h15-attendance-approval-prep.md) + fixture `mvp-attendance-over-time`; team approver |
| H17 | Post-MVP · **FREEZE** | Hybrid forecast/fusion public API theo H14 | Không làm tới sau submission |

**Verify:** link/traceability, contract test, docs khớp code/public DTO.

---

## 5. Khánh Duy — chi tiết task (FE — decision #24)

**Lane:** Frontend integration và UI (**không** nhầm Hạ Giang).
**Read first:** PRD §5; Ethics; H11a-r (không bắt đầu trên H11a cũ).
**Không làm:** tự chốt copy/contract; raw score; “Điểm rủi ro”; synthetic/legacy attendance mock sau G05.
**Lịch sử:** Task `M*` Done trong board §3 là công việc ML trước #24 (xem §6 / evidence).

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| G01 | P0 | FE shell + list mock tạm | Smoke — **Done** (mock phải bị G05 thay) · historical |
| G05 | P1 · sau H11a-r | Thay hẳn mock synthetic/K-12 bằng public DTO + fixture đã validate | **Done** — types/fixtures/limitations; xóa mock-review-list; AI-log G05 · historical |
| G02 | P1 · sau H02 | Dashboard → cohort → case dùng API | **Done** — `lib/api.ts` live `/review-cases`; fail-closed; AI-log G02 · historical |
| G03 | P2 · sau H12a | Care UI theo Process states + defer = giữ Pending | **Done** — `CareActions.tsx`; AI-log G03 · historical |
| G04 | P2 · sau H12a | Fairness/privacy/threshold panel | **Done** — login/role + Fairness/Threshold; AI-log G04; PR #23 · historical |
| G06 | P2 stretch · sau H22 | Filter theo advisor + Copy/`mailto:` bản nháp lô | FR-12; draft-only; **TODO — owner Duy**; H22 Live còn thiếu tới D4r |
| G07 | Next wave · sau H36 | Authenticated layout + global Agent shell | **TODO — owner Duy** |
| G08 | Next wave · sau G07 | Weekly briefing/report UI | BLOCKED → G07 · **owner Duy** |
| G09 | Next wave · sau G07 | `/notify` advisor draft FE (H35) | BLOCKED → G07 · **owner Duy** |

**Verify:** lint, production build, behavior smoke. Chỉ public DTO.

---

## 6. Giang — chi tiết task (ML — decision #24)

**Lane:** Data/ML, source validation, baseline/model/predict (**Giang** = Nguyễn Trường Giang).
**Read first:** PRD §§4,7–8; signal catalog; Ethics §§5–6; [EPU contract](../04-engineering/04-epu-data-integration-contract.md); [Data-ML](../04-engineering/08-data-ml-scoring-fairness-contract.md); ML tests gần nhất.
**Không làm:** hoàn thiện Markdown contract/PRD; dùng legacy synthetic đã liệt kê; hybrid/`M07`/`M08` tới sau submission; đưa `is_dropout_outcome`/group attr vào scoring.
**Lịch sử:** Task `M*` Done bên dưới / board §3 phần lớn làm bởi Khánh Duy trước #24.

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| M01 | P0→P1 | Quarantine/remove legacy ML synthetic | **Done** PR #16 · historical |
| M04 | Recovery · ASAP 03:30 | Handoff Data/ML | **Done:** [10-m04…](10-m04-data-ml-handoff.md) · historical |
| H06c | P1 · sau H10 | `FairnessReport` schema + fail-closed fixture | **Done** PR #17 · historical |
| M05a | P1 · sau H10 | **Build** source gate | **Done** PR #17 · historical |
| M05b | P1 · sau M05a | **Approved source available** | **Done** [14-m05b…](14-m05b-semester-approval.md) · historical |
| M06 | P1 · sau M05b | Fixture domain + attendance | **Done** · historical |
| M02 | P1 · baseline | Baseline ML scoring | **Done** · historical |
| M07 | **FREEZE** · **owner Giang** | Nghiên cứu forecast/fusion | Không tranh slot MVP; chỉ sau submission |
| M03 | P2 | Fairness gate FPR/ΔFPR/N hoặc `insufficient_data` | **Done** · historical |
| M08 | **FREEZE** · **owner Giang** | Attendance forecasting + gated fusion | Post-MVP; không làm tới sau submission |

### M07 — yêu cầu handoff hybrid (sau submission)

Chỉ chạy sau submission / khi unfreeze (**owner Giang**). So sánh semester feature vs forecast attendance: data readiness, window, timestamp order, horizon, label cutoff/no leakage, missingness, nghỉ có phép, gated/late fusion. Chỉ đề xuất:

- `TermEvidence` và `AttendanceForecastEvidence` tách riêng; coverage, freshness, provenance, `model_version`, `calculated_at`, ready/`insufficient_data`.
- Fusion chỉ khi cả hai branch qua gate; absence không zero-impute, không đổi priority.
- Public/agent chỉ `review_priority_band`, factors/evidence, limitations.

**Verify:** determinism, missing/stale, formula/denominator, PII/source gate.

---

## 7. Thu Trang — chi tiết task

**Lane:** Agent adapter, grounding/refusal tests; **nộp CP2 (`V05`)**.
**Read first:** PRD §5.4/FR-08; Ethics §8; H11a-r / H12a; [16-stories-thu-trang.md](16-stories-thu-trang.md) cho V05.
**Không làm:** tự tính/sửa mức ưu tiên; score/dropout conclusion; hybrid T04 tới sau submission; nộp CP2 trước `D4r`.

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| T03 | P1 · **Done** | Agent interface, fixture, refusal/adversarial | **Done:** `AgentExplanation` contract consume H11a envelope; 12 ca adversarial (7 refusal + ok/insufficient/unavailable, chống over-refusal); evidence `backend/tests/agent/` (26 tests) + `backend/tests/fixtures/agent/` + [doc 08](../04-engineering/08-agent-grounding-guardrails.md); mocked-only, không live call |
| T01 | P1 · **Done** | Agent stub từ fixture | **Done:** stub deterministic (guardrails-first → context-status fail-closed → grounded assembly); 12/12 adversarial + determinism + grounding tests xanh; evidence `backend/app/agent/stub.py`, `guardrails.py`, `backend/tests/agent/test_agent_stub.py` |
| T02 | P2 · **Done core/library** | Grounded explanation adapter từ safe context | **Done:** FPT text adapter + mocked grounding; chỉ band/factors/coverage/limits. **Không** claim server context/HTTP/runtime E2E — theo `H23`–`H26` |
| T04 | **FREEZE** | Agent adapter hybrid | Chỉ sau submission + H17 |
| V05 | P2 · ~22:45 · sau D4r | Nộp Checkpoint 2 | **Done** — Thu Trang nộp BTC Live=`https://abg-team.vercel.app` + GitHub; receipt ngoài repo → Hoàng/`H16` |

**Verify:** grounding/refusal/adversarial mocked tests. V05: form BTC + receipt ngoài repo.

---

## 8. Hạ Giang (`giang`) — chi tiết task

**Owner:** Trần Hạ Giang — UAT / claim-copy / slide skeleton. **Không** nhầm với Giang (Nguyễn Trường Giang = ML).
**Bắt đầu skeleton ngay; full UAT từ P2/Live.** Story: [08-stories-giang.md](08-stories-giang.md).

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| A05 | P2 · song song V07; **bắt buộc trước D4r** | UAT/claim-copy review | **Done** — [18](18-v07-a05-smoke-uat-2026-07-18.md); gap → Hoàng/`D4r` |
| D1 | P3 · 09:00 | Asset slide + mô tả | Skeleton/claim matrix **ngay**; finalize URL/screenshot sau D4r + H12b/H16 |

**A05:** list→case→review/handoff trên Live URL; rà care/privacy/fairness/claim; gửi Hoàng + **bắt buộc feed `D4r`**.

**D1:** chỉ copy/screenshot từ `H12b`/`H16` và Live URL đã `D4r`; điểm danh theo thời gian = MVP; forecast/fusion chỉ Post-MVP/research nếu chưa Done.

---

## 9. Văn Hải — chi tiết task

**Bắt đầu từ P2; V08 defer gần CP2/D5 (decision #19).** Story: [09-stories-van-hai.md](09-stories-van-hai.md). Evidence: [07-release-evidence.md](07-release-evidence.md). **`V05` không còn thuộc Hải** → Thu Trang ([16](16-stories-thu-trang.md)).

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| V07 | P2 · sau D4b | QA release + smoke độc lập lần 1 | **Done — PASS WITH MAJORS** · [18](18-v07-a05-smoke-uat-2026-07-18.md); defect → `D4r` |
| V02 | P3 · 08:00 | Script 4′ + Q&A 2′, rehearsal | Script skeleton sớm; Live sau `D4r` |
| D2 | P3 · 09:30 | Video ≤5 phút | Đúng Live URL sau `D4r` |
| V08 | **DEFER** · gần CP2 / trước D5 | Rà AI log một thể | Depends `H05b`; thu thập manifest + link **một lần**; gap → Hoàng/`D5`; CP2 không phụ thuộc V08 |
| V06 | P3 · 10:30 | Nộp cuối | Sau evidence `H16` đã khóa CP2+final; CP2 đã do Thu Trang nộp ở `V05` |

---

## 10. Quy ước, rủi ro và việc làm ngay

| Quy ước / risk | Cách xử lý |
|:--|:--|
| Realign §1.2 | Board này là SoT execution; không giữ snapshot “H11a mở G05/T03” cũ |
| H06a/H11a semantic | `H06a-r` + `H11a-r` **Done**; `G05`/`T03` **Done** |
| H06b ≠ deploy-ready (lịch sử) | Transition-core Done; deploy-blocker harden landed (seed-only create / server actor / no public `advisor_ref`) |
| Critical path song song | Data/API/FE tới **V05 Done**; còn `H16`/`H09`/P3 release |
| Source gate ≠ approved data | `M05b`/`H15` Done (decision #18); Live import LF hashes `73274079…` / `78d7153f…` |
| D3 residual history | Accept CP2; quyết định clean submission trước final |
| Release dồn muộn | Slide/script skeleton **ngay**; `V08` AI log **một thể** gần CP2/D5 (decision #19) |
| Advisor mail draft | Stretch `H21`→`H22`✓→`G06` (FR-12); **không** block G02/D4b; draft-only |
| Agent runtime overclaim | `H23`–`H26` = backend HTTP mocked-FPT history; repo có case-local `AgentPanel`, nhưng **không** claim Global Agent / weekly briefing / production RBAC / live OpenAI; target theo `H28+` |
| Hybrid | FREEZE `M07`/`H14`/`M08`/`H17`/`T04` tới sau submission |
| FE scoping gap (G02) | `ReviewCase` public thiếu `cohort`/`department`/`class_code` — FE chưa scoping khoa/lớp; **decision cần Hoàng chốt** (mở rộng allowlist H11a hoặc chấp nhận giới hạn MVP); không tự thêm field |
| Giang vs Hạ Giang | Giang = Nguyễn Trường Giang = **ML**; Khánh Duy = **FE**; Hạ Giang = UAT/slide (decision #24) |
| QA defects | V07 **và** A05 → owner fix → `D4r` → **`V05` (Thu Trang)** |
| V05 owner | **Thu Trang** nộp CP2; Hải giữ V07 / V02 / D2 / V08 / V06 |
| Vercel candidate (`H27`) | Hoàng deploy FE; **D4r flip Live URL nộp = Vercel** sau re-smoke |

1. **Ngay:** Hoàng — **`H16`** evidence CP2. Văn Hải — V02/D2. **Hạ Giang** — D1 slide trên Live đã nộp. **Khánh Duy** — FE/`G06`. **Giang** — ML freeze.
2. Critical path CP2: `D4b` ✓ → `V07`✓+`A05`✓ → `D4r`✓ → **`V05`✓ (Thu Trang)**. Stretch mail: H22 Live + G06 (**Duy**).
3. Attendance Live: known-limit `attendance_source_unapproved` trừ khi Duy/Giang kịp.
4. `V07`/`A05`/`D4r`/`V05` **Done**; decision **#24** Duy↔Giang; tiếp `H16`/`H09`/P3.
5. Trước handoff: verify phù hợp; trước final: `scripts/verify.ps1`, `git diff --check`, `git status --short`.
