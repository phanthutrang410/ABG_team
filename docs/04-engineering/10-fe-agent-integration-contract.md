# FE / Agent integration contract — Silent Shield (H11a + H11b)

> **Owner:** Hoàng · **Tasks:** H11a (schema lock) · **H11b** (docs after build).
> **Depends:** H06a Done (`ReviewCase` / `Coverage` / `ScoringFeatures`).
>
> Contract tối thiểu cho FE và agent. Schema Pydantic: `backend/app/contracts/integration.py`. Fixture JSON dưới `backend/tests/fixtures/integration/`. Khi lệch prose ↔ code, sửa schema hoặc mở decision — không âm thầm chọn một bản.
>
> **Không** thay [Data-ML](08-data-ml-scoring-fairness-contract.md) hay [Process](../02-product/03-process.md). Copy VI runtime thuộc [H12a](../03-project/03-sprint.md) / Data-ML §6 — contract này khóa **field allowlist** và **trạng thái lỗi**.
>
> **Delta sau H11b:** Repo hiện có `AgentPanel` trên case detail. Global Agent/weekly briefing và provider OpenAI vẫn là target chưa ship; xem [doc 13](13-weekly-snapshot-global-agent-architecture.md). Các dòng “no FE Agent UI” bên dưới chỉ mô tả thời điểm đóng H11b nếu được ghi là history.

## 1. Mục tiêu

| Consumer | Vai trò khi H11a Done |
|:---|:---|
| G05 | Types/routes theo public DTO + fixture đã validate; loading/error/empty/`insufficient_data`/`stale` |
| T03 | Agent context = cùng safe projection; refusal / insufficient / unavailable semantics |

H02 HTTP list/detail và T01/T02 core/library implement theo envelope này. Server-derived context + public Agent command route: [H23–H26](12-agent-runtime-integration-plan.md); browser không được gửi `AgentContextResponse`.

## 1.1 After build (H11b) — consumer matrix

| Surface | Status | Consumer |
|:--|:--|:--|
| `GET /review-cases` list/detail | **Done** | G05 + G02 |
| Care `POST /cases/.../transitions` | **Done** | G03 |
| Threshold / fairness config | **Done** | G04 |
| Agent `POST /review-cases/{id}/explanation` | **Done — backend HTTP** | Mocked E2E + `AgentPanel` case-local |
| FE Agent explain UI | **Done — case-local only** | `frontend/src/components/AgentPanel.tsx`; chưa phải Agent toàn cục |
| Global Agent + weekly briefing | **Chưa ship** | Target contract ở doc 13 |

**Claim boundary:** Có backend HTTP và case-local consumer. Không claim Global Agent, weekly workflow/briefing, live provider smoke hay production RBAC.

**`advisor_ref`:** vẫn **forbidden** trên ReviewCase / agent context (H11a §2.1). Exception chỉ trên FR-12 handoff-draft envelope ([doc 11](11-advisor-batch-mail-draft.md) / H22) — không mở rộng vào list/detail/agent.

## 2. Allowed display fields (public + agent context)

Chỉ được hiển thị / đưa vào agent context các field của `ReviewCase` (H06a):

| Field | UI | Agent |
|:---|:---:|:---:|
| `case_id` | có | có |
| `student_ref` (pseudonym) | có | có |
| `case_state` | có | có |
| `review_priority_band` | có | có |
| `contributing_factors[]` (`code`, `evidence_refs`) | có | có |
| `coverage` (counts, freshness timestamps, `status`, `reason_codes`) | có | có |
| `data_state` | có | có |
| `limitations[]` (machine / copy keys) | có | có — map VI qua H12a |
| `dataset_version` / `model_version` / `threshold_config_version` | có | có |
| `calculated_at` | có | có |

### 2.1 Forbidden (mọi surface public / agent)

Không được xuất hiện trong list/detail/agent context, mock G05 sau khi thay, hay tool observation:

`model_score`, `risk_score`, `raw_score`, `probability`, `weight`, `is_dropout_outcome`, `advisor_ref`, MSSV/tên/ngày sinh/email/SĐT, crawl `token`, thuộc tính nhóm audit, raw DWH rows, chain-of-thought.

FE **không** tự fallback band/priority khi API thiếu (RULES / AGENTS).

## 3. Envelope states

### 3.1 Case list — `CaseListResponse`

| `state` | `items` | `problem` | UI/G05 |
|:---|:---|:---|:---|
| `ok` | ≥1 `ReviewCase` | null | Render list |
| `empty` | `[]` | optional | Empty state — không bịa case |
| `stale` | 0..n (có thể kèm data) | `stale_snapshot` khuyến nghị | Banner stale + vẫn hiện items nếu có; không gọi là “mới nhất” |
| `error` | `[]` | **bắt buộc** | Error state; không fallback mock score |

### 3.2 Case detail — `CaseDetailResponse`

| `state` | `case` | `freshness` | Ý nghĩa |
|:---|:---|:---|:---|
| `ok` | có | `fresh` | Happy path |
| `empty` / not found | null | — | Không có case trong scope |
| `insufficient_data` | có hoặc null | — | Thiếu coverage/evidence; nếu có `case` thì `data_state=insufficient_data` |
| `stale` | có | `stale` | Snapshot/tính toán quá hạn theo gate freshness |
| `error` | null | — | Lỗi upstream/validation; `problem` bắt buộc |

`insufficient_data` **không** đồng nghĩa empty: có thể vẫn có case với limitation/`reason_codes` (vd. attendance unapproved + term partial → thường `data_state=partial`, không phải state envelope `insufficient_data`). Envelope `insufficient_data` dùng khi **không đủ** để giải thích/ưu tiên có ý nghĩa (coverage.status=`insufficient`).

### 3.3 Agent context — `AgentContextResponse`

| `status` | `case` | Hành vi |
|:---|:---|:---|
| `ready` | safe `ReviewCase` | Grounded explain / neutral draft |
| `empty` | null | Không có case trong scope |
| `insufficient_data` | optional partial/insufficient case | Trả insufficient; không bịa factor |
| `refused` | null | Ngoài scope / score / cause / handoff / PII |
| `unavailable` | null | Tool/upstream/timeout — UI care vẫn dùng được |

Allowed intents (H11a khóa tên): `explain_case`, `neutral_draft`. Agent **không** được transition case (H06b đã cấm `actor_kind=agent|llm`).

State/intent gate runtime theo [doc 12 §4](12-agent-runtime-integration-plan.md): `neutral_draft` chỉ sau approval với mapping nội bộ hợp lệ; stale/insufficient/refused bị chặn trước FPT. Envelope này khóa shape, không cấp quyền cho client tự chọn context hay nới state.

## 4. Problem object

```text
IntegrationProblem:
  code: not_found | unauthorized | validation_error | upstream_unavailable
        | stale_snapshot | insufficient_data | empty | refused
  reason_codes[]: machine codes (Data-ML §3 / H12a keys không có prefix copy.)
  message_key: optional copy.* hoặc code — không nhúng đoạn văn VI dài trong API
```

## 5. Fixtures (validated)

| Fixture | Dùng cho |
|:---|:---|
| `integration/case_list_ok.json` | G05 list happy |
| `integration/case_list_empty.json` | G05 empty |
| `integration/case_list_stale.json` | G05 stale banner |
| `integration/case_list_error.json` | G05 error |
| `integration/case_detail_ok.json` | G05/T03 detail |
| `integration/case_detail_insufficient.json` | insufficient_data |
| `integration/case_detail_stale.json` | stale detail |
| `integration/agent_context_ready.json` | T03 grounded |
| `integration/agent_context_refused.json` | T03 refusal |
| `integration/agent_context_insufficient.json` | T03 insufficient |
| `integration/agent_context_unavailable.json` | T03 unavailable |

## 6. Verify / Done when

### H11a (schema lock — Done)
- Pydantic envelopes + `extra=forbid`; test reject forbidden keys trên mọi envelope.
- Mọi fixture trên validate được.
- Sprint `H11a` / `H11a-r` Done → mở `G05` / `T03`.

### H11b (docs after build — historical Done criteria)
- Tại thời điểm đóng H11b: G05–G04 consume list/detail/care/config; agent = backend HTTP; chưa có FE Agent UI. Repo đã thêm case-local `AgentPanel` sau mốc này; Global Agent vẫn chưa ship.
- Architecture §6 + [guardrails](08-agent-grounding-guardrails.md) không còn “HTTP pending”.
- Không overclaim live provider / Global Agent / production RBAC / ReAct multi-loop.
