# MVP persistence schema — H19/H20/H30

> **Trạng thái:** `H19`/`H20` Done. `H30` **Done** — Alembic `20260718_h30_snapshot` thêm `dataset_source`, `dataset_snapshot`, `active_dataset_snapshot`, `workflow_run`, `workflow_step_run`; backfill từ `source_manifest` thành snapshot v1 (`legacy_source_id`). Domain rows vẫn keyed by `source_id` (chưa rewrite weekly IDs).
>
> **Owner:** Hoàng · **Evidence:** `tests/test_dwh_migrate.py`, `tests/test_h30_h31_weekly_workflow.py`; CLI `python -m app.dwh.cli weekly run`.
>
> **ERD + catalog cột hiện tại:** [14-database-schema-erd](14-database-schema-erd.md) (SoT vật lý; tài liệu này giữ quyết định thiết kế / import gate).

## 1. Quyết định persistence

MVP giữ pattern kỹ thuật `dwh`/ETL versioned của hệ cũ, nhưng **không** migrate schema hoặc row dữ liệu EduInsight cũ. Reference cũ chỉ là ngữ cảnh; MVP dùng snapshot semester đã duyệt (`M05b`) + điểm danh allowlisted (`H15`) theo [contract EPU](04-epu-data-integration-contract.md) và decision #18.

`H19` tạo schema vật lý rỗng (kể cả bảng `attendance_event`). `H20` là importer nội bộ (CLI/service), không phải FastAPI public endpoint. Không có seed mặc định; khi chưa có snapshot hợp lệ, consumer trả `insufficient_data`.

## 2. Bảng mục tiêu trong `dwh`

| Bảng | Khóa / constraint tối thiểu | Dùng cho | Không được có |
|:--|:--|:--|:--|
| `source_manifest` | `source_id` PK, `snapshot_sha256` unique, `provenance_approved`, `schema_version`, `record_count`, `extracted_at` | Chặn import/đọc snapshot không hợp lệ | token, đường dẫn raw, PII |
| `student_dimension` | `(source_id, student_ref)` PK; FK `source_id` | Scope cohort/khoa/ngành/lớp | MSSV, tên, ngày sinh, email, SĐT |
| `term_grade` | `(source_id, student_ref, term_code, course_ref)` unique; FK snapshot/student | Trend, coverage, factors theo kỳ | raw score model |
| `attendance_event` | `(source_id, student_ref, observed_at, course_ref?)` unique theo contract `H15`; FK snapshot/student | Xu hướng chuyên cần theo thời gian (**MVP**) — nạp từ `mvp-attendance-over-time` sau M06/H20 | Legacy synthetic week, PII, raw score |
| `academic_status` | `(source_id, student_ref)` unique; FK snapshot/student | Evaluation nội bộ của snapshot | Projection vào scoring/public API/agent |
| `advisor_assignment` | `(source_id, student_ref)` unique; FK snapshot/student | Kiểm tra routing sau approve | tên/email/SĐT cố vấn |
| `data_quality_report` | `source_id` FK + version/timestamp report | Missingness, freshness, reject/row count, reason | chi tiết nhận diện sinh viên |

Mọi bảng domain phải scoped bằng `source_id`; không cross-join V59 và `epu_data`. `academic_status.is_dropout_outcome` chỉ là dữ liệu evaluation nội bộ. `attendance_event` **H15 Done** — M06/H20 được nạp từ fixture allowlisted; trước H15 bảng có thể rỗng. Case state/public `ReviewCase` và bảng ML prediction không thuộc migration đầu tiên: chỉ khóa khi `H06a`/`M02` hoàn tất.

## 3. Mapping legacy metadata

| Pattern hệ cũ | Quyết định MVP |
|:--|:--|
| DWH/star schema, ETL idempotent, data-quality log | Kế thừa pattern kỹ thuật cho `dwh`, migration versioned và import repeatable |
| Identity/student profile, contact, token | Loại bỏ hoàn toàn; chỉ nhận `student_ref` pseudonymous |
| Course-risk/raw score/view dự báo cũ | Không migrate; baseline `M02` tự tạo output internal sau này |
| Attendance tuần synthetic / protected group synthetic | Không tạo cột/path từ legacy cấm; điểm danh MVP qua `H15` / `mvp-attendance-over-time` (decision #18) |

Nếu inventory legacy không có DDL truy cập được, H19 ghi `legacy_schema_unavailable`; không tự suy diễn bảng hoặc nạp reference để bù.

**H19 inventory result:** `legacy_schema_unavailable` — reference clone is gitignored (`reference-Learning-Analytics-AI/`) and no accessible legacy DDL/SQL dump was available in-repo for inventory. MVP tables follow this design doc + [EPU contract](04-epu-data-integration-contract.md) only; no legacy rows or schema were copied.

## 4. Import gate của H20

Semester mặc định: package M06 đã pseudonymize `data/approved/semester/domain_package.json` (git). Attendance: `data/approved/attendance/`. Override semester qua `SILENT_SHIELD_SEMESTER_SOURCE_PATH` (raw V59 hoặc package khác). Không commit export V59 raw.

**CLI (không phải FastAPI public endpoint):**

```text
python -m app.dwh.cli import-attendance
python -m app.dwh.cli import-semester
python -m app.dwh.cli readiness
```

Trước transaction, `import_gate` kiểm tra:

1. Approval artifact (M05b/H15) có owner, quyền sử dụng, snapshot SHA-256 và record count khớp bytes nguồn.
2. Domain package M06 đủ bảng theo role (`primary` / `attendance`); cùng `source_id`; không cross-source join. Attendance tạo stub `student_dimension` dưới `mvp-attendance-over-time` trước khi insert events.
3. Schema manifest + `data_quality_report` (row/reject count) hợp lệ.
4. Domain payload không có key PII/token; không nạp marker `"synthetic"` / source ngoài allowlist.

Mọi lỗi → zero write (không mở transaction ghi, hoặc rollback). Re-run cùng `source_id`+hash → `idempotent_skip`; hash khác trên cùng `source_id` → reject (không overwrite im lặng).

## 5. Verify và handoff

- DB rỗng migrate được nhiều lần mà không lỗi/không đổi schema.
- Import approved M06 thành công, record/reject count khớp report; rerun không duplicate.
- Approval thiếu, hash/count/schema sai, PII hoặc quality fail → importer reject và DB giữ nguyên.
- H08 chỉ đọc snapshot có provenance/coverage/freshness hợp lệ; thiếu `advisor_ref` tạo trạng thái mapping-repair, không assign/handoff.

Sau H20, H08 cung cấp `NormalizedStudentRecord`/`ScoringFeatures` cho M02. Public API, UI và agent chỉ nhận projection an toàn từ các task sau, không truy cập trực tiếp `dwh`.
