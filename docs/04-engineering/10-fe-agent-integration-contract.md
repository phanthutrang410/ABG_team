# FE / Agent integration contract — Silent Shield (H11a)

> **Owner:** Hoàng · **Task:** H11a · **Depends:** H06a Done (`ReviewCase` / `Coverage` / `ScoringFeatures`).
>
> Contract tối thiểu để **G05** (FE thay mock) và **T03** (agent interface) bắt đầu. Schema Pydantic: `backend/app/contracts/integration.py`. Fixture JSON dưới `backend/tests/fixtures/integration/`. Khi lệch prose ↔ code, sửa schema hoặc mở decision — không âm thầm chọn một bản.
>
> **Không** thay [Data-ML](08-data-ml-scoring-fairness-contract.md) hay [Process](../02-product/03-process.md). Copy VI runtime vẫn thuộc [H12a](../03-project/03-sprint.md) / Data-ML §6 — contract này chỉ khóa **field allowlist** và **trạng thái lỗi**.

## 1. Mục tiêu

| Consumer | Được bắt đầu khi H11a Done |
|:---|:---|
| G05 | Types/routes theo public DTO + fixture đã validate; loading/error/empty/`insufficient_data`/`stale` |
| T03 | Agent context = cùng safe projection; refusal / insufficient / unavailable semantics |

H02 HTTP list/detail và T01/T02 core/library đã implement theo envelope này. Server-derived context, public Agent command route và runtime hardening thuộc [H23–H26](12-agent-runtime-integration-plan.md); browser không được gửi `AgentContextResponse`.

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

| `status` | `case` | Hành vi T03 |
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

- Pydantic envelopes + `extra=forbid`; test reject forbidden keys trên mọi envelope.
- Mọi fixture trên validate được.
- Doc này + index docs; Sprint `H11a` Done → mở `G05` / `T03`.
- Không implement H02 routes hay agent runtime trong H11a (H11b hoàn thiện docs sau build).
