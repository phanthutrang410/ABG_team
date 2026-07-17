# MVP persistence schema — H19/H20

> **Trạng thái:** Draft implementation target. `H19` chỉ bắt đầu sau `H10`; `H20` chỉ bắt đầu sau `H19` + `M06` (do đó đã có M05b/data-owner approval). Tài liệu này không cho phép nạp reference clone, raw export hay dữ liệu synthetic.
>
> **Owner:** Hoàng · **Evidence khi Done:** migration revision, mapping metadata không PII, test DB rỗng/repeatable và import-gate test.

## 1. Quyết định persistence

MVP giữ pattern kỹ thuật `dwh`/ETL versioned của hệ cũ, nhưng **không** migrate schema hoặc row dữ liệu EduInsight cũ. Reference cũ chỉ là ngữ cảnh; MVP dùng một snapshot EPU đã pseudonymize và được data owner duyệt theo [contract EPU](04-epu-data-integration-contract.md).

`H19` tạo schema vật lý rỗng. `H20` là importer nội bộ (CLI/service), không phải FastAPI public endpoint. Không có seed mặc định; khi chưa có snapshot hợp lệ, consumer trả `insufficient_data`.

## 2. Bảng mục tiêu trong `dwh`

| Bảng | Khóa / constraint tối thiểu | Dùng cho | Không được có |
|:--|:--|:--|:--|
| `source_manifest` | `source_id` PK, `snapshot_sha256` unique, `provenance_approved`, `schema_version`, `record_count`, `extracted_at` | Chặn import/đọc snapshot không hợp lệ | token, đường dẫn raw, PII |
| `student_dimension` | `(source_id, student_ref)` PK; FK `source_id` | Scope cohort/khoa/ngành/lớp | MSSV, tên, ngày sinh, email, SĐT |
| `term_grade` | `(source_id, student_ref, term_code, course_ref)` unique; FK snapshot/student | Trend, coverage, factors theo kỳ | raw score model |
| `attendance_event` | `(source_id, student_ref, observed_at, course_ref?)` unique theo contract `H15`; FK snapshot/student | Xu hướng chuyên cần theo thời gian (**MVP**) | Synthetic week, PII, raw score |
| `academic_status` | `(source_id, student_ref)` unique; FK snapshot/student | Evaluation nội bộ của snapshot | Projection vào scoring/public API/agent |
| `advisor_assignment` | `(source_id, student_ref)` unique; FK snapshot/student | Kiểm tra routing sau approve | tên/email/SĐT cố vấn |
| `data_quality_report` | `source_id` FK + version/timestamp report | Missingness, freshness, reject/row count, reason | chi tiết nhận diện sinh viên |

Mọi bảng domain phải scoped bằng `source_id`; không cross-join V59 và `epu_data`. `academic_status.is_dropout_outcome` chỉ là dữ liệu evaluation nội bộ. `attendance_event` mở khi `H15` có export đã duyệt; trước đó schema có thể có bảng rỗng / chưa nạp. Case state/public `ReviewCase` và bảng ML prediction không thuộc migration đầu tiên: chỉ khóa khi `H06a`/`M02` hoàn tất.

## 3. Mapping legacy metadata

| Pattern hệ cũ | Quyết định MVP |
|:--|:--|
| DWH/star schema, ETL idempotent, data-quality log | Kế thừa pattern kỹ thuật cho `dwh`, migration versioned và import repeatable |
| Identity/student profile, contact, token | Loại bỏ hoàn toàn; chỉ nhận `student_ref` pseudonymous |
| Course-risk/raw score/view dự báo cũ | Không migrate; baseline `M02` tự tạo output internal sau này |
| Attendance tuần synthetic / protected group synthetic | Không tạo cột/path từ legacy; điểm danh thật chỉ qua `H15` |

Nếu inventory legacy không có DDL truy cập được, H19 ghi `legacy_schema_unavailable`; không tự suy diễn bảng hoặc nạp reference để bù.

## 4. Import gate của H20

Input được đặt ở vị trí artifact có kiểm soát ngoài repo. H20 chỉ commit migration/code/test và readiness report tối thiểu, không commit export/fixture raw.

Trước transaction, importer phải kiểm tra:

1. M05b approval artifact có owner, quyền sử dụng, snapshot SHA-256 và record count khớp `source_manifest`.
2. Đủ bảng domain điểm cùng `source_id` (+ `attendance_event` khi snapshot `H15` có); không có cross-source join.
3. Schema, primary/unique key, term/grade range, row/reject count và `data_quality_report` hợp lệ.
4. Không có key/value bị cấm: MSSV, tên, ngày sinh, email, SĐT, token, protected group hoặc raw score; không nạp chuỗi điểm danh synthetic/legacy.

Mọi lỗi phải rollback toàn bộ: không partial write. Re-run cùng `source_id`/hash phải idempotent; snapshot khác phải qua approval mới, không overwrite snapshot cũ im lặng.

## 5. Verify và handoff

- DB rỗng migrate được nhiều lần mà không lỗi/không đổi schema.
- Import approved M06 thành công, record/reject count khớp report; rerun không duplicate.
- Approval thiếu, hash/count/schema sai, PII hoặc quality fail → importer reject và DB giữ nguyên.
- H08 chỉ đọc snapshot có provenance/coverage/freshness hợp lệ; thiếu `advisor_ref` tạo trạng thái mapping-repair, không assign/handoff.

Sau H20, H08 cung cấp `NormalizedStudentRecord`/`ScoringFeatures` cho M02. Public API, UI và agent chỉ nhận projection an toàn từ các task sau, không truy cập trực tiếp `dwh`.
