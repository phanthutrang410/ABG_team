# Stories — Hoàng: weekly snapshot, OpenAI và Global Agent

> **Owner:** Hoàng
> **Trạng thái:** Planned wave sau release gate hiện tại; không tự động block `D4r` / `V05` / `H09`.
> **Nguồn chuẩn:** [Decision #22](04-decisions.md) · [Target architecture](../04-engineering/13-weekly-snapshot-global-agent-architecture.md) · [PRD](../02-product/04-prd.md) · [Process](../02-product/03-process.md) · [Ethics](../02-product/05-ethics.md) · [BRD](../02-product/08-brd.md).
> **Ranh giới owner:** Hoàng sở hữu contract, backend/API, persistence, security scope và deploy. Frontend `G07–G09` thuộc **Khánh Duy** (decision #24); adversarial/e2e `T05` thuộc Thu Trang trừ khi Sprint đổi owner rõ ràng.

Tài liệu này là task brief chi tiết cho các row mới trong [Sprint §3–4](03-sprint.md). `H28` chỉ chứng minh kiến trúc/decision đã được viết; nó **không** có nghĩa weekly feed, OpenAI runtime hay Global Agent đã ship.

## 1. Dependency graph và thứ tự thực hiện

```text
H28 ✓
 ├─→ H29 OpenAI adapter ───────────────────────────────┐
 └─→ H28a readiness/decision lock                     │
       ├─→ H30 snapshot registry/run ledger           │
       │     └─→ H31 stage/promote + approved replay  │
       │            └─→ H32 linked bundle/observation │
       │                   └─→ H33a durable case/event│
       │                          └─→ H33b delta engine├─→ H34a weekly report
       │                                               │       └─→ H34b briefing/receipt
       └─→ H36 production auth/RBAC ──────────────────┘       ├─→ H38 safe export
                                                              ├─→ H35 advisor draft v2
H29 + H34b + H35 + H36 ───────────────────────────────────────┴─→ H37 Agent tool runtime

H36 → G07 → G08/G09
H29 + H34b + H37 + G07 → T05
H31 + H34b + H35 + H37 + H38 → D6
```

`H32` không được bắt đầu bằng heuristic nếu chưa có canonical linked bundle cùng pseudonym namespace được duyệt. `H34a`/`H34b`/`H35`/`H37` không được mở public scope trước `H36`.

## 2. Danh sách task của Hoàng

| ID | Priority · timebox | Outcome | Depends | Status |
|:--|:--|:--|:--|:--|
| `H28` | P0 · docs | Khóa target architecture và OpenAI decision | H27 baseline audit | [x] Done — docs/decision only |
| `H28a` | P0 · 2–3h | Khóa readiness: delta, linked snapshot, identity, retention và scheduler | H28 | [x] Done — Decision #23 |
| `H29` | P0 · 3–4h | Migration runtime từ FPT sang OpenAI Responses | H28 | [x] Done |
| `H30` | P0 · 3–4h | Snapshot v2 registry + workflow ledger + active pointer | H28a, H19 | [x] Done |
| `H31` | P0 · 3–4h | Stage/promote workflow service + CLI approved replay | H30, H20 | [x] Done |
| `H32` | P0 · 3–4h | Canonical linked bundle + immutable observations | H31, H28a | [x] Done — Mode B |
| `H33a` | P0 · 3–4h | Durable case/event persistence; GET trở thành read-only | H32, H06b | [x] Done — in-memory MVP |
| `H33b` | P0 · 3–4h | Deterministic delta/reconcile engine | H33a, H28a | [x] Done |
| `H36` | P0 · 3–4h | Production identity/RBAC/scope + access-audit foundation | H28a, H06b | [x] Done |
| `H34a` | P1 · 3–4h | Weekly report materializer + scoped APIs | H33b, H36 | [x] Done |
| `H34b` | P1 · 2–3h | Deterministic briefing + one-time receipt APIs | H34a, H36 | [x] Done |
| `H35` | P1 · 2–3h | Advisor draft v2 trên durable approved cases/report | H34a, H36, H22 | [x] Done |
| `H37` | P1 · 3–4h | Global Agent backend turn + strict capability registry | H29, H34b, H35, H36 | [x] Done |
| `H38` | P1 · 2–3h | Export report an toàn + watermark/access audit | H34a, H36 | [x] Done |
| `D6` | Release · 3–4h | Scheduler/worker deploy, observability, retention và rollback | H31, H34b, H35, H37, H38 | [x] Done — ops foundation |

## 3. Task briefs chi tiết

<a id="h28"></a>
### H28 — Target architecture + provider decision

```text
ID — Outcome: H28 — Khóa kiến trúc đích tách weekly data DAG, application services và Global Agent; OpenAI là provider target.
Phase / Priority / Timebox: Architecture / P0 / docs task.
Owner: Hoàng.
Depends on + readiness: audit code/docs H19–H27; owner đã reconfirm OpenAI.
Read first: PRD §§5–8; Process §§3–6; Ethics §§3–8; BRD §§8–9; docs 05/10/11/12.
Input contract / fixture: hiện trạng schema/importer/case/agent; không cần hoặc tạo dữ liệu mới.
Scope: Decision #22; current-vs-target; snapshot/DAG/delta/report/Global Agent/tool/RBAC/backlog.
Do not touch: runtime code, scoring, data rows, live provider, auto-send hoặc bulk export định danh.
Verify: local links; Quick verify; git diff --check; current-vs-target khớp code.
Evidence / Done when: docs/04-engineering/13-weekly-snapshot-global-agent-architecture.md + Decision #22; mọi feature chưa ship được ghi rõ.
```

**Trạng thái:** **Done — docs/decision only**. Task này mở `H28a` và `H29`, không mở trực tiếp importer/report/UI.

<a id="h28a"></a>
### H28a — Readiness và decision lock cho build

```text
ID — Outcome: H28a — Chuyển sáu open decisions của architecture thành contract/approval handles có thể dùng làm dependency.
Phase / Priority / Timebox: Wave 0 / P0 / 2–3 giờ.
Owner: Hoàng.
Depends on + readiness: H28 Done; Product owner, data owner và identity/deploy owner cung cấp input hoặc xác nhận limitation.
Read first: target architecture §§4,7,8,13,16; EPU contract; Data-ML contract; BRD §§8–9; Decisions #18/#20/#22.
Input contract / fixture: approval handle cho canonical linked bundle; role/scope matrix; retention; scheduler target; không nhận raw PII qua repo.
Scope: chốt significant-change/resurfaced semantics; pseudonym namespace; identity claims/scope; receipt/audit retention; scheduler adapter; export/email boundary.
Do not touch: tự phê duyệt nguồn thay data owner, tự tạo snapshot tuần, schema migration hoặc code provider.
Verify: decision/contract links không mâu thuẫn PRD/Ethics/Process; từng downstream task có task-ID dependency và readiness rõ.
Evidence / Done when: decision mới/amendment có owner/date; approval handle được ghi không lộ PII; `H30`, `H32`, `H33b`, `H36` không còn input mơ hồ.
```

<a id="h29"></a>
### H29 — OpenAI Responses provider migration

```text
ID — Outcome: H29 — Runtime agent dùng OpenAI API key thật phía server qua adapter provider-neutral; không còn chọn FPT trong runtime target.
Phase / Priority / Timebox: Wave 1 / P0 / 3–4 giờ.
Owner: Hoàng.
Depends on + readiness: H28 Done; model target được cấu hình cho mocked contract, live smoke chưa cần để build.
Read first: target architecture §11; Ethics §8; agent model/runtime/grounded/renderer; H24–H26 tests; official OpenAI Responses/function-calling/data docs.
Input contract / fixture: existing FakeModel + StructuredPlan; mocked OpenAI Responses payload; env names `OPENAI_API_KEY`/`OPENAI_MODEL`.
Scope: tách TextModel/ModelUnavailable; OpenAIResponsesClient; Settings/runtime; official host; store=false; strict schema; one application attempt; secret-safe errors/logging.
Do not touch: weekly DAG, scoring/delta, case transition, frontend, automatic provider fallback hoặc live call trong default tests.
Verify: Ruff; mocked happy/missing-key/401/429/timeout/malformed/oversize; request forbidden-field scan; existing grounding/refusal/adversarial tests; full verify.
Evidence / Done when: runtime factory chỉ dựng OpenAI target; FPT client không còn active path; tests chứng minh missing key = zero network call và provider failure = unavailable.
```

<a id="h30"></a>
### H30 — Snapshot v2 registry và workflow ledger

```text
ID — Outcome: H30 — DB lưu nhiều snapshot immutable của cùng dataset và theo dõi workflow run/step mà không overwrite history.
Phase / Priority / Timebox: Wave 1 / P0 / 3–4 giờ.
Owner: Hoàng.
Depends on + readiness: H28a Done; H19 Done; snapshot v2 contract và retention đã khóa.
Read first: target architecture §§4–6; persistence schema; dwh models/migrations; importer idempotency; migration tests.
Input contract / fixture: dataset_key, snapshot_id, three hashes, period/extracted_at, approval/lineage, workflow/model/threshold versions.
Scope: Alembic cho dataset_source/dataset_snapshot/active pointer/workflow_run/workflow_step_run; migrate current snapshot thành version đầu; constraints/indexes.
Do not touch: import rows mới, scoring, case/report materialization, destructive rewrite dữ liệu hoặc nối source_id thành weekly ID.
Verify: upgrade/downgrade trên DB test; multi-version same dataset; duplicate hash; correction lineage; invalid period/hash/status; transaction rollback; Ruff + full verify.
Evidence / Done when: schema có PK/FK/unique/check rõ; current source được bảo toàn; migration tests xanh và docs persistence đồng bộ.
```

<a id="h31"></a>
### H31 — Stage/promote workflow + approved replay

```text
ID — Outcome: H31 — Cùng WeeklyWorkflowService chạy được từ CLI và scheduler adapter, stage/promote atomic và replay idempotent.
Phase / Priority / Timebox: Wave 1 / P0 / 3–4 giờ.
Owner: Hoàng.
Depends on + readiness: H30 + H20 Done; có approved artifact ref; không cần snapshot tuần mới để test replay.
Read first: target architecture §§4.2–5; current import_gate/importer/cli; H20 tests; deploy runbook.
Input contract / fixture: manifest_ref + content hash + idempotency key; exact bytes package pseudonymous đã duyệt.
Scope: register→validate→stage→promote skeleton; CLI `weekly run`; advisory lock/idempotency; replay_of; failure reason; internal service interface.
Do not touch: public upload endpoint, APScheduler trong FastAPI, sửa extracted_at/observations để giả tuần mới, case/report/LLM.
Verify: exact-byte replay; concurrent duplicate; approval/hash/schema fail zero promotion; crash từng stage giữ active pointer; same input no duplicate effects; full verify.
Evidence / Done when: CLI run và replay có run ledger; duplicate/no-op xác định; approved bytes không bị mutate; failure có reason code và rollback.
```

<a id="h32"></a>
### H32 — Canonical linked bundle và signal observations

```text
ID — Outcome: H32 — Một canonical bundle cùng pseudonym namespace được normalize thành immutable signal observations có coverage/freshness đúng nguồn.
Phase / Priority / Timebox: Wave 2 / P0 / 3–4 giờ.
Owner: Hoàng.
Depends on + readiness: H31 Done; H28a có approval handle cho linked namespace. Nếu chưa có → BLOCKED, không join heuristic.
Read first: EPU/Data-ML contracts; target architecture §§4,6; current read_adapter/scoring; source/import/coverage tests.
Input contract / fixture: approved linked bundle hoặc approved as-of replay; same namespace cho semester/attendance/advisor; actual extracted_at.
Scope: snapshot-keyed domain adapter; coverage/freshness; deterministic scoring call; immutable observation + evidence fingerprint; separate fairness gate state.
Do not touch: generate/modify student/grade/attendance rows, cross-source fuzzy join, public raw score/outcome/audit attribute, delta/case state.
Verify: hash/count/PII/schema; namespace mismatch fail; missing branch insufficient_data; same input+versions deterministic; source freshness not calculated_at-now; full verify.
Evidence / Done when: observations có lineage/versions và forbidden-field scan; fixture current zero-intersection không bị mô tả là combined feed.
```

<a id="h33a"></a>
### H33a — Durable case/event persistence

```text
ID — Outcome: H33a — Case episode và event history được persist; đọc danh sách/chi tiết không còn tạo hoặc mutate case.
Phase / Priority / Timebox: Wave 2 / P0 / 3–4 giờ.
Owner: Hoàng.
Depends on + readiness: H32 Done; H06b Done; persistence contract giữ nguyên Process state/action.
Read first: Process §4; Ethics anti-repeat; target architecture §§6–7; cases domain/store/review_projection; transition/review API tests.
Input contract / fixture: immutable observations H32; current case snapshots/history; opaque student/scope handles.
Scope: review_case/case_event schema+repository; opaque episode ID; one-active-episode constraint; migrate current RAM behavior; GET read-only.
Do not touch: delta classification, auto approve/dismiss/resolve/assign, scoring, Agent hoặc đổi state vocabulary.
Verify: create/read/update through authorized transition service; GET no write; append-only history; concurrent active-episode constraint; migration/transition regression; full verify.
Evidence / Done when: RAM store không còn source of truth; every transition có durable event; H33b nhận stable repository contract.
```

<a id="h33b"></a>
### H33b — Deterministic delta và case reconcile

```text
ID — Outcome: H33b — Delta tuần được tính deterministic và reconcile vào durable case episode mà không ghi đè quyết định con người.
Phase / Priority / Timebox: Wave 2 / P0 / 3–4 giờ.
Owner: Hoàng.
Depends on + readiness: H33a + H28a Done; significant-change/resurfaced policy đã khóa.
Read first: target architecture §7; Process §4; Ethics false-alarm/anti-repeat; observation and case repository contracts/tests.
Input contract / fixture: comparable observations của current/previous successful promoted run; model/threshold/namespace versions.
Scope: delta types initial/new/ongoing/changed/no-longer/resurfaced/comparison-unavailable; reconcile events/effects idempotent.
Do not touch: treat all baseline rows as new; compare incompatible versions; auto close/transition; agent/LLM decision.
Verify: full delta matrix; terminal/resurface policy; preserve pending/approved/assigned/monitoring; duplicate run no event; concurrent reconcile; full verify.
Evidence / Done when: report-ready delta output có lineage; unique effect keys chặn trùng; no-longer-detected không tự resolve/dismiss.
```

<a id="h36"></a>
### H36 — Production identity, RBAC và access-audit foundation

```text
ID — Outcome: H36 — Mọi report/case/agent/advisor request lấy actor/role/org/advisor scope từ trusted server session và có audit metadata tối thiểu.
Phase / Priority / Timebox: Wave 2 / P0 / 3–4 giờ.
Owner: Hoàng.
Depends on + readiness: H28a Done; H06b Done; identity provider/session claims + role matrix được chốt.
Read first: BRD §§8–9; Ethics §§3–4; target architecture §§8–10; current auth/session/AppShell/my-class/advisor router; security tests gần nhất.
Input contract / fixture: trusted actor ID, active role, organization scope, assigned advisor scope; negative-role fixtures; retention/audit policy.
Scope: backend principal dependency; scope service/query filters; source/advisor derived server-side; audit event/resource handle; deny-by-default errors.
Do not touch: coi localStorage/client role là security, nhận actor/advisor/source scope từ client, lộ existence của resource ngoài scope hoặc log PII/raw prompt.
Verify: leader/GVCN/admin allow matrix; cross-org/cross-advisor/role-switch negative tests; forged fields rejected; audit metadata; Ruff + full verify.
Evidence / Done when: production routes không dùng demo identity; GVCN không fetch toàn bộ rồi lọc client; H34a/H34b/H35/G07 có trusted scope contract.
```

<a id="h34a"></a>
### H34a — Weekly report materializer và APIs

```text
ID — Outcome: H34a — Backend materialize report tuần có exact aggregates, delta/limitations và scoped list APIs.
Phase / Priority / Timebox: Wave 2 / P1 / 3–4 giờ.
Owner: Hoàng.
Depends on + readiness: H33b + H36 Done; WeeklyReport schemas đã khóa bằng Pydantic + validated fixtures.
Read first: target architecture §8; PRD FR-03/05; BRD §§8–9; reporting persistence; nearest API contract tests.
Input contract / fixture: durable cases/delta + workflow/snapshot versions + coverage/freshness/fairness status; authenticated principal.
Scope: weekly_report/item materializer; latest/by-id/scoped-list APIs; stale/failed/empty/baseline-unavailable states; last successful pointer.
Do not touch: LLM tạo counts/newness; public bulk identifiers; export file; briefing receipt; hide last failed sync; auto-change case state.
Verify: exact aggregates; first baseline; new/ongoing/changed; previous failed run; stale source; RBAC negative tests; full verify.
Evidence / Done when: G08/H34b/H38 có OpenAPI + fixtures; provider down không ảnh hưởng report; full organization list chỉ trong authorized app response.
```

<a id="h34b"></a>
### H34b — Deterministic briefing và one-time receipt

```text
ID — Outcome: H34b — Backend trả một briefing deterministic đúng role/scope và ghi receipt để chỉ tự hiện một lần mỗi report.
Phase / Priority / Timebox: Wave 2 / P1 / 2–3 giờ.
Owner: Hoàng.
Depends on + readiness: H34a + H36 Done; briefing/receipt schema và retention khóa.
Read first: target architecture §9; PRD FR-08 boundary; H34a report contract; identity/audit contract; UI briefing state proposal.
Input contract / fixture: scoped WeeklyReport; authenticated principal+role; ok/empty/stale/failed/baseline-unavailable fixtures.
Scope: deterministic message catalog; latest briefing API; shown/ack endpoints; unique receipt `(user, role, briefing)`; concurrent dedupe.
Do not touch: OpenAI tạo counts/newness; localStorage làm source of truth; raw student refs trong auto-popup; auto-blocking modal.
Verify: role-specific content/actions; first show once; navigation/relogin/role switch; concurrent shown/ack; stale/failed copy; full verify.
Evidence / Done when: G08 có stable API/fixtures; repeated navigation không tái auto-open; OpenAI off vẫn có briefing/action cards.
```

<a id="h35"></a>
### H35 — Advisor draft API v2 trên durable cases

```text
ID — Outcome: H35 — Advisor draft bundles dùng đúng report/run và chỉ gom case durable đã approved/assigned trong server scope.
Phase / Priority / Timebox: Wave 3 / P1 / 2–3 giờ.
Owner: Hoàng.
Depends on + readiness: H34a + H36 + H22 Done; H22 contract giữ draft-only.
Read first: advisor draft doc 11; Ethics §4; Process handoff; target architecture §12; H22 router/service/tests.
Input contract / fixture: report_id; durable eligible cases; internal advisor mapping; mapping-repair cases; authenticated leader scope.
Scope: bỏ client-controlled source/advisor expansion; report lineage; deterministic grouping/draft preview; mapping_repair; audit metadata.
Do not touch: email/SĐT/họ tên public, SMTP/Gmail/Outlook, auto recipient selection, send/mark-sent hoặc transition state.
Verify: approved/assigned only; pending/dismissed/resolved excluded; mapping missing bucket; cross-scope deny; forbidden public fields; no send route; full verify.
Evidence / Done when: G09 nhận stable envelope + fixtures; `requires_human_approval=true`; existing H22 behavior được migrate không regression.
```

<a id="h37"></a>
### H37 — Global Agent backend turn và capability registry

```text
ID — Outcome: H37 — `POST /agent/turns` chỉ chọn/thực thi capability read/navigation/draft-preview đã authorize và trả controlled UI actions.
Phase / Priority / Timebox: Wave 3 / P1 / 3–4 giờ.
Owner: Hoàng.
Depends on + readiness: H29 + H34b + H35 + H36 Done; capability schemas và route-key allowlist đã khóa.
Read first: target architecture §§10–11; Ethics §8; H23–H29 agent code/tests; report/advisor contracts; OpenAI tool-calling docs.
Input contract / fixture: safe page context `{surface, resource_handle}`; principal scope; capability registry; mocked OpenAI tool decision.
Scope: input guard; server context resolution; allowed capability derivation; max one tool decision; read/draft-preview executor; evidence refs/cards/ui_action; redacted audit.
Do not touch: run_workflow, send_mail, transition/approve/assign, arbitrary URL/SQL/search, raw DWH/PII, memory xuyên case hoặc parallel tool calls.
Verify: strict schema/additionalProperties false; injection/PII/out-of-scope; fabricated route/tool args; provider down; one-call bound; zero forbidden effect; full verify.
Evidence / Done when: G07/G08 có contract ổn định; action cards hoạt động không cần provider; every model claim maps to allowed evidence handle.
```

<a id="h38"></a>
### H38 — Export báo cáo an toàn

```text
ID — Outcome: H38 — Ban quản lý xuất được aggregate không định danh hoặc một case có watermark/audit, không có bulk export định danh.
Phase / Priority / Timebox: Wave 3 / P1 / 2–3 giờ.
Owner: Hoàng.
Depends on + readiness: H34a + H36 Done; BRD §9 giữ nguyên.
Read first: BRD §§8–9; Ethics access/data minimization; target architecture §8.3; weekly report schema; audit contract.
Input contract / fixture: scoped WeeklyReport; per-case safe projection; principal/watermark timestamp; export reason if policy requires.
Scope: aggregate CSV/PDF-safe response; per-student export one case; watermark + access audit; content disposition/size bounds; forbidden-field scan.
Do not touch: toàn bộ identifiable student list download, raw score/outcome/audit group, background email delivery hoặc client-side generation từ unscoped list.
Verify: aggregate contains no identifiers; per-case watermark/audit; bulk filter rejected; cross-scope deny; formula/CSV injection escaping; deterministic snapshot/version labels; full verify.
Evidence / Done when: export acceptance của BRD §9 xanh; mỗi per-case export có audit event; no bulk-identifiable endpoint trong OpenAPI.
```

<a id="d6"></a>
### D6 — Scheduler/worker deploy và operations gate

```text
ID — Outcome: D6 — Weekly workflow chạy theo lịch qua external scheduler/worker, quan sát được, replay/rollback được và không phụ thuộc OpenAI.
Phase / Priority / Timebox: Release wave / P1 / 3–4 giờ.
Owner: Hoàng.
Depends on + readiness: H31, H34b, H35, H37, H38 Done; H37 đã chạy mocked grounding/RBAC/adversarial gate; deploy target/retention/secret policy khóa ở H28a.
Read first: target architecture §§4.3,5,13; deploy runbook; workflow CLI/service; release evidence template; provider/data retention docs.
Input contract / fixture: service-auth manifest reference; approved replay schedule; kill-switch config; redacted run IDs/metrics.
Scope: EventBridge+queue/worker hoặc approved cron adapter; secret/config; run status/alerts; stale SLA; kill switches; replay; rollback; runbook/evidence.
Do not touch: public trigger/upload, scheduler trong FastAPI process, rows trong event, raw snapshot/prompt logs, provider call trong critical workflow path.
Verify: scheduled approved replay; duplicate schedule no-op; failed run keeps latest report; kill switches; worker restart; rollback; health/API/UI smoke; full verify.
Evidence / Done when: runbook có exact start/stop/replay/rollback; redacted scheduled-run evidence; report/briefing vẫn hoạt động khi OpenAI off.
```

<a id="h39a"></a>
### H39a — DB-backed auth/session + canonical roles

```text
ID — Outcome: H39a — Schema app.* auth + /auth/* cookie session; Principal chỉ {ban_quan_ly,gvcn}
Phase / Priority / Timebox: Next wave / P0 / 3–4 giờ
Owner: Hoàng
Depends on: H36 Done; H30 Alembic/Postgres
Scope: migration 20260719_h39a_auth_rbac; seed CLI; login/me/active-role/logout; Decision #23 amend; ERD app.*
Do not touch: dwh domain; FE; RBAC enforcement on open APIs (H39b)
Verify: migration + CHECK; login matrix; Ruff + targeted pytest
```

<a id="h39b"></a>
### H39b — Enforce RBAC on frontend APIs

```text
ID — Outcome: H39b — ban_quan_ly/gvcn matrix trên case/config/draft/explanation/export; audit persist
Depends on: H39a Done
Scope: review-cases, transitions, thresholds/fairness, advisor drafts, agent explanation; no client source_id
Do not touch: FE session UI (G07); ReviewCase DTO; new migrations
Verify: RBAC matrix tests; full verify; OpenAPI
```

## 4. Handoff sang lane khác

| Hoàng hoàn tất | Consumer được mở | Contract/evidence bàn giao |
|:--|:--|:--|
| `H36` / `H39a`+`H39b` | Khánh Duy `G07` | `/auth/*` + cookie identity; roles `{ban_quan_ly,gvcn}`; negative tests |
| `H34a` + `H34b` + `H36` | Khánh Duy `G08` | Weekly report/briefing OpenAPI + ok/empty/stale/failed/baseline fixtures |
| `H35` + `H36` | Khánh Duy `G09` | Advisor draft v2 + mapping-repair/no-send fixtures |
| `H29` + `H34b` + `H37` | Thu Trang `T05` | Mocked provider/tool runtime, capability matrix và forbidden-effect hooks |
| `H31` + `H34b` + `H35` + `H37` + `H38` | Hoàng `D6` | Release candidate workflow + full test/evidence set; `T05` là cross-lane QA bổ sung khi được board hóa |

Consumer không bắt đầu bằng frontend mock tự đặt field hoặc quyền. Provider task chỉ được tick Done khi schema → fixture → producer → tests → docs cùng khớp.

## 5. Definition of Done chung cho wave

- Không có synthetic/modified weekly observations trên operational/demo path; mock sender chỉ replay artifact đã duyệt.
- `newly_detected` do backend deterministic tính từ comparable successful run; không phải LLM/UI heuristic.
- GET/read không tạo case hoặc đổi state; mọi care transition vẫn là hành động người theo Process.
- OpenAI nhận safe projection, dùng `store=false`; provider down không làm hỏng report/case/navigation.
- GVCN chỉ thấy case được giao; actor/scope không đến từ client.
- Advisor workflow chỉ draft/Copy/`mailto:`; không send endpoint.
- Xem full list trong app; export chỉ aggregate hoặc per-case có watermark/audit.
- Targeted tests, full verify, `git diff --check`, status/diff review và release evidence sạch PII/secret.
