# Sprint — Silent Shield (17–19/7/2026)

> Nguồn chuẩn: [Quy chế VAIC](../01-requirements/01-vaic-rules.md) · [PRD MVP](../02-product/04-prd.md) · [Process](../02-product/03-process.md) · [RULES.md](../../RULES.md).
>
> **Điều chỉnh phân công 18/7:** Hoàng là owner duy nhất hoàn thiện tài liệu/contract nguồn chuẩn. Build tập trung vào Hoàng, Khánh Duy, Giang và Thu Trang. Hạ Giang (viết là **giang**) và Văn Hải chỉ nhận task từ P2, chủ yếu QA/review độc lập và chuẩn bị asset trình bày–nộp bài.
>
> **Chặn phạm vi hybrid (forecasting):** Duy được nghiên cứu forecasting điểm danh + gated fusion (`M07`/`M08`). Điểm danh theo thời gian **thuộc MVP** (sau export data owner phê duyệt ở `H15`). Không được tự tạo hay dùng fixture attendance giả khi chưa có nguồn duyệt; thiếu nguồn → `insufficient_data`. Forecast/fusion vẫn ngoài CP2; không đồng nghĩa đẩy chuyên cần ra Post-MVP.
>
> **Snapshot board 18/7:** `H05a` + `M04` + `H10` Done → **P0.5 qua**; mở `H06a`/`H19`/`M05a`/`H12a`/`H13` (H15 còn chờ data-owner). Xem mục 1.1 recovery.

**Quy ước tên:** Giang = Nguyễn Trường Giang (FE); giang = Trần Hạ Giang (QA/review/presentation). ID là mã workstream ổn định; cột **Owner** mới là nguồn chuẩn phân công, không suy ra owner từ tiền tố ID.

| Thành viên | Lane đang chịu trách nhiệm | Không chịu trách nhiệm |
|:--|:--|:--|
| Hoàng | Tất cả tài liệu/contract nguồn chuẩn; backend/API; deploy; tài liệu release | Không tự viết model/fusion của Duy |
| Khánh Duy | Data/ML, source validation, baseline semester model, nghiên cứu hybrid | Không hoàn thiện Markdown contract/PRD nguồn chuẩn |
| Giang | Frontend integration và UI | Không tự chốt copy/contract |
| Thu Trang | Agent adapter, grounding/refusal tests | Không tự tính/sửa mức ưu tiên |
| giang | Từ P2: UAT, review claim/copy, slide + asset mô tả | Không sửa canonical docs hoặc code |
| Văn Hải | Từ P2: QA release, smoke độc lập, script/video/submission | Không sửa canonical docs, deploy hoặc code |

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
| CP1 (`H13`) | Hoàng | vẫn 11:00 | Scope tối thiểu từ `H05a`+`H10`; không claim hybrid — **unblocked** |

Deadline cũ P0.5 00:30 / `H10` 02:00 chỉ còn giá trị lịch sử. Board dưới dùng mốc recovery.

## 2. Boundary bắt buộc cho ML, agent và hybrid

1. MVP ship baseline từ điểm theo học kỳ **và** điểm danh theo thời gian, kèm coverage và freshness. Không có chuỗi điểm danh đã duyệt thì nhánh attendance trả `insufficient_data`; không impute 0, không tạo tuần giả, không gọi đó là hybrid/forecast. Tín hiệu chuyên cần vẫn là phạm vi MVP (`H15` + feature), không Post-MVP.
2. Model/API giữ raw score nội bộ. Đầu ra công khai chỉ là `review_priority_band`, factors/evidence, coverage, freshness, data state, model version và calculated-at.
3. Agent chỉ giải thích output model/API đã được cấp quyền. Agent không tính/sửa score, không dự báo/khẳng định dropout cho một sinh viên, không suy luận nguyên nhân và không đổi trạng thái case.
4. Fairness chỉ có metric khi đủ audit group được phê duyệt, ground truth và mẫu số; nếu thiếu thì fail closed bằng `insufficient_data`.
5. `academic_status.is_dropout_outcome` chỉ evaluation nội bộ (M02/M03 test); **không** vào scoring features, public `ReviewCase`, hay agent context.
6. Case state machine theo [Process §4](../02-product/03-process.md): `New Signal` → `Pending Review` → `Approved for Follow-up` → `Assigned` → `Follow-up in Progress` → `Resolved`/`Monitoring` (hoặc `Dismissed` từ `Pending Review`). “Hoãn” = action giữ `Pending Review` + thời điểm xem lại; **không** phải state riêng. Thiếu `advisor_ref` → dừng handoff, đưa mapping-repair queue — không handoff chỉ vì đã approve.

## 3. Board chuẩn — task / depends / status

Mỗi task có một owner. Nếu dependency chưa Done, status ghi `BLOCKED → ID`; không tự tạo fixture, fallback hoặc contract thay thế. Chi tiết outcome, gate, DoD nằm ở mục 4–9.

**Critical path MVP (đã bổ sung nhánh persistence):**
`H05a` + `M04` → `H10` → (`H06a` ∥ `H19` ∥ `M05a` → `M05b` → `M06`) → `H20` → `H08` → `M02` → `H02` → `H11a` → `G05` → `G02` → (`H07` ∥ `D3`) → `D4` → `V07` → `D4r` → `V05`.

**Release loop bắt buộc:** `D4` (smoke lần 1) → `V07`/`A05` ghi defect → owner fix → `D4r` (redeploy + re-smoke) → mới `V05`. Không nộp CP2 trong cửa sổ 10 phút sau smoke đầu.

**Không đưa lên CP2 (forecast/fusion research):** `M07` → `H14` → `M08` → `H17` → `T04`. `H15` (attendance source approval) thuộc **MVP** — mở song song sau `H10`/`M04`, không xếp Post-MVP. `M07` chỉ chạy sau `M02`+`H02`+`H13`. Nếu `H15` chưa Done, demo hiện giới hạn dữ liệu trên nhánh chuyên cần (`insufficient_data`); vẫn không được tuyên bố chuyên cần là Post-MVP.

### Hoàng

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| H01 | Backend health + DB stub | — | [x] |
| H05a | Minimum contract/state (arch, PRD/thuật ngữ, Process state/care) | — | [x] Done — arch + Process §4 + thuật ngữ MVP |
| H05b | AI-log template + release-evidence template | H05a | [x] Done — templates + pointers; không rewrite policy |
| H10 | Contract EPU/Data-ML + decision từ M04 | H05a, M04 | [x] Done — EPU + [08 Data-ML](../04-engineering/08-data-ml-scoring-fairness-contract.md) + decision #17 · mốc 02:00 đã trễ |
| H06a | Pydantic internal/public envelopes | H10 | [ ] TODO — mở sau H10 |
| H06b | Transition API theo Process state machine | H05a | [x] Done — Process §4 + forbidden + advisor_ref; 15 tests |
| H11a | Integration contract tối thiểu cho G05/T03 | H06a | [ ] BLOCKED → H06a |
| H11b | Docs agent/FE hoàn thiện sau build | H11a, G05, T03 | [ ] BLOCKED → H11a, G05, T03 |
| H07 | Deployment/runbook docs | H05a | [x] Done — runbook draft; finalize Live/smoke/rollback tại D4 |
| H19 | MVP persistence schema versioned + legacy mapping | H10 | [ ] TODO — mở sau H10 |
| H20 | Transactional approved-fixture import vào `dwh` | H19, M06 | [ ] BLOCKED → H19, M06 |
| H08 | `dwh` → normalized internal DTO read adapter | H20, H06a | [ ] BLOCKED → H20, H06a |
| H18 | Quarantine legacy ML synthetic khỏi API/MVP path | M01 | [ ] BLOCKED → M01 |
| H14 | Decision/contract research forecast/fusion từ M07 | M07 | [ ] BLOCKED → M07 · ngoài CP2 |
| H02 | API list/detail ReviewCase public | H06a, M02, H18 | [ ] BLOCKED → H06a, M02, H18 |
| H13 | Nội dung + nộp Checkpoint 1 | H05a, H10 | [ ] TODO — mở sau H10 |
| H03 | Care workflow API + advisor_ref gate | H05a, H06b, H08 | [ ] BLOCKED → H08 · H06b Done (transition core sẵn) |
| H04 | Threshold/config API (public semantics) | M03 | [ ] BLOCKED → M03 |
| H12a | Runtime privacy/care copy (UI/agent) | H05a, H10 | [ ] TODO — mở sau H10 · copy keys trong Data-ML §6 |
| H12b | Post-MVP banner + asset copy | H12a | [ ] BLOCKED → H12a |
| D3 | GitHub public + PII/secret scan | — | [x] Done — public URL + scan evidence; SĐT redacted |
| D4 | Live URL + smoke lần 1 + rollback sẵn | H07, H02, G02, D3 | [ ] BLOCKED → H02, G02 · H07+D3 Done |
| D4r | Fix từ QA → redeploy → re-smoke | D4, V07 | [ ] BLOCKED → D4, V07 |
| H16 | Acceptance matrix + release evidence | A05, V07, V05 | [ ] BLOCKED → A05, V07, V05 |
| H09 | README + verify/known-limit note cuối | H02, D4r, H16 | [ ] BLOCKED → H02, D4r, H16 |
| D5 | AI collaboration log từ V08 | V08 | [ ] BLOCKED → V08 |
| H15 | Attendance source approval + amendment (**MVP**) | H10 + **external approval artifact** | [ ] BLOCKED → data-owner · H10 Done; default cửa sổ trong Data-ML §2.2 |
| H17 | Post-MVP hybrid public API/envelope (forecast/fusion) | H14, M08 | [ ] BLOCKED → H14, M08 |

### Khánh Duy

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| M01 | Quarantine/remove legacy ML synthetic (reopen) | — | [ ] REOPEN — chưa sạch consumer |
| M04 | Handoff kỹ thuật Data/ML cho Hoàng | — | [x] Done — [handoff](10-m04-data-ml-handoff.md); khóa bởi H10 |
| H06c | FairnessReport schema + fail-closed fixture | H10 | [ ] TODO — mở sau H10 |
| M05a | Build semester source gate (code/tests) | H10 | [ ] TODO — mở sau H10 |
| M05b | Approved source available (artifact duyệt) | M05a + data-owner approval | [ ] BLOCKED → M05a + approval |
| M06 | Fixture 4 bảng domain + manifests + quality tests | M05b | [ ] BLOCKED → M05b |
| M02 | Baseline semester ML | M06, H06a, H08 | [ ] BLOCKED → M06, H06a, H08 |
| M07 | Nghiên cứu hybrid (research-only, ngoài CP2) | M02, H02, H13 | [ ] BLOCKED → M02, H02, H13 |
| M03 | Fairness gate FPR/ΔFPR/N | M02, H06c | [ ] BLOCKED → M02, H06c |
| M08 | Attendance forecast + gated fusion (Post-MVP) | H15, M02, H14 | [ ] BLOCKED → H15, M02, H14 |

### Giang

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| G01 | FE shell + list mock | — | [x] (mock tạm; G05 phải thay) |
| G05 | Thay mock bằng public DTO/fixture đã validate | H11a | [ ] BLOCKED → H11a |
| G02 | Dashboard → cohort → case dùng API | G05, H02 | [ ] BLOCKED → G05, H02 |
| G03 | Care UI review/handoff | H03, H12a | [ ] BLOCKED → H03, H12a |
| G04 | Fairness/privacy/threshold panel | H04, H12a | [ ] BLOCKED → H04, H12a |

### Thu Trang

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| T03 | Agent interface + fixture + refusal/adversarial | H11a | [ ] BLOCKED → H11a |
| T01 | Agent stub từ fixture, refusal tests xanh | T03, H06a | [ ] BLOCKED → T03, H06a |
| T02 | Agent grounded explanation từ API/ML | T01, H02, H12a | [ ] BLOCKED → T01, H02, H12a |
| T04 | Agent adapter hybrid (Post-MVP) | H17 | [ ] BLOCKED → H17 |

### giang

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| A05 | UAT / claim-copy review → gap cho Hoàng | H02, G02, H03, G03, M03, H04, G04, T02, D4, H12a | [ ] BLOCKED → H02…H12a |
| D1 | Asset slide + mô tả dự án nộp | V02, H12b, H16, D4r | [ ] BLOCKED → V02, H12b, H16, D4r |

### Văn Hải

| ID | Task | Depends | Status |
|:--|:--|:--|:--|
| V07 | QA release + smoke độc lập (lần 1) | D3, D4 | [ ] BLOCKED → D4 · D3 Done |
| V05 | Nộp Checkpoint 2 | D3, D4r, V07 | [ ] BLOCKED → D3, D4r, V07 |
| V02 | Script demo 4′ + Q&A 2′, rehearsal | D4r, G02, T02, G03, G04, H12a | [ ] BLOCKED → D4r…H12a |
| D2 | Video ≤5 phút đúng Live URL | D1, D4r | [ ] BLOCKED → D1, D4r |
| V08 | Rà AI log → gap cho Hoàng | H05b | [ ] TODO — H05b Done; sẵn sàng rà AI log |
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
| H06a | P1 · sau H10 | Pydantic internal/public envelopes | Public không raw score, PII, outcome, audit attr, `is_dropout_outcome` |
| H06b | P1 · sau H05a | Transition API đúng Process: `New Signal` → `Pending Review` → `Approved for Follow-up` → `Assigned` → `Follow-up in Progress` → `Resolved`/`Monitoring`; `Dismissed` từ Pending; defer = giữ Pending + review_at | Contract tests transition/hành động cấm; **không** dùng `new/in_review/deferred/handed_off` — **Done:** `backend/app/cases/*` + `tests/test_case_transitions.py` (15 xanh; Quick+full verify); in-memory store; chưa full public ReviewCase (`H06a`) |
| H11a | P1 · sau H06a | Integration contract tối thiểu: allowed display fields, error/empty/stale/`insufficient_data` | Đủ cho `G05`/`T03` bắt đầu |
| H11b | P2 · sau G05+T03 | Docs agent/FE hoàn thiện | Guardrail đầy đủ khớp code đã build |
| H07 | P1 · sau H05a | Deployment/runbook: env, CORS, seed, health, smoke, rollback | Runbook không secret — **Done:** [06-deploy-runbook](../04-engineering/06-deploy-runbook.md) draft từ arch; linked docs index + arch; Live URL/smoke/rollback TBD đến deploy thật (`D4`) |
| H19 | P1 · sau H10 | Thiết kế persistence MVP versioned: mapping metadata legacy DWH → schema `dwh` mới và migration DB rỗng | [Schema persistence](../04-engineering/07-mvp-persistence-schema.md); không copy schema/row legacy, PII, raw score hay outcome vào public path; bảng điểm danh theo thời gian khi `H15` sẵn sàng; migrate lặp được trên DB rỗng |
| H20 | P1 · sau H19+M06 | Nạp transactional fixture M06 đã được duyệt vào `dwh` | Chỉ đọc artifact ngoài repo có M05b approval; hash/count/schema/PII gate fail → rollback/zero write; re-run idempotent; readiness report không PII |
| H08 | P1 · sau H20+H06a | `dwh` → `NormalizedStudentRecord`/`ScoringFeatures` read adapter | Provenance/coverage/freshness; fail closed; không chiếu outcome vào scoring/public; `advisor_ref` thiếu giữ mapping-repair; chuyên cần theo thời gian khi có snapshot `H15` |
| H18 | P1 · song song M01 | Quarantine legacy `EarlyWarning*` / synthetic attendance-week / synth group khỏi API/MVP path | Test fail nếu MVP path còn import legacy/synthetic; không raw risk public; **không** cấm chuỗi điểm danh đã duyệt qua `H15` |
| H14 | Post-CP2 | Decision/contract research forecasting/fusion từ M07 | Tách `TermEvidence`/`AttendanceForecastEvidence`; ready/`insufficient_data` |
| H02 | P1 · sau M02 | API list/detail chỉ `ReviewCase` public | Happy/missing-state; agent context public-only |
| H13 | P1 · 11:00 | Nộp Checkpoint 1 | Không claim forecast/hybrid đã ship |
| H03 | P2 · sau H08 | Care workflow API | Approve / dismiss / defer(keep Pending) / assign-handoff tests; **`advisor_ref` thiếu ⇒ dừng handoff + mapping-repair queue** (không handoff chỉ vì approved) — `H06b` Done; còn chờ `H08` |
| H04 | P2 · sau M03 | Threshold/config API public semantics | Không raw score |
| H12a | P2 · ~15:00 (trước T02/G03/G04) | Runtime privacy/care copy cho UI/agent | Copy không claim quá dữ liệu; không “Điểm rủi ro” |
| H12b | P2 · sau H12a · ~19:00 | Banner + asset copy | Forecast/fusion ghi research/blocked; **điểm danh theo thời gian = MVP** |
| D3 | P2 · ~20:30 | GitHub public, PII/secret scan | URL ẩn danh + scan evidence — **Done:** [scan notes](10-d3-github-pii-secret-scan.md); https://github.com/phanthutrang410/ABG_team public; SĐT gỡ khỏi tree |
| D4 | P2 · ~21:00 | Live URL + smoke lần 1 + rollback sẵn sàng | Health + list→case ẩn danh — `H07`+`D3` Done; còn chờ `H02`, `G02` |
| D4r | P2 · ~22:00 | Sau V07/A05 defects: owner fix → redeploy → re-smoke | Re-smoke xanh trước V05; có cửa sổ fix (≥45–60 phút) |
| H16 | P3 · sau V05 | Acceptance matrix + release evidence | Phụ thuộc **A05 + V07 + V05**; mỗi FR/CP2 item có evidence hoặc limitation |
| H09 | P3 · 09:00 | README + verify/known-limit | Khớp deploy và scope thật |
| D5 | P3 · 10:00 | AI collaboration log từ V08 | Gap có owner; sạch PII/secret |
| H15 | P1 · MVP | Attendance source approval + amendment contract | **External:** data-owner approval artifact (owner, quyền, hash, cadence, privacy review). Content: provenance, exception policy; không synthetic. Depends `H10` + approval — **không** Post-MVP |
| H17 | Post-MVP | Hybrid forecast/fusion public API theo H14 | Agent-safe fields only; T04 chỉ bắt đầu sau H17 |

**Verify:** link/traceability, contract test, docs khớp code/public DTO.

---

## 5. Khánh Duy — chi tiết task

**Lane:** Data/ML, source validation, baseline semester, nghiên cứu hybrid.
**Read first:** PRD §§4,7–8; signal catalog; Ethics §§5–6; [EPU contract](../04-engineering/04-epu-data-integration-contract.md); [Data-ML](../04-engineering/08-data-ml-scoring-fairness-contract.md); ML tests gần nhất.
**Không làm:** hoàn thiện Markdown contract/PRD; dùng synthetic hoặc attendance thiếu approval; đưa `is_dropout_outcome`/group attr vào scoring.

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| M01 | P0→P1 REOPEN | Quarantine/remove legacy ML synthetic: attendance tuần, synth socioeconomic/ethnicity, raw risk path trong `early_warning` | README + module không còn MVP consumer; test cấm feature attendance-week/synth group trong scoring |
| M04 | Recovery · ASAP 03:30 | Handoff Data/ML: semester + attendance-over-time baseline, source/quality gate, threshold/FPR, giới hạn forecast/fusion | **Done:** [10-m04…](10-m04-data-ml-handoff.md); **không** đồng nghĩa dữ liệu đã được duyệt |
| H06c | P1 · sau H10 | `FairnessReport` schema + fail-closed fixture | Metric chỉ khi group + GT + N hợp lệ |
| M05a | P1 · sau H10 | **Build** source gate: register, hash/count, PII exclusion, fail-closed khi thiếu approval | Code/tests gate; H10 Done ≠ source approved |
| M05b | P1 · sau M05a | **Approved source available** | Artifact duyệt của data owner (owner, quyền, snapshot hash, record count); thiếu → giữ `insufficient_data`, không bịa fixture “đã duyệt” |
| M06 | P1 · sau M05b | Fixture: bảng domain điểm (+ `attendance_event` khi `H15` sẵn sàng) + `source_manifest` + `data_quality_report` | Deterministic, pseudonymous; không cross-join/PII/token; outcome chỉ trong evaluation |
| M02 | P1 · baseline | Baseline ML: trend/volatility điểm + chuyên cần theo thời gian (khi có) + factors + coverage | Dùng chuỗi điểm danh đã duyệt; cấm synthetic/legacy week; không dùng `is_dropout_outcome` trong score |
| M07 | Sau M02+H02+H13 · ngoài CP2 | Nghiên cứu forecast/fusion research-only | Handoff cho H14; không thay thế CORE-03 MVP; **không** cùng deadline với M02 |
| M03 | P2 | Fairness gate FPR/ΔFPR/N hoặc `insufficient_data` | Formula/denominator/group-separation; outcome chỉ evaluation |
| M08 | Post-MVP | Attendance forecasting + gated fusion | Depends **H15 + M02 + H14**; determinism, no-leakage, fusion-gating; output internal priority only |

### M07 — yêu cầu handoff hybrid

Chỉ chạy sau khi MVP slice `M02`/`H02`/`H13` xong. So sánh semester feature vs forecast attendance: data readiness, window, timestamp order, horizon, label cutoff/no leakage, missingness, nghỉ có phép, gated/late fusion. Chỉ đề xuất:

- `TermEvidence` và `AttendanceForecastEvidence` tách riêng; coverage, freshness, provenance, `model_version`, `calculated_at`, ready/`insufficient_data`.
- Fusion chỉ khi cả hai branch qua gate; absence không zero-impute, không đổi priority.
- Public/agent chỉ `review_priority_band`, factors/evidence, limitations.

**Verify:** determinism, missing/stale, formula/denominator, PII/source gate.

---

## 6. Giang — chi tiết task

**Lane:** Frontend integration và UI.
**Read first:** PRD §5; Ethics; H11a (không chờ H11b).
**Không làm:** tự chốt copy/contract; raw score; “Điểm rủi ro”; synthetic/legacy attendance mock sau G05.

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| G01 | P0 | FE shell + list mock tạm | Smoke — **Done** (mock phải bị G05 thay) |
| G05 | P1 · sau H11a | Thay hẳn `MOCK_RISK_LIST`/raw risk/synthetic attendance bằng public DTO + fixture đã validate | Routes/types: loading/error/`insufficient_data`; không còn “Điểm rủi ro” / synthetic demo copy; chuyên cần theo thời gian theo public DTO khi có |
| G02 | P1 · sau H02 | Dashboard → cohort → case dùng API | Lint/build/smoke |
| G03 | P2 · sau H12a | Care UI theo Process states + defer = giữ Pending | Chỉ action được phép; lint/build/smoke |
| G04 | P2 · sau H12a | Fairness/privacy/threshold panel | Metric hợp lệ hoặc `insufficient_data` |

**Verify:** lint, production build, behavior smoke. Chỉ public DTO.

---

## 7. Thu Trang — chi tiết task

**Lane:** Agent adapter, grounding/refusal tests.
**Read first:** PRD §5.4/FR-08; Ethics §8; H11a / H12a.
**Không làm:** tự tính/sửa mức ưu tiên; score/dropout conclusion.

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| T03 | P1 · sau H11a | Agent interface, fixture, refusal/adversarial | ≥5 case grounded/refusal; read-only; không live call bắt buộc |
| T01 | P1 · sau T03 | Agent stub từ fixture | Không bịa score/cause; mocked tests pass |
| T02 | P2 · sau H12a (~16:30+, không cùng 18:00 với H12a) | Grounded explanation từ API/ML | Adversarial pass; chỉ band/factors/limits |
| T04 | Post-MVP | Agent adapter hybrid | **Chỉ sau H17** (API đã cấp quyền); không raw attendance/score |

**Verify:** grounding/refusal/adversarial mocked tests.

---

## 8. giang — chi tiết task

**Bắt đầu từ P2.** Story: [08-stories-giang.md](08-stories-giang.md).

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| A05 | P2 · ~21:30 (song song V07; defects → D4r) | UAT/claim-copy review | Checklist pass/fail/gap; không sửa docs/code |
| D1 | P3 · 09:00 | Asset slide + mô tả | Dựa `H12b` + evidence; URL thật; không PII |

**A05:** list→case→review/handoff trên Live URL; rà care/privacy/fairness/claim; gửi Hoàng + feed `D4r`.

**D1:** chỉ copy/screenshot từ `H12b`/`H16` và Live URL đã `D4r`; điểm danh theo thời gian = MVP; forecast/fusion chỉ Post-MVP/research nếu chưa Done.

---

## 9. Văn Hải — chi tiết task

**Bắt đầu từ P2.** Story: [09-stories-van-hai.md](09-stories-van-hai.md). Evidence: [07-release-evidence.md](07-release-evidence.md).

| ID | Gate · deadline | Outcome | DoD / evidence |
|:--|:--|:--|:--|
| V07 | P2 · ~21:20 | QA release + smoke độc lập lần 1 | Incognito; ghi defect cho owner/`D4r`; không tự sửa |
| V05 | P2 · ~22:45 | Nộp Checkpoint 2 | **Chỉ sau `D4r` xanh**; BTC nhận 2 URL + xác nhận |
| V02 | P3 · 08:00 | Script 4′ + Q&A 2′, rehearsal | Copy `H12a`; Live sau `D4r` |
| D2 | P3 · 09:30 | Video ≤5 phút | Đúng Live URL sau `D4r` |
| V08 | P3 · 09:45 | Rà AI log | Depends `H05b` — **unblocked**; gap cho Hoàng/`D5` |
| V06 | P3 · 10:30 | Nộp cuối | Sau evidence `H16` đã khóa CP2+final |

---

## 10. Quy ước, rủi ro và việc làm ngay

| Quy ước / risk | Cách xử lý |
|:--|:--|
| P0.5 trễ / H10 trễ | Chạy recovery §1.1; không giữ deadline cũ trên board |
| Docs choke-point Hoàng | Split `H05a/b`, `H11a/b`, `H12a/b`; Hoàng vẫn owner duy nhất |
| Source gate ≠ approved data | `M05a` build gate; `M05b` chờ artifact duyệt; M06 chỉ sau M05b |
| DB cần sẵn sàng nhưng nguồn chưa duyệt | `H19` chỉ tạo schema/migration DB rỗng; `H20` chỉ nạp fixture M06 có M05b, không dùng DB/reference/synthetic cũ |
| Attendance chưa duyệt | `H15` là task **MVP** (approval artifact); nhánh chuyên cần trả `insufficient_data` — không đẩy Post-MVP |
| Agent “dropout risk” | Từ chối; chỉ band/factors/limits từ API |
| QA phát hiện lỗi | V07/A05 → owner fix → `D4r` → mới V05 |
| Blocked >2 giờ | Ghi ID blocker; không tự đổi schema/fixture/scope |
| Legacy synthetic còn trên UI/ML | `M01` REOPEN + `H18` + `G05` thay mock |

1. **Ngay:** `H10`/`M04` Done — mở `H06a` / `H19` / `M05a` / `H12a` / `H13` / `H06c`; Duy `M01` reopen; `H15` chờ data-owner; `H03` còn chờ `H08`.
2. Không coi dữ liệu đã duyệt cho đến `M05b`; chỉ nạp qua `H20` sau `M06`.
3. `H12a` xong trước `T02`/`G03`/`G04` (copy keys đã khóa trong Data-ML §6); `H12b` sau cho asset.
4. `M07` chỉ sau `M02`+`H02`+`H13`; không tranh slot với baseline.
5. Trước handoff: verify phù hợp; trước final: `scripts/verify.ps1`, `git diff --check`, `git status --short`.
