# Database schema & ERD — Silent Shield MVP

> **Trạng thái:** SoT vật lý cho PostgreSQL schemas `dwh` + `app` tại migrations `20260718_h19_dwh` → `20260718_h30_snapshot` → `20260719_h39a_auth_rbac` → `20260719_ml_attendance_week`.
>
> **Nguồn code:** `backend/app/dwh/models.py`, `backend/app/auth/models.py` · **Migrations:** `backend/alembic/versions/` · **Thiết kế/import gate:** [07-mvp-persistence-schema](07-mvp-persistence-schema.md).
>
> Khi prose và ORM lệch nhau, ưu tiên migration đã apply + models; cập nhật tài liệu này trong cùng handoff.

## 1. Phạm vi

| Có trong Postgres | Chưa có bảng Postgres (in-memory / process-local) |
|:--|:--|
| **`dwh`** Domain snapshot (điểm, điểm danh event + week rollup, advisor, quality) | Care `ReviewCase` / `CaseStore` (`app.cases.store`) |
| **`dwh`** `ml_term_snapshot` (features + band; CLI `materialize-ml`) | Weekly durable cases/events H33a (`app.weekly.cases_durable`) |
| **`dwh`** Snapshot registry H30 (`dataset_*`, `active_dataset_snapshot`) | Weekly report / briefing / receipts (`app.weekly.state`) |
| **`dwh`** Workflow ledger H30 (`workflow_run`, `workflow_step_run`) | — |
| **`app`** Auth RBAC H39 (`auth_account`, `auth_account_role`, `auth_session`, `access_audit_event`) | — |

**H39 không đổi dữ liệu học vụ `dwh`.** Engine: **PostgreSQL** qua `DATABASE_URL`. Alembic version table nằm trong schema `dwh`. Public API/UI/agent **không** query trực tiếp `dwh`; đọc qua H08 adapter và projection an toàn. Identity SoT = cookie `ss_session` → `app.auth_session`.

## 1b. ERD schema `app` (H39)

```mermaid
erDiagram
  auth_account ||--o{ auth_account_role : actor_id
  auth_account ||--o{ auth_session : actor_id

  auth_account {
    string actor_id PK
    string username UK
    string display_name
    string password_hash
    string org_scope
    string advisor_scope
    bool is_active
  }

  auth_account_role {
    string actor_id PK_FK
    string role PK
  }

  auth_session {
    string session_id PK
    string actor_id FK
    string token_hash UK
    string active_role
    timestamptz expires_at
    timestamptz revoked_at
  }

  access_audit_event {
    int id PK
    string actor_id
    string role
    string action
    string resource_handle
    string decision
    timestamptz at
  }
```

Role CHECK: `ban_quan_ly|gvcn` only. Seed accounts via `python -m app.auth.cli seed` (not in migration).

## 2. ERD tổng quan (`dwh`)

```mermaid
erDiagram
  source_manifest ||--o{ student_dimension : "source_id"
  source_manifest ||--o{ data_quality_report : "source_id"
  student_dimension ||--o{ term_grade : "source_id+student_ref"
  student_dimension ||--o{ attendance_event : "source_id+student_ref"
  student_dimension ||--o{ attendance_week : "source_id+student_ref"
  student_dimension ||--o{ academic_status : "source_id+student_ref"
  student_dimension ||--o{ advisor_assignment : "source_id+student_ref"
  student_dimension ||--o{ ml_term_snapshot : "source_id+student_ref"

  dataset_source ||--o{ dataset_snapshot : "dataset_key"
  dataset_source ||--|| active_dataset_snapshot : "dataset_key"
  dataset_snapshot ||--o| active_dataset_snapshot : "snapshot_id"
  workflow_run ||--o{ workflow_step_run : "run_id"

  source_manifest {
    string source_id PK
    string snapshot_sha256 UK
    bool provenance_approved
    string schema_version
    int record_count
    timestamptz extracted_at
  }

  student_dimension {
    string source_id PK_FK
    string student_ref PK
    string cohort
    string department
    string program
    string major
    string class_code
  }

  term_grade {
    string source_id PK_FK
    string student_ref PK_FK
    string term_code PK
    string course_ref PK
    numeric credits
    numeric final_grade
    string grade_status
  }

  attendance_event {
    string source_id PK_FK
    string student_ref PK_FK
    timestamptz observed_at PK
    string course_ref PK
    string presence_status
    bool excused
  }

  attendance_week {
    string source_id PK_FK
    string student_ref PK_FK
    date week_start_date PK
    date week_end_date
    int n_events
    int n_in_denominator
    int n_present
    numeric attendance_rate
  }

  academic_status {
    string source_id PK_FK
    string student_ref PK_FK
    string status_code
    timestamptz status_observed_at
    string is_dropout_outcome
  }

  advisor_assignment {
    string source_id PK_FK
    string student_ref PK_FK
    string advisor_ref
    string scope_source
  }

  ml_term_snapshot {
    string source_id PK_FK
    string student_ref PK_FK
    string model_version
    string review_priority_band
    numeric latest_term_gpa
    string coverage_status
    text agent_explain_json
  }

  data_quality_report {
    int report_id PK
    string source_id FK
    string report_version
    timestamptz generated_at
    int row_count
    int reject_count
  }

  dataset_source {
    string dataset_key PK
    string source_owner
    string retention_policy
    text usage_notes
  }

  dataset_snapshot {
    string snapshot_id PK
    string dataset_key FK
    string dataset_content_sha256
    string legacy_source_id
    string status
  }

  active_dataset_snapshot {
    string dataset_key PK_FK
    string snapshot_id FK
    timestamptz promoted_at
  }

  workflow_run {
    string run_id PK
    string dataset_key
    string snapshot_id
    string status
    string idempotency_key
  }

  workflow_step_run {
    int step_run_id PK
    string run_id FK
    string step_name
    string status
  }
```

### 2.1 Hai cụm logic

```mermaid
flowchart TB
  subgraph Domain["Domain rows — keyed by source_id (H19/H20)"]
    SM[source_manifest]
    SD[student_dimension]
    TG[term_grade]
    AE[attendance_event]
    AW[attendance_week]
    AS[academic_status]
    AA[advisor_assignment]
    ML[ml_term_snapshot]
    DQR[data_quality_report]
    SM --> SD
    SM --> DQR
    SD --> TG
    SD --> AE
    SD --> AW
    SD --> AS
    SD --> AA
    SD --> ML
  end

  subgraph Registry["Snapshot registry + workflow — H30"]
    DSrc[dataset_source]
    DSnap[dataset_snapshot]
    Active[active_dataset_snapshot]
    WR[workflow_run]
    WSR[workflow_step_run]
    DSrc --> DSnap
    DSrc --> Active
    DSnap --> Active
    WR --> WSR
  end

  SM -. "H30 backfill: legacy_source_id = source_id" .-> DSnap
```

Domain rows **chưa** rewrite sang `snapshot_id`; bridge tạm qua `dataset_snapshot.legacy_source_id` ↔ `source_manifest.source_id`. Không cross-join hai `source_id` khác nhau (ví dụ V59 vs `mvp-attendance-over-time`).

## 3. Catalog bảng

### 3.1 `dwh.source_manifest`

Gate provenance cho mỗi import snapshot.

| Cột | Kiểu | Null | Ghi chú |
|:--|:--|:--:|:--|
| `source_id` | `varchar(128)` | PK | Logical source (vd. semester package / attendance allowlist) |
| `snapshot_sha256` | `varchar(64)` | N | Unique; đúng 64 ký tự |
| `provenance_approved` | `boolean` | N | Phải true để consumer đọc |
| `schema_version` | `varchar(64)` | N | |
| `record_count` | `integer` | N | `>= 0` |
| `extracted_at` | `timestamptz` | N | |

### 3.2 `dwh.student_dimension`

Cohort scope — chỉ `student_ref` pseudonymous; **không** MSSV/tên/email/SĐT.

| Cột | Kiểu | Null | Ghi chú |
|:--|:--|:--:|:--|
| `source_id` | `varchar(128)` | PK, FK → `source_manifest` CASCADE | |
| `student_ref` | `varchar(128)` | PK | |
| `cohort` | `varchar(64)` | Y | |
| `department` | `varchar(128)` | Y | |
| `program` | `varchar(128)` | Y | |
| `major` | `varchar(128)` | Y | |
| `class_code` | `varchar(64)` | Y | |

### 3.3 `dwh.term_grade`

Điểm theo kỳ / môn.

| Cột | Kiểu | Null | Ghi chú |
|:--|:--|:--:|:--|
| `source_id` + `student_ref` | | PK, FK → `student_dimension` CASCADE | |
| `term_code` | `varchar(32)` | PK | |
| `course_ref` | `varchar(128)` | PK | |
| `credits` | `numeric(6,2)` | Y | |
| `final_grade` | `numeric(5,2)` | Y | |
| `grade_status` | `varchar(64)` | Y | |

### 3.4 `dwh.attendance_event`

Sự kiện chuyên cần theo thời gian (MVP: `mvp-attendance-over-time`).

| Cột | Kiểu | Null | Ghi chú |
|:--|:--|:--:|:--|
| `source_id` + `student_ref` | | PK, FK → `student_dimension` CASCADE | |
| `observed_at` | `timestamptz` | PK | |
| `course_ref` | `varchar(128)` | PK | Default `''` khi thiếu grain môn |
| `presence_status` | `varchar(32)` | Y | |
| `excused` | `boolean` | Y | |

### 3.4b `dwh.attendance_week`

Rollup chuyên cần **student × ISO week** (Monday = `week_start_date`). Derive từ `attendance_event`; ghi qua CLI `rollup-attendance-week` (`app.dwh.attendance_week_rollup`).

| Cột | Kiểu | Null | Ghi chú |
|:--|:--|:--:|:--|
| `source_id` + `student_ref` | | PK, FK → `student_dimension` CASCADE | |
| `week_start_date` | `date` | PK | Monday của tuần ISO |
| `week_end_date` | `date` | N | ≥ `week_start_date` |
| `n_events` | `integer` | N | Tổng event trong tuần |
| `n_in_denominator` | `integer` | N | Non-excused có `presence_status` |
| `n_present` / `n_absent` | `integer` | N | Trong mẫu số |
| `n_excused_excluded` | `integer` | N | `excused=true` — không vào mẫu số |
| `attendance_rate` | `numeric(6,4)` | Y | null khi `n_in_denominator=0` |
| `first_observed_at` / `last_observed_at` | `timestamptz` | Y | |

### 3.5 `dwh.academic_status`

Evaluation nội bộ của snapshot — **không** project vào scoring / public API / agent.

| Cột | Kiểu | Null | Ghi chú |
|:--|:--|:--:|:--|
| `source_id` + `student_ref` | | PK, FK → `student_dimension` CASCADE | |
| `status_code` | `varchar(64)` | Y | |
| `status_observed_at` | `timestamptz` | Y | |
| `is_dropout_outcome` | `varchar(16)` | N | Check: `true` \| `false` \| `unknown` |

### 3.6 `dwh.advisor_assignment`

Routing sau approve; chỉ `advisor_ref` pseudonymous.

| Cột | Kiểu | Null | Ghi chú |
|:--|:--|:--:|:--|
| `source_id` + `student_ref` | | PK, FK → `student_dimension` CASCADE | |
| `advisor_ref` | `varchar(128)` | Y | Thiếu → mapping-repair, không handoff |
| `scope_source` | `varchar(128)` | Y | |

### 3.6b `dwh.ml_term_snapshot`

Materialize M02 `ScoringFeatures` + nhãn ưu tiên rà soát theo snapshot semester (`source_id`). Một hàng / SV; upsert khi re-score. Ghi qua CLI `materialize-ml` (`app.dwh.ml_materializer`).

| Cột | Kiểu | Null | Ghi chú |
|:--|:--|:--:|:--|
| `source_id` + `student_ref` | | PK, FK → `student_dimension` CASCADE | |
| `dataset_version` / `model_version` / `threshold_config_version` | `varchar` | N | Data-ML §1 |
| `calculated_at` | `timestamptz` | N | |
| `last_term_code` | `varchar(32)` | Y | Neo kỳ học của snapshot |
| `latest_term_gpa` … `attendance_trend_slope` | `numeric` | Y | Features Data-ML §2 |
| `coverage_status` | `varchar(32)` | N | `ok` \| `partial` \| `insufficient` |
| `coverage_json` | `text` | N | Full Coverage envelope |
| `review_priority_band` | `varchar(32)` | Y | `uu_tien_som` \| `can_ra_soat` \| null dưới τ |
| `contributing_factors_json` | `text` | N | Default `[]` |
| `model_score` | `numeric(6,4)` | Y | **Nội bộ only** — cấm project API/agent |
| `explain_schema_version` | `varchar(64)` | Y | Version shape `agent_explain_json` |
| `agent_explain_json` | `text` | Y | Payload an toàn linh hoạt cho bot |
| `evidence_fingerprint` | `varchar(128)` | Y | Delta / reconcile |

### 3.7 `dwh.data_quality_report`

| Cột | Kiểu | Null | Ghi chú |
|:--|:--|:--:|:--|
| `report_id` | `integer` | PK identity | |
| `source_id` | `varchar(128)` | FK CASCADE | |
| `report_version` | `varchar(64)` | N | |
| `generated_at` | `timestamptz` | N | Unique cùng `(source_id, report_version, generated_at)` |
| `row_count` / `reject_count` | `integer` | N | `>= 0` |
| `missingness_summary` | `text` | Y | |
| `term_coverage_summary` | `text` | Y | |
| `freshness_summary` | `text` | Y | |
| `reason_codes` | `text` | Y | |

### 3.8 `dwh.dataset_source` (H30)

Registry logical dataset.

| Cột | Kiểu | Null | Ghi chú |
|:--|:--|:--:|:--|
| `dataset_key` | `varchar(128)` | PK | Thường = `source_id` sau backfill H30 |
| `source_owner` | `varchar(128)` | Y | |
| `retention_policy` | `varchar(128)` | Y | |
| `usage_notes` | `text` | Y | |

### 3.9 `dwh.dataset_snapshot` (H30)

Snapshot bất biến, multi-version.

| Cột | Kiểu | Null | Ghi chú |
|:--|:--|:--:|:--|
| `snapshot_id` | `varchar(128)` | PK | Backfill: `snap-v1-{source_id}` |
| `dataset_key` | `varchar(128)` | FK CASCADE | |
| `previous_snapshot_id` / `supersedes_snapshot_id` | `varchar(128)` | Y | Chưa FK cứng |
| `period_start` / `period_end` | `varchar(32)` | Y | |
| `extracted_at` | `timestamptz` | N | |
| `delivered_at` | `timestamptz` | Y | |
| `schema_version` | `varchar(64)` | N | |
| `pseudonym_namespace_version` | `varchar(64)` | N | |
| `source_snapshot_sha256` | `varchar(64)` | N | Len 64 |
| `normalized_artifact_sha256` | `varchar(64)` | Y | |
| `dataset_content_sha256` | `varchar(64)` | N | Unique với `dataset_key` |
| `approval_id` | `varchar(128)` | Y | |
| `provenance_approved` | `boolean` | N | |
| `fixture_mode` | `varchar(64)` | Y | vd. `legacy_source_manifest` |
| `legacy_source_id` | `varchar(128)` | Y | Bridge tới domain `source_id` |
| `row_counts_json` | `text` | Y | |
| `quality_reason_codes` | `text` | Y | |
| `status` | `varchar(32)` | N | `staged` \| `active` \| `superseded` \| `rejected` |

### 3.10 `dwh.active_dataset_snapshot` (H30)

Pointer atomic: một active snapshot / `dataset_key`.

| Cột | Kiểu | Null | Ghi chú |
|:--|:--|:--:|:--|
| `dataset_key` | `varchar(128)` | PK, FK CASCADE | |
| `snapshot_id` | `varchar(128)` | FK RESTRICT | |
| `promoted_at` | `timestamptz` | N | |
| `promoted_by_run_id` | `varchar(128)` | Y | |

### 3.11 `dwh.workflow_run` (H30)

Ledger chạy weekly workflow.

| Cột | Kiểu | Null | Ghi chú |
|:--|:--|:--:|:--|
| `run_id` | `varchar(128)` | PK | |
| `dataset_key` | `varchar(128)` | N | Không FK cứng |
| `snapshot_id` | `varchar(128)` | Y | Không FK cứng |
| `trigger_kind` | `varchar(64)` | N | Default runtime: `cli` |
| `idempotency_key` | `varchar(256)` | N | Unique với `(dataset_content_sha256, workflow_version)` |
| `workflow_version` | `varchar(64)` | N | |
| `model_version` / `threshold_config_version` | `varchar(64)` | Y | |
| `dataset_content_sha256` | `varchar(64)` | N | |
| `status` | `varchar(32)` | N | Xem check bên dưới |
| `failure_reason_code` | `varchar(128)` | Y | |
| `replay_of_run_id` | `varchar(128)` | Y | |
| `started_at` / `finished_at` | `timestamptz` | Y | |

`status` ∈ `queued`, `validating`, `staging`, `scoring`, `reconciling`, `reporting`, `publishing`, `succeeded`, `failed`, `duplicate`.

### 3.12 `dwh.workflow_step_run` (H30)

| Cột | Kiểu | Null | Ghi chú |
|:--|:--|:--:|:--|
| `step_run_id` | `integer` | PK identity | |
| `run_id` | `varchar(128)` | FK CASCADE | Unique với `step_name` |
| `step_name` | `varchar(64)` | N | |
| `status` | `varchar(32)` | N | `queued` \| `running` \| `succeeded` \| `failed` \| `skipped` |
| `reason_code` | `varchar(128)` | Y | |
| `started_at` / `finished_at` | `timestamptz` | Y | |

## 4. Migration chain

| Revision | Tạo / đổi |
|:--|:--|
| `20260718_h19_dwh` | Schema `dwh` + 7 bảng domain (rỗng, không seed) |
| `20260718_h30_snapshot` | 5 bảng registry/workflow; backfill `source_manifest` → `dataset_source` + `dataset_snapshot` + `active_dataset_snapshot` |

```powershell
Push-Location backend
alembic upgrade head
Pop-Location
```

Import / materialize (không phải public API): xem [07 §4](07-mvp-persistence-schema.md) — `python -m app.dwh.cli import-semester` / `import-attendance` / `readiness` / `materialize-ml` / `rollup-attendance-week` / `weekly run`.

## 5. Ràng buộc privacy / care

- Chỉ `student_ref` / `advisor_ref` / `course_ref` pseudonymous; không cột PII, token, đường dẫn raw.
- `is_dropout_outcome` và audit-group attributes không vào scoring hay public case API.
- Domain scoped theo `source_id`; thiếu provenance/coverage/freshness → consumer `insufficient_data`, không suy luận.
- Case transition và LLM state **không** nằm trong schema này.

## 6. Gap đã biết (không claim đã ship)

| Gap | Hệ quả |
|:--|:--|
| Domain rows chưa keyed by `snapshot_id` | Lịch sử tuần nhiều version trên cùng logical source còn hạn chế |
| `workflow_run.dataset_key` / `snapshot_id` chưa FK | Ledger lỏng hơn registry; enforce ở application |
| `ml_term_snapshot` / `attendance_week` writer | **Done** — CLI `materialize-ml` / `rollup-attendance-week`; H02 prefer snapshot via `ml_snapshot_reader` |
| `list_attendance_weeks` reader | **Done** (D460-12) — helper; no dedicated public week API yet |
| Care `app.review_case` / `app.case_event` | **Done** (D460-08) — Alembic `20260719_care_case_store`; `PostgresCaseStore` |
| Weekly `CaseRepository` (H33a) | Vẫn in-memory process-local (D460-09 deferred) — weekly episode mất khi restart |
| Live linked attendance | **Done** — Live `:d460` + bootstrap · [23-d460…](../03-project/23-d460-live-redeploy-evidence.md) · Vercel FE `/auth` redeploy còn lại |

Target còn lại: weekly episode DB; `signal_observation` table nếu cần immutable ledger — [doc 13](13-weekly-snapshot-global-agent-architecture.md).

## 7. Verify liên quan

- `tests/test_dwh_migrate.py` — migrate rỗng / schema ổn định
- `tests/test_h20_import.py` — import gate
- `tests/test_h30_h31_weekly_workflow.py` — registry + workflow ledger

Cần Postgres local (`DATABASE_URL` / `TEST_DATABASE_URL`); test skip nếu DB không sẵn.
