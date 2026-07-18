# Nhật ký công việc

## 2026-07-18 (Wave H28a–D6 backend Done — weekly + OpenAI + Global Agent)

- Slice 0–5 backend landed: Decision #23; OpenAI runtime (`H29`); snapshot ledger + CLI (`H30`/`H31`); Mode B observations + durable cases + delta + report/briefing (`H32`–`H34b`); RBAC (`H36`); advisor draft v2 (`H35`); `POST /agent/turns` (`H37`); safe export (`H38`); ops kill-switch/`scheduler_tick` (`D6` foundation).
- Checks: backend `pytest -m "not slow and not eval"` → **548 passed, 1 skipped**; Ruff clean.
- **Gaps:** Case store still in-memory (not Alembic); linked namespace combined feed still pending approval; EventBridge live wiring manual; FE `G07–G09` + `T05` chưa ship — không overclaim trên Live URL nộp bài.
- Unlock: Giang `G07` (sau H36); `G08`/`G09` sau G07; Thu Trang `T05` sau G07.

## 2026-07-18 (H29 Done — OpenAI Responses provider)

- `H29` **Done**: `app/agent/model.py` + `openai_client.py`; `get_text_model` chỉ OpenAI / missing-key stand-in; FPT không còn active path; `store=false`; `tests/test_h29_openai_transport.py` + agent regression 100 passed / 1 skipped.
- Env: `OPENAI_API_KEY` / `OPENAI_MODEL` / `OPENAI_BASE_URL` trong `.env.example`.

## 2026-07-18 (H28a Done — readiness/decision lock weekly wave)

- `H28a` **Done**: Decision #23 khóa significant-change/resurfaced, Mode B linked-namespace (`approval:pending-linked-namespace`), identity/RBAC/90d retention, EventBridge→SQS→worker, OpenAI model pin/`store=false`, email draft-only (#20).
- Artifacts: [04-decisions.md](04-decisions.md) #23; architecture §16; deploy runbook §12; Sprint unlock `H30`/`H32`(Mode B)/`H33b`/`H36`.
- Không schema migration / provider code trong H28a. Critical path `V07+A05→D4r` không bị block bởi wave này.

## 2026-07-18 (Phân công: V05 → Thu Trang; V07 checklist rõ cho Hải)

- `V05` (nộp Checkpoint 2) **chuyển owner** Văn Hải → **Thu Trang**; story [16-stories-thu-trang.md](16-stories-thu-trang.md).
- `V07` viết lại thành checklist từng bước + **output template** bắt buộc trong [09-stories-van-hai.md](09-stories-van-hai.md); Hải không nộp CP2.
- Đồng bộ [Sprint](03-sprint.md) board/lane + [07-release-evidence §2](07-release-evidence.md).

## 2026-07-18 (H11b + H22 Done — docs agent/FE + advisor handoff draft API)

- `H11b` **Done**: sync arch §6 (bounded DAG HTTP), [guardrails](../04-engineering/08-agent-grounding-guardrails.md) canonical, [doc 10](../04-engineering/10-fe-agent-integration-contract.md) after-build matrix; claim FR-08 = backend HTTP only; no FE Agent UI overclaim.
- `H22` **Done**: `GET /advisor-handoff-drafts` · `AdvisorHandoffDraftBundle` · mapping_repair bucket · draft-only · `tests/test_h22_advisor_handoff_draft_api.py` (8); unlock `G06`.
- Board: `H11b`/`H22` Done; `G06` TODO unblocked; `D4r` vẫn chờ V07+A05.

## 2026-07-18 (D4b Done — Live product smoke list→case)

- `D4b` **Done**: redeploy Live `:d4b` (API + FE), gắn Postgres, import approved semester (460 SV) + attendance (15 events), smoke list→case ẩn danh.
- Evidence: health `database:true`; `GET /review-cases` state=`ok` n=50; detail `rc-s-00518c9485a9` / band=`can_ra_soat`; FE `/login` `/dashboard` 200; forbidden-field scan sạch; [07-release-evidence §2](07-release-evidence.md).
- Board sync: `G05`/`G02`/`G03`/`G04` **Done** (PR #23 + AI-log); `H11b`/`V07`/`A05` **unblocked**; `D4r` còn chờ V07+A05.
- Fixture gate: chuẩn hóa LF + hash approval `73274079…` / `78d7153f…` (CRLF working-tree hash cũ lệch GitHub tarball). Dockerfile/.dockerignore: giữ `alembic` trong image cho H20 migrate.

## 2026-07-18 (Board sync lane M — G05/G02/G03/G04 Done, D4b/H11b unblocked; superseded bởi board sync D4b/H11b của Hoàng ở trên)

- Đồng bộ [Sprint](03-sprint.md) với thực tế sau merge `d579909`: lane Giang `G05`/`G02`/`G03`/`G04` **Done** — evidence từ `.ai-log/manifest.csv` (sessions `20260718-G05-…-12`, `…-13`, `…-15`, `…-16`) và code đã merge (`frontend/src/lib/{types,fixtures,api,session,limitations}`, `CareActions`/`FairnessPanel`/`ThresholdPanel`/`AppShell`, các trang login/select-role/dashboard/my-class/cases; `mock-review-list.ts` đã xóa).
- Dây chuyền mở khóa ghi nhận tại thời điểm đó: `D4b`/`H11b` unblocked; `A05` chỉ còn BLOCKED → D4b; `V02` chỉ còn BLOCKED → D4r — sau đó Hoàng đã hoàn tất D4b/H11b/H22 (xem entry trên).
- Gap ghi nhận từ G02 (cần Hoàng chốt, không tự sửa contract): `ReviewCase` public thiếu `cohort`/`department`/`class_code` → FE chưa làm được scoping khoa/lớp; row risk giữ trong Sprint §10.
- Checks: docs-only — `git diff --check` + `.\scripts\verify.ps1 -Quick` pass.

## 2026-07-18 (H23–H26 Done — Agent runtime FR-08 backend HTTP)

- `H23`–`H26` **Done**: server-derived `AgentContext` → `POST /review-cases/{case_id}/explanation` → structured grounding + hardened FPT client → mocked HTTP E2E.
- Evidence: `backend/tests/test_h23_agent_context.py`, `test_h24_agent_api.py`, `test_h25_grounding.py`, `test_h25_fpt_transport.py`, `test_h26_agent_e2e.py`; release [07-release-evidence §5c](07-release-evidence.md).
- Checks: targeted H23–H26 + `tests/agent/` → **130 passed, 1 skipped** (live FPT SKIP — no approved key); `.\scripts\verify.ps1` → **410 passed, 1 skipped**; Ruff clean; `git diff --check` clean.
- **Claim:** FR-08 E2E ở mức **backend HTTP** (FakeModel structured plan). **Không** claim FE Agent UI, production RBAC, hay live FPT. `H11b` **Done** — docs sync sau G05–G04 + H26.

## 2026-07-18 (Agent runtime gap plan — H23–H26)

- Audit sau merge xác nhận `T02` **Done ở mức core/library**: chưa có server context service, agent HTTP route, production FPT wiring hoặc HTTP E2E; không dùng T02 riêng để claim FR-08 end-to-end.
- Chốt decision #21 và [implementation brief](../04-engineering/12-agent-runtime-integration-plan.md): Hoàng làm `H23` contract/context → `H24` HTTP runtime → `H25` structured grounding/provider hardening → `H26` E2E/release gate. `H22` mail-draft vẫn là FR-12 stretch riêng, không phải Agent send tool.
- Gap an toàn cần sửa: raw reviewer question hiện vẫn nằm trong payload T02 nên có thể mang PII/prompt injection; H25 phải bỏ raw question khỏi provider và validate output theo context. Chưa sửa runtime, chưa live FPT call và chưa claim Done cho H23–H26.

## 2026-07-18 (T02 Done — grounded explanation qua FPT adapter)

- `T02` **Done core/library**: `backend/app/agent/fpt_client.py` gọi FPT Chat Completions tương thích OpenAI; `grounded.py` tái dùng pre-LLM guardrail và context fail-closed của T01. Payload không chủ động gửi `student_ref`, score hay audit attrs, nhưng vẫn chứa raw reviewer question chưa qua DLP; runtime/PII hardening được theo dõi ở H23–H26.
- LLM chỉ được sinh `answer_vi`/`draft_body_vi`; facts, factor codes, limitations, model version và cờ human approval luôn dựng xác định từ H11a context. JSON sai shape, draft rỗng, outage hoặc copy chứa score/%/chẩn đoán/nguyên nhân nhạy cảm đều trả `unavailable`, không fallback bịa.
- Evidence: `backend/tests/agent/test_t02_grounded.py`; agent suite **59 passed**, Ruff sạch. Quick verify xanh; full verify **338 passed, 1 skipped**, frontend lint/build xanh. Skip trong suite: external raw V59 không được cấu hình. Live FPT eval không chạy vì `FPT_API_KEY` chưa cấu hình; frontend `npm test` vẫn là placeholder theo repo gate.
- Môi trường local: `backend/.venv` đã có backend dev dependencies; PostgreSQL test container dùng cổng `55432` vì máy có PostgreSQL khác trên `5432`. Cache legacy `early_warning` chỉ gồm `.pyc` đã chuyển có thể khôi phục sang `C:\tmp\abg-team-generated-cache\early_warning` để quarantine tests phản ánh đúng source Git.

## 2026-07-18 (~09:30 H13 Done + V08 defer + advisor mail FR-12)

- `H13` **Done** — CP1 form BTC đã nộp; evidence [07-release-evidence](07-release-evidence.md) §1 `[x]`; draft [11-h13…](11-h13-cp1-btc-draft.md).
- `V08` **defer** (decision #19): Hải không backfill AI log ngay; thu thập **một thể** gần CP2 / trước `D5`.
- Advisor-batch mail draft: research [11-advisor-batch-mail-draft](../04-engineering/11-advisor-batch-mail-draft.md) + decision #20 + PRD **FR-12** + Process bước 9–11. Tasks: `H21` **Done** → `H22` API (Hoàng, stretch) → `G06` FE (Giang). Option A = in-app aggregate + Copy/`mailto:`; **cấm** SMTP. **Không** block `G02`→`D4b`/CP2.
- Owner ngay: Hoàng `H22` nếu còn slot; Giang `G05`/`G02`; Trang `T02`.

## 2026-07-18 (H02 + H04 Done — review/threshold APIs)

- `H02` **Done**: `GET /review-cases` + `GET /review-cases/{case_id}` — `review_projection.py` / `review_router.py`; H11a envelopes; no `model_score`/PII; tests `test_h02_review_case_api.py`.
- `H04` **Done**: `GET /config/thresholds` (+ impact) + `GET /fairness/report` — `threshold_public.py` + `config_api/router.py`; fairness MVP fail-closed; tests `test_h04_threshold_fairness_api.py`.
- Verify targeted: H02/H04/H18/H20/source_gate/m06 → **99 passed**. Mở khóa consumer `G02`/`G04` (sau G05/H12a) và `D4b` (sau G02).

## 2026-07-18 (git-ready approved domain data)

- Commit package M06 semester pseudonymous: `data/approved/semester/domain_package.json` (460 SV / 3680 grades); attendance moved to `data/approved/attendance/`.
- H20 default import không cần env; regen raw qua `scripts/export_approved_semester_domain.py`. Raw V59 vẫn ngoài git.
- Docs: `data/README.md`, M05b, EPU §5, persistence §4, `.env.example`.

## 2026-07-18 (T01 Done — agent stub, lane Thu Trang)

- `T01` **Done**: stub deterministic `backend/app/agent/stub.py` — không LLM, lắp theo 3 tầng: (1) guardrail classifier `guardrails.py` (7 refusal codes, rule-based, first-match-wins — T02 tái dùng làm pre-LLM gate); (2) fail-closed mapping `context.status` (unavailable/empty/refused/insufficient → không bịa); (3) grounded assembly chỉ từ case fields (factor codes nguyên văn, coverage counts, H12a copy keys cho limitations).
- Tests: `tests/agent/test_agent_stub.py` — **12/12 ca adversarial pass** + determinism + grounding-only-case-codes + quét `assert_no_forbidden_keys` trên output thật (không chỉ fixture). Tổng agent suite **42 xanh**; contract suite chung **118 passed**; ruff pass.
- Mở khóa: `T02` chỉ còn chờ `H02` (T01 + H12a Done).

## 2026-07-18 (T03 Done — agent contract, lane Thu Trang)

- `T03` **Done**: output contract `backend/app/agent/schemas.py` (`AgentExplanationRequest` bọc `AgentContextResponse` H11a — không widen; `AgentExplanation` với invariants: refused⇒reason, draft chỉ khi ok + luôn `requires_human_approval`, ok⇒`model_version`, unavailable⇒không facts/draft).
- 6 fixtures `backend/tests/fixtures/agent/` (ok / insufficient_data / refusal / draft / unavailable + adversarial); **12 ca adversarial** phủ đủ 7 refusal codes + 3 outcome không-refusal (chống over-refusal); input contexts **tham chiếu** fixtures H11a `tests/fixtures/integration/agent_context_*.json`, không nhân bản shape.
- Privacy: mọi fixture quét đệ quy `assert_no_forbidden_keys` (H11a §2.1); chỉ `student_ref` pseudonym; không score/%/PII trong copy.
- Verify: pytest `tests/agent` **26 passed**; contract suite (agent + integration + review_case + scoring + fairness) **102 passed**; ruff pass; `git diff --check` sạch. **Skip có ghi:** `test_health`/`test_case_transitions`/`test_dwh_migrate` không chạy được trên máy build (env thiếu fastapi/sqlalchemy — không liên quan T03); chưa live-LLM eval (thuộc T02).
- Doc draft cho H11b: [08-agent-grounding-guardrails.md](../04-engineering/08-agent-grounding-guardrails.md). Mở khóa: `T01` (TODO).

## 2026-07-18 (M06 Done — domain transform + quality report)

- `M06` **Done** (Duy): `backend/app/ml/domain/` — `models.py` (Pydantic domain rows + `DataQualityReport`, tên khớp cột `dwh`), `transform.py` (semester: term_code normalize, taxonomy `Trạng thái` decision #17, miền điểm `[0,10]`, khóa unique, reject reasons, coverage `single_term`/`grade_coverage_insufficient`/`status_unknown`), `attendance.py` (nhánh `mvp-attendance-over-time`; rate loại `excused=true`; ≥4 mốc; trend ≥2 điểm). `DataQualityReport` được lắp trong transform/attendance (không tách file riêng).
- Fail-closed: field PII/token trong input ⇒ `PiiFieldError` (zero output). Không cross-join hai nguồn. `is_dropout_outcome` chỉ ở `academic_status` (evaluation) — test chứng minh không rò sang `student_dimension`/`term_grade`/`advisor_assignment`.
- Committed attendance artifacts (pseudonymous, no PII): later moved to `data/approved/attendance/` — regen-deterministic (test so khớp build).
- Semester domain artifact: initially ngoài repo; sau đó commit package `data/approved/semester/domain_package.json` (git-ready).
- Tests: `tests/test_m06_domain_fixture.py` (46) — normalize, taxonomy, reject layers, PII fail-closed, determinism, no cross-join, alignment field ↔ cột `dwh`, attendance rate/excused/coverage, artifact no-drift.
- Verify: `ruff check app tests` pass; `pytest -q -m "not slow and not eval"` → **197 passed, 4 errors**. 4 errors = `test_dwh_migrate.py` (H19) yêu cầu Postgres (`docker compose up -d db`) — **không** liên quan M06 (transform thuần, không chạm DB); môi trường local không có Docker. FE không đổi (không chạy). Chưa commit trong bước này → commit/push branch `KhanhDuyBui` theo yêu cầu.
- Mở khóa `H20` (Hoàng) — consume `app/ml/domain` output. `M02` vẫn `BLOCKED → H08` (H20→H08).

## 2026-07-18 (~07:05 M05b + H15 unlock — decision #18)

- **Decision #18:** team approver (Hoàng) unlock MVP demo — semester V59 ngoài git + attendance allowlisted `mvp-attendance-over-time`.
- `M05a`/`H06c` board sync **Done** (PR #17). `M05b` **Done** — [14-m05b…](14-m05b-semester-approval.md) (hash `34a53298…`, 460 rows).
- `H15` **Done** — [12-h15…](12-h15-attendance-approval-prep.md) + fixture `data/approved/attendance/mvp_attendance_over_time.json`; amend EPU/Data-ML/persistence; RULES pointer.
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
- Scan tracked tree (`scripts/d3_pii_secret_scan.py` + gitleaks): không secret trong tree; 24 findings SĐT trên hai bản khảo sát trùng → redact; bản canonical còn lại là `02-team.md`.
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
- Chưa xong lúc ghi nhận: AWS creds invalid, `GITHUB_TOKEN` user env; optional tracing sau đó được bỏ khỏi MVP.

## 2026-07-17

- Chọn đề Silent Shield (~75% transfer từ EduInsight) — [Quyết định chọn đề](01-topic-selection.md)
- Bootstrap skeleton tối giản + chuyển MD gốc vào `docs/`
- Phân lane H/M/G/T/A/V/D — [Đội ngũ và phân vai](02-team.md)
