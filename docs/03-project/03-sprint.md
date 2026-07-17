# Sprint — Silent Shield (17–19/7/2026)

> Nguồn chuẩn: [Quy chế VAIC](../01-requirements/01-vaic-rules.md) · [PRD MVP](../02-product/04-prd.md) · [Process](../02-product/03-process.md) · [RULES.md](../../RULES.md).
>
> **Điều chỉnh phân công 18/7:** Hoàng là owner duy nhất hoàn thiện tài liệu/contract nguồn chuẩn. Build tập trung vào Hoàng, Khánh Duy, **Giang** (FE) và Thu Trang. **Hạ Giang** (board ID `giang`) và Văn Hải nhận task từ P2: QA/UAT/claim/slide skeleton và release smoke/submission — không sửa canonical docs/code.
>
> **Chặn phạm vi hybrid (forecasting):** Freeze hoàn toàn `M07`/`H14`/`M08`/`H17`/`T04` tới sau submission. Điểm danh theo thời gian **thuộc MVP** (sau `H15`); thiếu nguồn → `insufficient_data`; **không** thay bằng synthetic để claim E2E.
>
> **Realign chốt ~05:45 18/7:** Direction giữ nguyên (prototype care/review, không claim dự báo dropout đã chứng minh). Execution: `H06a` REOPEN semantic; `H11a` REVALIDATE (tạm chặn consumer `G05`/`T03`); `H06b` giữ Done transition-core (chưa deploy-ready); `D3` Done + residual history accept CP2; ba nhánh song song Data / Profile / Contract safety. Chi tiết §1.2.

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
| P0 | 17/7 11:00–15:00 | Scaffold | Health, FE shell | [x] (M01 legacy chưa sạch — reopen) |
| P0.5 | kế hoạch 17/7 22:30–18/7 00:30 | Contract lock | `H05a` + `M04` Done; schema/code chỉ theo contract | **[x] Done** — `H05a` + `M04` + `H10` (mốc cũ đã trễ) |
| P1 | recovery 18/7 sáng → CP1 | Vertical slice | Baseline điểm theo kỳ + điểm danh theo thời gian + CP1 | Mở — còn `M05a`… |
| P2 | 18/7 11:00–23:00 | Rubric + live | UI/API/test + QA→fix→re-smoke + CP2 | Chưa mở đủ |
| P3 | 18/7 23:00–19/7 11:00 | Release | Docs cuối, slide/video, AI log, form nộp | Chưa |

### 1.1 Recovery P0.5 → P1 (chốt lúc ~02:03 +07)

| Việc | Owner | Mục tiêu mới | Ghi chú |
|:--|:--|:--|:--|
| `H05a` minimum contract/state | Hoàng | ASAP · trước 03:30 | **Done** — mở `H06b`/`H07` |
| `M04` handoff Data/ML | Khánh Duy | ASAP · trước 03:30 | **Done** — [handoff](10-m04-data-ml-handoff.md) |
| `H10` contract EPU/decision | Hoàng | ngay sau `H05a`+`M04` · ~04:00 | **Done** (mốc 02:00 đã trễ) — EPU + Data-ML + decision #17 |
| `H05b` AI-log + release template | Hoàng | sau `H05a` · trước V08 | **Done** — mở `V08` |
| CP1 (`H13`) | Hoàng | vẫn 11:00 | Nội dung paste sẵn; **BLOCKED → human BTC submit** trước 11:00; không claim hybrid |

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

**Bổ sung board:** Critical path còn nhánh `M01→H18` vì `H02` depends `M02` **và** `H18`. `H06b` = **Done — transition core**; thêm deploy-blocker hardening (auth/scope/create route/`advisor_ref` leakage) trước public deploy — không xóa lịch sử Done, không hiểu nhầm deploy-ready.

**Owner ngay:** Hoàng — H13 + chase `M05b`/`H15` + `H06a-r`/`H11a-r` + care deploy-blocker + `D4a`. Khánh Duy — `M05a` rồi `M01`/`H06c`. Giang — `G05` sau `H11a-r`. Thu Trang — `T03` sau `H11a-r`. Văn Hải — `V08` ngay. **Hạ Giang** — UAT/slide/claim skeleton (không đợi Live URL cho skeleton).

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
Data:     M05a → M05b(ext) → M06 → H20 → H08 → M02 ─┐
Profile:  M01 → H18 ───────────────────────────────┼→ H02 → G02 → D4b
Contract: H06a-r → H11a-r → (G05 ∥ T03) ───────────┘
Deploy:   (H07 ∥ D3) → D4a (shell) → D4b (product smoke) → V07 + A05 → D4r → V05
```

`H02` **bắt buộc** cả `M02` và `H18`. `H19` Done (schema rỗng). `H11a` lịch sử Done nhưng đang REVALIDATE — consumer `G05`/`T03` chỉ sau `H11a-r`.

**Release loop bắt buộc:** `D4a` (Live shell) sớm sau `H07`+`D3` → `D4b` (product smoke sau `H02`/`G02`) → `V07` **và** `A05` ghi defect → owner fix → `D4r` → mới `V05`. Không nộp CP2 trong cửa sổ 10 phút sau smoke đầu.

**Freeze tới sau submission:** `M07` → `H14` → `M08` → `H17` → `T04`. `H15` thuộc **MVP** (approval artifact). Thiếu `M05b`/`H15`: demo `insufficient_data` trung thực — **cấm** synthetic E2E.

### Hoàng

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| H01 | Backend health + DB stub | — | [x] |
| H05a | Minimum contract/state (arch, PRD/thuật ngữ, Process state/care) | — | [x] Done — arch + Process §4 + thuật ngữ MVP |
| H05b | AI-log template + release-evidence template | H05a | [x] Done — templates + pointers; không rewrite policy |
| H10 | Contract EPU/Data-ML + decision từ M04 | H05a, M04 | [x] Done — EPU + [08 Data-ML](../04-engineering/08-data-ml-scoring-fairness-contract.md) + decision #17 · mốc 02:00 đã trễ |
| H06a | Pydantic internal/public envelopes | H10 | [ ] **REOPEN** semantic (`H06a-r`) — coverage/band/factors/dataset_version; regression trước consumer |
| H06b | Transition API theo Process state machine | H05a | [x] **Done — transition core** (15 tests); **chưa deploy-ready** — cần hardening auth/scope/create-route/`advisor_ref` trước public |
| H11a | Integration contract tối thiểu cho G05/T03 | H06a | [ ] **REVALIDATE** (`H11a-r`) — BLOCKED → H06a-r; tạm chặn G05/T03 |
| H11b | Docs agent/FE hoàn thiện sau build | H11a, G05, T03 | [ ] BLOCKED → H11a-r, G05, T03 |
| H07 | Deployment/runbook docs | H05a | [x] Done — runbook draft; finalize Live/smoke/rollback tại D4a/D4b |
| H19 | MVP persistence schema versioned + legacy mapping | H10 | [x] Done — Alembic 7 bảng `dwh` + 4 migrate tests; schema doc |
| H20 | Transactional approved-fixture import vào `dwh` | H19, M06 | [ ] BLOCKED → M06 · H19 Done |
| H08 | `dwh` → normalized internal DTO read adapter | H20, H06a | [ ] BLOCKED → H20, H06a-r |
| H18 | Quarantine legacy ML synthetic khỏi API/MVP path | M01 | [ ] BLOCKED → M01 · nhánh Profile song song Data |
| H14 | Decision/contract research forecast/fusion từ M07 | M07 | [ ] BLOCKED → M07 · **FREEZE** tới sau submission |
| H02 | API list/detail ReviewCase public | H06a, M02, H18 | [ ] BLOCKED → M02, H18, H06a-r |
| H13 | Nội dung + nộp Checkpoint 1 | H05a, H10 | [ ] TODO — paste-ready sẵn ([11-h13-cp1-btc-draft.md](11-h13-cp1-btc-draft.md)); Hoàng nộp form BTC + receipt trước 11:00 |
| H03 | Care workflow API + advisor_ref gate | H05a, H06b, H08 | [ ] BLOCKED → H08 · H06b transition-core Done; deploy hardening riêng |
| H04 | Threshold/config API (public semantics) | M03 | [ ] BLOCKED → M03 |
| H12a | Runtime privacy/care copy (UI/agent) | H05a, H10 | [x] Done — 4 copy keys Data-ML §6; bỏ “Điểm rủi ro” trên FE |
| H12b | Post-MVP banner + asset copy | H12a | [ ] TODO — mở sau H12a; skeleton sớm cho Hạ Giang |
| D3 | GitHub public + PII/secret scan | — | [x] Done — tree sạch; **residual history accept CP2**; trước final: clean submission repo hoặc purge có phê duyệt |
| D4a | Deploy infrastructure / Live shell (health + rollback sẵn) | H07, D3 | [ ] TODO — mở ngay (không chờ H02/G02) |
| D4b | Product smoke list→case trên Live URL | D4a, H02, G02 | [ ] BLOCKED → D4a, H02, G02 |
| D4r | Fix từ QA → redeploy → re-smoke | D4b, V07, A05 | [ ] BLOCKED → D4b, V07, **A05** |
| H16 | Acceptance matrix + release evidence | A05, V07, V05 | [ ] BLOCKED → A05, V07, V05 |
| H09 | README + verify/known-limit note cuối | H02, D4r, H16 | [ ] BLOCKED → H02, D4r, H16 |
| D5 | AI collaboration log từ V08 | V08 | [ ] BLOCKED → V08 · V08 chạy ngay |
| H15 | Attendance source approval + amendment (**MVP**) | H10 + **external approval artifact** | [ ] BLOCKED → data-owner · prep ([12-h15…](12-h15-attendance-approval-prep.md)); không Done tới khi có approval artifact |
| H17 | Post-MVP hybrid public API/envelope (forecast/fusion) | H14, M08 | [ ] BLOCKED → H14, M08 · **FREEZE** |

### Khánh Duy

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| M01 | Quarantine/remove legacy ML synthetic (reopen) | — | [ ] REOPEN — chưa sạch consumer |
| M04 | Handoff kỹ thuật Data/ML cho Hoàng | — | [x] Done — [handoff](10-m04-data-ml-handoff.md); khóa bởi H10 |
| H06c | FairnessReport schema + fail-closed fixture | H10 | [ ] TODO — mở sau H10 |
| M05a | Build semester source gate (code/tests) | H10 | [ ] TODO — mở sau H10 |
| M05b | Approved source available (artifact duyệt) | M05a + data-owner approval | [ ] BLOCKED → M05a + approval |
| M06 | Fixture 4 bảng domain + manifests + quality tests | M05b | [ ] BLOCKED → M05b |
| M02 | Baseline semester ML | M06, H06a, H08 | [ ] BLOCKED → M06, H08, H06a-r |
| M07 | Nghiên cứu hybrid (research-only) | M02, H02, H13 | [ ] **FREEZE** tới sau submission |
| M03 | Fairness gate FPR/ΔFPR/N | M02, H06c | [ ] BLOCKED → M02, H06c |
| M08 | Attendance forecast + gated fusion (Post-MVP) | H15, M02, H14 | [ ] **FREEZE** tới sau submission |

### Giang

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| G01 | FE shell + list mock | — | [x] (mock tạm; G05 phải thay) |
| G05 | Thay mock bằng public DTO/fixture đã validate | H11a | [ ] BLOCKED → H11a-r · không bắt đầu trên contract chưa revalidate |
| G02 | Dashboard → cohort → case dùng API | G05, H02 | [ ] BLOCKED → G05, H02 |
| G03 | Care UI review/handoff | H03, H12a | [ ] BLOCKED → H03 · H12a Done |
| G04 | Fairness/privacy/threshold panel | H04, H12a | [ ] BLOCKED → H04 · H12a Done |

### Thu Trang

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| T03 | Agent interface + fixture + refusal/adversarial | H11a | [ ] BLOCKED → H11a-r · guard/refusal sau revalidate; **không** cần H02 |
| T01 | Agent stub từ fixture, refusal tests xanh | T03, H06a | [ ] BLOCKED → T03, H06a-r |
| T02 | Agent grounded explanation từ API/ML | T01, H02, H12a | [ ] BLOCKED → T01, H02 · H12a Done |
| T04 | Agent adapter hybrid (Post-MVP) | H17 | [ ] **FREEZE** tới sau submission |

### Hạ Giang (`giang`)

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| A05 | UAT / claim-copy review → gap cho Hoàng | H02, G02, H03, G03, M03, H04, G04, T02, D4b, H12a | [ ] BLOCKED → H02… · skeleton checklist **chạy ngay**; full UAT sau D4b; **bắt buộc trước D4r** |
| D1 | Asset slide + mô tả dự án nộp | V02, H12b, H16, D4r | [ ] BLOCKED → V02… · **skeleton slide/claim matrix chạy ngay** (chưa screenshot thiếu evidence) |

### Văn Hải

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| V07 | QA release + smoke độc lập (lần 1) | D3, D4b | [ ] BLOCKED → D4b · D3 Done |
| V05 | Nộp Checkpoint 2 | D3, D4r, V07 | [ ] BLOCKED → D3, D4r, V07 |
| V02 | Script demo 4′ + Q&A 2′, rehearsal | D4r, G02, T02, G03, G04, H12a | [ ] BLOCKED → D4r… · script skeleton sớm |
| D2 | Video ≤5 phút đúng Live URL | D1, D4r | [ ] BLOCKED → D1, D4r |
| V08 | Rà AI log → gap cho Hoàng | H05b | [ ] **TODO ngay** — H05b Done; backfill AI log từng thành viên |
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
| H06a | P1 · **REOPEN** | Pydantic internal/public envelopes — semantic Data-ML §3 | **REOPEN (`H06a-r`):** cấm coverage=0+`ok`; cấm band khi không nhánh ready; cấm factors rỗng khi `ok`; cấm synthetic `dataset_version` trên public case; regression tests rồi mới mở consumer |
| H06b | P1 · sau H05a | Transition API đúng Process | **Done — transition core:** `backend/app/cases/*` + 15 tests. **Không deploy-ready:** thêm hardening (tắt/seed-only create; không tin actor client; tách public projection; không public `advisor_ref`) trước D4a/public |
| H11a | P1 · **REVALIDATE** | Integration contract tối thiểu | **REVALIDATE (`H11a-r`)** sau H06a-r; tạm chặn G05/T03; envelopes + fixtures phải khớp semantic mới |
| H11b | P2 · sau G05+T03 | Docs agent/FE hoàn thiện | Guardrail đầy đủ khớp code đã build |
| H07 | P1 · sau H05a | Deployment/runbook: env, CORS, seed, health, smoke, rollback | Runbook không secret — **Done:** [06-deploy-runbook](../04-engineering/06-deploy-runbook.md) draft từ arch; linked docs index + arch; Live URL/smoke/rollback finalize tại `D4a`/`D4b` |
| H19 | P1 · sau H10 | Thiết kế persistence MVP versioned: mapping metadata legacy DWH → schema `dwh` mới và migration DB rỗng | **Done:** [Schema persistence](../04-engineering/07-mvp-persistence-schema.md); Alembic 7 bảng `dwh` + `tests/test_dwh_migrate.py` (4); không copy schema/row legacy/PII; attendance table rỗng tới `H15` |
| H20 | P1 · sau H19+M06 | Nạp transactional fixture M06 đã được duyệt vào `dwh` | Chỉ đọc artifact ngoài repo có M05b approval; hash/count/schema/PII gate fail → rollback/zero write; re-run idempotent; readiness report không PII |
| H08 | P1 · sau H20+H06a | `dwh` → `NormalizedStudentRecord`/`ScoringFeatures` read adapter | Provenance/coverage/freshness; fail closed; không chiếu outcome vào scoring/public; `advisor_ref` thiếu giữ mapping-repair; chuyên cần theo thời gian khi có snapshot `H15` |
| H18 | P1 · song song M01 | Quarantine legacy `EarlyWarning*` / synthetic attendance-week / synth group khỏi API/MVP path | Test fail nếu MVP path còn import legacy/synthetic; không raw risk public; **không** cấm chuỗi điểm danh đã duyệt qua `H15` |
| H14 | Post-CP2 | Decision/contract research forecasting/fusion từ M07 | Tách `TermEvidence`/`AttendanceForecastEvidence`; ready/`insufficient_data` |
| H02 | P1 · sau M02+H18 | API list/detail chỉ `ReviewCase` public | Depends **M02 và H18** (Profile song song Data); happy + empty/error/stale/`insufficient_data` |
| H13 | P1 · 11:00 | Nộp Checkpoint 1 | Nội dung 4 trường sẵn ([draft](11-h13-cp1-btc-draft.md)); chưa Done — chờ human nộp form + receipt; không claim forecast/hybrid đã ship |
| H03 | P2 · sau H08 | Care workflow API | Approve / dismiss / defer(keep Pending) / assign-handoff tests; **`advisor_ref` thiếu ⇒ dừng handoff** — H06b transition-core Done; còn H08 + deploy hardening |
| H04 | P2 · sau M03 | Threshold/config API public semantics | Không raw score |
| H12a | P2 · ~15:00 (trước T02/G03/G04) | Runtime privacy/care copy cho UI/agent | **Done:** `frontend/src/lib/copy.ts` 4 keys Data-ML §6; mock list không “Điểm rủi ro”; mở `H12b` / giảm blocker `G03`/`G04`/`T02` |
| H12b | P2 · sau H12a · ~19:00 | Banner + asset copy | Forecast/fusion ghi research/blocked; **điểm danh theo thời gian = MVP** — **mở** (H12a Done); skeleton sớm cho Hạ Giang |
| D3 | P2 · ~20:30 | GitHub public, PII/secret scan | **Done** tree + [scan notes](10-d3-github-pii-secret-scan.md); residual history **accept CP2**; trước final: clean submission repo hoặc purge có phê duyệt |
| D4a | P2 · sớm sau H07+D3 | Live shell: deploy infra, health, rollback sẵn | Không chờ product API; evidence Live URL shell |
| D4b | P2 · sau H02+G02 | Product smoke list→case ẩn danh trên Live | Happy hoặc fail-closed `insufficient_data` theo go/no-go nguồn |
| D4r | P2 · sau V07+A05 | Owner fix → redeploy → re-smoke | **A05 bắt buộc** cùng V07 trước D4r; cửa sổ fix ≥45–60 phút trước V05 |
| H16 | P3 · sau V05 | Acceptance matrix + release evidence | Phụ thuộc **A05 + V07 + V05**; mỗi FR/CP2 item có evidence hoặc limitation |
| H09 | P3 · 09:00 | README + verify/known-limit | Khớp deploy và scope thật |
| D5 | P3 · 10:00 | AI collaboration log từ V08 | Gap có owner; sạch PII/secret |
| H15 | P1 · MVP | Attendance source approval + amendment contract | **External:** data-owner approval artifact. Prep only: [12-h15…](12-h15-attendance-approval-prep.md). **Giữ BLOCKED** tới khi có artifact — không fake Done |
| H17 | Post-MVP · **FREEZE** | Hybrid forecast/fusion public API theo H14 | Không làm tới sau submission |

**Verify:** link/traceability, contract test, docs khớp code/public DTO.

---

## 5. Khánh Duy — chi tiết task

**Lane:** Data/ML, source validation, baseline semester.
**Read first:** PRD §§4,7–8; signal catalog; Ethics §§5–6; [EPU contract](../04-engineering/04-epu-data-integration-contract.md); [Data-ML](../04-engineering/08-data-ml-scoring-fairness-contract.md); ML tests gần nhất.
**Không làm:** hoàn thiện Markdown contract/PRD; dùng synthetic hoặc attendance thiếu approval; hybrid/`M07`/`M08` tới sau submission; đưa `is_dropout_outcome`/group attr vào scoring.

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| M01 | P0→P1 REOPEN | Quarantine/remove legacy ML synthetic: attendance tuần, synth socioeconomic/ethnicity, raw risk path trong `early_warning` | README + module không còn MVP consumer; test cấm feature attendance-week/synth group trong scoring |
| M04 | Recovery · ASAP 03:30 | Handoff Data/ML: semester + attendance-over-time baseline, source/quality gate, threshold/FPR, giới hạn forecast/fusion | **Done:** [10-m04…](10-m04-data-ml-handoff.md); **không** đồng nghĩa dữ liệu đã được duyệt |
| H06c | P1 · sau H10 | `FairnessReport` schema + fail-closed fixture | Metric chỉ khi group + GT + N hợp lệ |
| M05a | P1 · sau H10 | **Build** source gate: register, hash/count, PII exclusion, fail-closed khi thiếu approval | Code/tests gate; H10 Done ≠ source approved |
| M05b | P1 · sau M05a | **Approved source available** | Artifact duyệt của data owner (owner, quyền, snapshot hash, record count); thiếu → giữ `insufficient_data`, không bịa fixture “đã duyệt” |
| M06 | P1 · sau M05b | Fixture: bảng domain điểm (+ `attendance_event` khi `H15` sẵn sàng) + `source_manifest` + `data_quality_report` | Deterministic, pseudonymous; không cross-join/PII/token; outcome chỉ trong evaluation |
| M02 | P1 · baseline | Baseline ML: trend/volatility điểm + chuyên cần theo thời gian (khi có) + factors + coverage | Sau M06+H08+H06a-r; cấm synthetic/legacy; không dùng `is_dropout_outcome` trong score |
| M07 | **FREEZE** | Nghiên cứu forecast/fusion | Không tranh slot MVP; chỉ sau submission |
| M03 | P2 | Fairness gate FPR/ΔFPR/N hoặc `insufficient_data` | Formula/denominator/group-separation; outcome chỉ evaluation |
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
| G05 | P1 · sau H11a-r | Thay hẳn mock synthetic/K-12 bằng public DTO + fixture đã validate | **BLOCKED → H11a-r**; loading/error/`insufficient_data`; không còn “Điểm rủi ro” / synthetic demo copy |
| G02 | P1 · sau H02 | Dashboard → cohort → case dùng API | Lint/build/smoke; fail-closed nếu go/no-go nguồn fail |
| G03 | P2 · sau H12a | Care UI theo Process states + defer = giữ Pending | Chỉ action được phép; lint/build/smoke |
| G04 | P2 · sau H12a | Fairness/privacy/threshold panel | Metric hợp lệ hoặc `insufficient_data` |

**Verify:** lint, production build, behavior smoke. Chỉ public DTO.

---

## 7. Thu Trang — chi tiết task

**Lane:** Agent adapter, grounding/refusal tests.
**Read first:** PRD §5.4/FR-08; Ethics §8; H11a-r / H12a.
**Không làm:** tự tính/sửa mức ưu tiên; score/dropout conclusion; hybrid T04 tới sau submission.

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| T03 | P1 · sau H11a-r | Agent interface, fixture, refusal/adversarial | **BLOCKED → H11a-r**; ≥5 case grounded/refusal; **không cần H02/live API** |
| T01 | P1 · sau T03 | Agent stub từ fixture | Không bịa score/cause; mocked tests pass |
| T02 | P2 · sau H12a | Grounded explanation từ API/ML | Adversarial pass; chỉ band/factors/limits |
| T04 | **FREEZE** | Agent adapter hybrid | Chỉ sau submission + H17 |

**Verify:** grounding/refusal/adversarial mocked tests.

---

## 8. Hạ Giang (`giang`) — chi tiết task

**Owner:** Trần Hạ Giang — UAT / claim-copy / slide skeleton. **Không** nhầm với Giang (FE).
**Bắt đầu skeleton ngay; full UAT từ P2/Live.** Story: [08-stories-giang.md](08-stories-giang.md).

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| A05 | P2 · song song V07; **bắt buộc trước D4r** | UAT/claim-copy review | Skeleton checklist ngay; full UAT trên Live sau D4b; gap → Hoàng/`D4r`; không sửa docs/code |
| D1 | P3 · 09:00 | Asset slide + mô tả | Skeleton/claim matrix **ngay**; finalize URL/screenshot sau D4r + H12b/H16 |

**A05:** list→case→review/handoff trên Live URL; rà care/privacy/fairness/claim; gửi Hoàng + **bắt buộc feed `D4r`**.

**D1:** chỉ copy/screenshot từ `H12b`/`H16` và Live URL đã `D4r`; điểm danh theo thời gian = MVP; forecast/fusion chỉ Post-MVP/research nếu chưa Done.

---

## 9. Văn Hải — chi tiết task

**Bắt đầu từ P2; V08 chạy ngay.** Story: [09-stories-van-hai.md](09-stories-van-hai.md). Evidence: [07-release-evidence.md](07-release-evidence.md).

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| V07 | P2 · sau D4b | QA release + smoke độc lập lần 1 | Incognito; ghi defect cho owner/`D4r`; không tự sửa |
| V05 | P2 · sau D4r | Nộp Checkpoint 2 | **Chỉ sau `D4r` xanh**; BTC nhận 2 URL + xác nhận |
| V02 | P3 · 08:00 | Script 4′ + Q&A 2′, rehearsal | Script skeleton sớm; Live sau `D4r` |
| D2 | P3 · 09:30 | Video ≤5 phút | Đúng Live URL sau `D4r` |
| V08 | **ngay** | Rà AI log | Depends `H05b` — **unblocked**; yêu cầu từng thành viên backfill; gap cho Hoàng/`D5` |
| V06 | P3 · 10:30 | Nộp cuối | Sau evidence `H16` đã khóa CP2+final |

---

## 10. Quy ước, rủi ro và việc làm ngay

| Quy ước / risk | Cách xử lý |
|:--|:--|
| Realign §1.2 | Board này là SoT execution; không giữ snapshot “H11a mở G05/T03” cũ |
| H06a/H11a semantic | REOPEN/REVALIDATE trước consumer; không ship G05/T03 trên contract cũ |
| H06b ≠ deploy-ready | Transition-core Done; hardening create/auth/scope/`advisor_ref` trước public |
| Critical path song song | Data **và** Profile (`M01→H18`); `H02` cần cả hai |
| Source gate ≠ approved data | `M05a` build; `M05b` artifact; fail go/no-go → chỉ `insufficient_data` |
| D3 residual history | Accept CP2; quyết định clean submission trước final |
| Release dồn muộn | `V08` + AI log + slide/script skeleton **ngay** |
| Hybrid | FREEZE `M07`/`H14`/`M08`/`H17`/`T04` tới sau submission |
| Giang vs Hạ Giang | Giang = FE; Hạ Giang = UAT/slide/claim |
| QA defects | V07 **và** A05 → owner fix → `D4r` → mới V05 |

1. **Ngay:** Hoàng — H13 submit + `H06a-r` + care deploy-blocker + chase `M05b`/`H15` + `D4a`. Duy — `M05a` rồi `M01`/`H06c`. Văn Hải — `V08`. **Hạ Giang** — UAT/slide/claim skeleton.
2. **Sau H06a-r → H11a-r:** mở `G05` (Giang) và `T03` (Thu Trang); không chờ H02 cho T03.
3. Không coi dữ liệu đã duyệt tới `M05b`; chỉ nạp qua `H20` sau `M06`. Fail nguồn → demo fail-closed, **cấm** synthetic E2E.
4. `D4a` shell sớm; `D4b` sau H02/G02; `D4r` chỉ sau V07 **và** A05.
5. Trước handoff: verify phù hợp; trước final: `scripts/verify.ps1`, `git diff --check`, `git status --short`.
