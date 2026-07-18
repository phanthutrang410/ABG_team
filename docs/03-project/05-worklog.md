# Nhật ký công việc

## 2026-07-18 (M06 Done — domain transform + quality report)

- `M06` **Done** (Duy): `backend/app/ml/domain/` — `models.py` (Pydantic domain rows + `DataQualityReport`, tên khớp cột `dwh`), `transform.py` (semester: term_code normalize, taxonomy `Trạng thái` decision #17, miền điểm `[0,10]`, khóa unique, reject reasons, coverage `single_term`/`grade_coverage_insufficient`/`status_unknown`), `attendance.py` (nhánh `mvp-attendance-over-time`; rate loại `excused=true`; ≥4 mốc; trend ≥2 điểm). `DataQualityReport` được lắp trong transform/attendance (không tách file riêng).
- Fail-closed: field PII/token trong input ⇒ `PiiFieldError` (zero output). Không cross-join hai nguồn. `is_dropout_outcome` chỉ ở `academic_status` (evaluation) — test chứng minh không rò sang `student_dimension`/`term_grade`/`advisor_assignment`.
- Committed attendance artifacts (pseudonymous, no PII): `tests/fixtures/attendance/mvp_attendance_source_manifest.json` + `…_data_quality_report.json` — regen-deterministic (test so khớp build).
- Semester domain artifact **không commit**: sinh tại vị trí ngoài repo từ file M05b external (`v59-empty-program-students`) — `H20` đọc; repo chỉ giữ transform + tests (EPU §5). Không commit raw V59/PII/map MSSV.
- Tests: `tests/test_m06_domain_fixture.py` (46) — normalize, taxonomy, reject layers, PII fail-closed, determinism, no cross-join, alignment field ↔ cột `dwh`, attendance rate/excused/coverage, artifact no-drift.
- Verify: `ruff check app tests` pass; `pytest -q -m "not slow and not eval"` → **197 passed, 4 errors**. 4 errors = `test_dwh_migrate.py` (H19) yêu cầu Postgres (`docker compose up -d db`) — **không** liên quan M06 (transform thuần, không chạm DB); môi trường local không có Docker. FE không đổi (không chạy). Chưa commit trong bước này → commit/push branch `KhanhDuyBui` theo yêu cầu.
- Mở khóa `H20` (Hoàng) — consume `app/ml/domain` output. `M02` vẫn `BLOCKED → H08` (H20→H08).

## 2026-07-18 (~07:05 M05b + H15 unlock — decision #18)

- **Decision #18:** team approver (Hoàng) unlock MVP demo — semester V59 ngoài git + attendance allowlisted `mvp-attendance-over-time`.
- `M05a`/`H06c` board sync **Done** (PR #17). `M05b` **Done** — [14-m05b…](14-m05b-semester-approval.md) (hash `34a53298…`, 460 rows).
- `H15` **Done** — [12-h15…](12-h15-attendance-approval-prep.md) + fixture `backend/tests/fixtures/attendance/mvp_attendance_over_time.json`; amend EPU/Data-ML/persistence; RULES pointer.
- Gate: allowlist `mvp-attendance-over-time` role `attendance`; `tests/test_source_gate.py` **26** xanh.
- **M06 mở** cho Duy. Không làm H20/H08 trong wave này. Public copy trung lập (không slogan synthetic / không claim institutional approval).

## 2026-07-18 (~06:35 Option 1: M01 Done + H18)

- Chốt **Option 1** multitask Hoàng (không spawn lane Duy/Giang/Trang).
- `M01` **Done** (PR #16 `1046ffe`): board sync; dọn leftover `backend/app/ml/early_warning/` (`__pycache__`) — 4/4 `test_m01_legacy_quarantine` xanh.
- `H18` **Done**: `backend/tests/test_h18_api_mvp_quarantine.py` (6) — API/MVP packages không legacy; OpenAPI/ReviewCase không raw risk; health/cases surface không cần early_warning.
- `H02` còn `BLOCKED → M02` (H18/H06a-r Done).
- `H13` vẫn TODO — human BTC submit + receipt trước 11:00; draft paste-ready giữ nguyên.
- Chase `M05b`/`H15` refresh — vẫn BLOCKED → data-owner / M05a; **không** fake approval.

## 2026-07-18 (~05:56 chase M05b/H15)

- Chase refresh only: [12-h15…](12-h15-attendance-approval-prep.md) §0 — status bảng M05a/M05b/H15 + next asks copy/paste cho Duy và data-owner; checklist §1 vẫn **OPEN** cả 5 hàng.
- Sprint giữ nguyên: `M05a` TODO; `M05b` `BLOCKED → M05a + approval`; `H15` `BLOCKED → data-owner`. **Không** tick Done; **không** fake approval; **không** amend EPU/Data-ML.

## 2026-07-18 (~H06a verify + H11a Done)

- `H06a` xác nhận lại: Coverage/ScoringFeatures/ReviewCase — **35** contract tests xanh (không đổi scope).
- `H11a` Done: [10 FE/Agent integration](../04-engineering/10-fe-agent-integration-contract.md); `backend/app/contracts/integration.py` (`CaseListResponse` / `CaseDetailResponse` / `AgentContextResponse` + allowlist/forbidden); fixtures `tests/fixtures/integration/*`; **18** tests. Mở `G05`/`T03`. Không implement H02 routes / agent runtime.
- Verify: `.\scripts\verify.ps1` — ruff pass; pytest **92 passed**; FE lint/build OK; FE test placeholder skip (warned).

## 2026-07-18 (~merge handoff multitask H10–H15)

- Gom board sau Wave 1: `H06a` Done (Pydantic Coverage/ScoringFeatures/ReviewCase + 35 tests); `H19` Done (Alembic 7 bảng `dwh` + 4 migrate tests); `H12a` Done (4 copy keys + bỏ “Điểm rủi ro”).
- `H10` giữ Done (baseline). `H13` vẫn TODO — draft [11-h13…](11-h13-cp1-btc-draft.md) paste-ready; form + receipt human. `H15` vẫn `BLOCKED → data-owner` — prep [12-h15…](12-h15-attendance-approval-prep.md) only.
- Mở khóa: `H11a`/`H12b` TODO; `H20` còn `BLOCKED → M06`; giảm blocker trên `H02`/`H08`/`M02`/`T01`/`G03`/`G04`/`T02` (H06a/H12a/H19 Done).
- Verify: `git diff --check` OK; `.\scripts\verify.ps1` — ruff pass; pytest **74 passed**; FE lint pass; FE test placeholder skip (warned); `next build` OK. Không commit.

## 2026-07-18 (~04:25 H13 CP1 draft)

- `H13` nội dung CP1 paste-ready: [11-h13-cp1-btc-draft.md](11-h13-cp1-btc-draft.md); checklist [07-release-evidence.md](07-release-evidence.md) §1 — hàng nội dung `[x]`; form + receipt còn `[ ]` / BLOCKED → human BTC submit trước 11:00.
- Sprint `H13` giữ TODO (chưa Done): chưa có form submit/receipt.
- Hard rules giữ: không hybrid/forecast ship; không “Điểm rủi ro”; thiếu chuyên cần → `insufficient_data` (MVP); không “xu hướng dài hạn”.

## 2026-07-18 (~H15 prep only — still BLOCKED)

- Wave 2 prep: [12-h15-attendance-approval-prep.md](12-h15-attendance-approval-prep.md) — chase checklist (owner/rights/hash/cadence/privacy) + amendment outline (§2.2 window/`excused`/unique key). **Không** tick Done; Sprint giữ `BLOCKED → data-owner`.
- Consumers tiếp tục fail-closed `attendance_source_unapproved`; không synthetic attendance fixture; không amend EPU/Data-ML như đã duyệt.

## 2026-07-18 (~04:15 H10 Done)

- `M04` artifact đã có ([handoff](10-m04-data-ml-handoff.md)); `H10` khóa contract: [EPU](../04-engineering/04-epu-data-integration-contract.md), [Data-ML](../04-engineering/08-data-ml-scoring-fairness-contract.md), decision #17.
- Taxonomy: `Rút học phí`/`Bảo lưu` → `unknown`; pseudonym ngoài repo; attendance default cửa sổ/mốc + `attendance_source_unapproved` tới H15; copy keys cho H12a.
- Supersede synthetic contract → `09-synthetic-…`; P0.5 **Done**; mở `H06a`/`H19`/`M05a`/`H12a`/`H13`/`H06c`. H10 Done ≠ nguồn đã duyệt (`M05b`).

## 2026-07-18 (~04:00 D3 Done)

- `D3` Done: repo đã `visibility=public` (`https://github.com/phanthutrang410/ABG_team`); anonymous API/HTML 200.
- Scan tracked tree (`scripts/d3_pii_secret_scan.py` + gitleaks): không secret trong tree; 24 SĐT trong `02-team.md` / `Khao_sat_ABG_tong_hop.md` → redact cột Liên hệ `—`.
- Evidence: [10-d3-github-pii-secret-scan.md](10-d3-github-pii-secret-scan.md); private JSON dưới `.ai-log-private/` (gitignored). `.gitleaks.toml` allowlist false positive + ignored paths.
- Residual: SĐT vẫn có trong git history cũ (không rewrite). `D4`/`V07` còn chờ `H02`/`G02`/`D4`.

## 2026-07-18 (scope: điểm danh theo thời gian = MVP)

- Sửa decision #9/#13, RULES, PRD, problem, signal catalog (`CORE-03`), traceability, sprint, stories, architecture, EPU contract/catalog/persistence: **điểm danh theo thời gian thuộc MVP**, không Post-MVP.
- `H15` chuyển về P1/MVP (source approval). Forecast/gated fusion (`M07`/`M08`/`H14`/`H17`/`T04`) vẫn research/Post-MVP ngoài CP2.
- Thiếu nguồn điểm danh → `insufficient_data`; cấm tạo chuỗi giả.

## 2026-07-18 (persistence DB readiness)

- Theo yêu cầu chuẩn bị database cho các task sau, thêm `H19` (schema/migration DB rỗng) và `H20` (import fixture approved) trước `H08`. DB cũ chỉ được inventory metadata/pattern; không copy schema/row/raw export.
- Chưa có M04, M05b hay artifact data-owner approval trong workspace: không nạp V59, `epu_data` hay synthetic. `H20` phải rollback nếu thiếu approval/hash/count/schema/PII gate.

## 2026-07-18 (~03:20 re-verify H06b / H07 / H05b)

- Re-audit DoD: transition API + templates + runbook đã đủ; chỉ sửa nit `.ai-log/README.md` example path `03-system-architecture` → `05-system-architecture`.
- Checks: `ruff check app tests` pass; `pytest -q tests/test_case_transitions.py` → 15 passed; `.\scripts\verify.ps1 -Quick` (xem kết quả cùng handoff).
- Verdict giữ Done cho cả ba; chưa commit (theo yêu cầu).

## 2026-07-18 (~02:40 board merge — H06b / H07 / H05b)

- `H06b` Done: Process §4 transitions + forbidden actions + `advisor_ref` gate dưới `/cases`; `backend/app/cases/*`, `main.py`, `tests/test_case_transitions.py` (15 xanh; Quick+full verify). Gap: in-memory store; chưa full public ReviewCase (`H06a`). `H03` còn `BLOCKED → H08`.
- `H07` Done: [deploy runbook](../04-engineering/06-deploy-runbook.md) draft từ arch, không secret; linked docs index + arch; finalize Live/smoke/rollback tại `D4`. `D4` còn `BLOCKED → H02, G02, D3`.
- `H05b` Done: `.ai-log/templates/*` + release-evidence template; pointer README/`07-release-evidence` only. Mở `V08`.

## 2026-07-18 (~H05a Done)

- `H05a` Done: [kiến trúc tối thiểu](../04-engineering/05-system-architecture.md); Process §4 khóa ma trận transition + mã API + `defer`/`advisor_ref` gate; PRD FR-06/07 + product statement; banner Target vs MVP trên BRD/scope; decision #15; index docs.
- Mở khóa `H06b`, `H07`, `H05b`. `H10`/`H13`/`H12a` vẫn chờ `M04` (và H10). P0.5 còn một chân `M04`.

## 2026-07-18 (~02:10 board recovery)

- P0.5 **chưa qua** (H05/M04 vẫn TODO lúc ~02:03): cập nhật [Sprint](03-sprint.md) recovery plan; tách choke-point docs `H05a/b`, `H11a/b`, `H12a/b`; thêm `D4r` (QA→fix→re-smoke); `H16` phụ thuộc thêm `V05`.
- Đồng bộ Process state machine cho `H06b`/`H03`; `H03` phụ thuộc `H08` + test thiếu `advisor_ref`; tách `M05a/b`; M06 = domain + manifests; reopen `M01` + `H18` + `G05` thay mock; `M07` sau `M02/H02/H13`; `M08`←`M02+H14+H15`, `T04`←`H17`.
- Cập nhật stories giang/Văn Hải, [release evidence](07-release-evidence.md), [EPU contract](../04-engineering/04-epu-data-integration-contract.md).

## 2026-07-18 (điều chỉnh ownership + hybrid research)

- Theo phân công mới, [Sprint](03-sprint.md) giao mọi tài liệu/contract/evidence Markdown cho **Hoàng**; code/build chỉ thuộc Hoàng, Khánh Duy, Giang và Thu Trang. **giang** và **Văn Hải** bắt đầu task từ P2: UAT/QA/review, slide–mô tả asset, rehearsal/video và submission.
- Thêm M07 để Duy nghiên cứu forecasting điểm danh + gated fusion. Research-only cho forecast/fusion: không tự tạo weekly attendance giả. **Sửa sau:** `H15` (source approval điểm danh) thuộc MVP; chỉ `M08`/`H17`/`T04` (và `H14` research contract) là Post-MVP/forecast ngoài CP2.
- Agent chỉ giải thích priority/evidence/limits do model/API trả về; không tạo hoặc khẳng định dropout risk cho sinh viên.

## 2026-07-18 (tái cấu trúc task)

- Chuẩn hóa [Sprint](03-sprint.md) thành một board định nghĩa task duy nhất: mỗi ID có **một owner**, outcome/artifact, DoD, verify/evidence và `Depends (phải Done)`.
- Bỏ vai trò nghiệm thu riêng khỏi task/story/release checklist. Task bị thiếu đầu vào phải ghi `BLOCKED → <task ID>`; không còn slot chưa đặc tả hoặc polish ad-hoc không ID.
- Đồng bộ [RULES.md](../../RULES.md), [AGENTS.md](../../AGENTS.md), stories giang/Văn Hải và [release evidence](07-release-evidence.md) theo quy ước này.

## 2026-07-18 (data reset EPU)

- Theo catalog EPU, loại pipeline synthetic cũ: không tạo chuỗi tuần/chuyên cần, nhãn outcome, thuộc tính fairness hoặc mapping GVCN giả để lấp field thiếu.
- Thêm [hợp đồng tích hợp EPU](../04-engineering/04-epu-data-integration-contract.md) và task M05 (source gate), M06 (extract/pseudonymize/normalize), H08 (DTO/fixture cho Hoàng). V59 và `epu_data` vẫn là candidate đến khi data owner xác nhận provenance/quyền sử dụng.
- Snapshot đã kiểm tra: V59 và `epu_data` không có `MSSV` giao nhau; M06 không được cross-join hai nguồn. Fairness thiếu nhóm audit hợp lệ phải trả `insufficient_data`.

## 2026-07-18 (đêm ~00:30)

- Bổ sung story non-tech cho **giang** và **Văn Hải**: [08-stories-giang.md](08-stories-giang.md), [09-stories-van-hai.md](09-stories-van-hai.md); mở rộng mô tả lane A/V trong [03-sprint.md](03-sprint.md) (P0.5→P3) bằng ngôn ngữ nghiệp vụ + link checklist

## 2026-07-17 (tối ~22:30)

- Nâng [03-sprint.md](03-sprint.md) theo format SprintPlanning tham khảo: 4 gate + **P0.5 Architecture Lock**; task docs/thiết kế đầy đủ cho 6 người. Cơ chế phân công và các slot chưa đặc tả của bản ghi này đã được thay bằng board one-owner có dependency/evidence ở mục 2026-07-18 bên trên.
- Lane 48h: Giang = FE, Thu Trang = agent; threshold/FP thuộc Khánh Duy
- Đồng hồ gắn Checkpoint 1 (11:00 18/7), Checkpoint 2 (23:00 18/7), đóng cổng (11:00 19/7)

## 2026-07-17 (chiều)

- P0 done: H01 backend `/health` + schemas `dwh`/`ml`, M01 synthetic CSV (40 hồ sơ), G01 Next.js dashboard mock
- Đối chiếu [Problems Brief](../01-requirements/02-problems-brief.md): chốt Ban Lãnh đạo là primary user, viết lại PRD/ethics, tách danh mục tín hiệu và ghi [các độ lệch còn mở](../01-requirements/03-traceability.md)
- Docker Postgres `vaic2026-db-1` up; `.env` created (cần điền `FPT_API_KEY`)
- Chưa xong: AWS creds invalid, `GITHUB_TOKEN` user env, LangSmith khi T02

## 2026-07-17

- Chọn đề Silent Shield (~75% transfer từ EduInsight) — [Quyết định chọn đề](01-topic-selection.md)
- Bootstrap skeleton tối giản + chuyển MD gốc vào `docs/`
- Phân lane H/M/G/T/A/V/D — [Đội ngũ và phân vai](02-team.md)
