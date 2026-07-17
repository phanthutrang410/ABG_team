# Hợp đồng tích hợp dữ liệu EPU — giao Hoàng

> **Trạng thái:** Contract mục tiêu cho M05–M06, H19–H20 và H08; chưa đồng nghĩa dữ liệu nguồn đã được duyệt để deploy. Nguồn trường: [catalog EPU](03-epu-reference-data-fields.md). Không commit reference-Learning-Analytics-AI/, raw export, PII hay mapping danh tính vào repo.

## 1. Quyết định và phạm vi

Silent Shield không dùng hoặc sinh dữ liệu synthetic. Pipeline chỉ nhận bản trích xuất EPU/điểm danh đã được data owner phê duyệt, pseudonymize và kiểm tra theo contract này. Điểm danh theo thời gian thuộc MVP (`H15`). Khi thiếu một nguồn hay một điều kiện chất lượng, API trả `insufficient_data`; không tạo chuỗi tuần, nhãn outcome, thuộc tính fairness hoặc mapping GVCN giả.

Các ứng viên đã quan sát trong reference local:

| Ứng viên | Tận dụng được sau data gate | Không được suy ra | Vai trò dự kiến |
|:--|:--|:--|:--|
| `v59-empty-program-students.json` | 460 hồ sơ; `Trạng thái`, 8 điểm môn/SV ở HK1–HK2 2022–2023, khoa/lớp/ngành, `Cố vấn học tập` | Chuỗi điểm danh theo thời gian (catalog hiện thiếu), email GVCN, lịch sử dài hơn hai kỳ | Primary cho slice điểm theo kỳ + routing sau pseudonymization |
| Export điểm danh (sau `H15`) | Chuỗi chuyên cần theo buổi/ngày/tuần đã duyệt + provenance | Synthetic week, PII, nghỉ có phép chưa xác nhận | **MVP** — nguồn `attendance_event` / CORE-03 |
| `epu_data.json` | 20 hồ sơ; bảng điểm 20–66 môn/SV, nhiều học kỳ | GVCN, cỡ mẫu/evaluation đáng tin, join sang V59 | Regression fixture/kiểm tra transform, không trộn hồ sơ với V59 |

Loại khỏi pipeline: `v59-synthetic-students.json`, `synthetic_student_profile_replacements.json`, `synthetic-transcript-coverage-v5.json` và mọi dữ liệu/generator synthetic mới. Tên file không chứng minh provenance: M05 phải ghi owner, quyền sử dụng, hash snapshot và kết quả duyệt trước khi chọn một ứng viên.

## 2. Nguồn → schema thống nhất

M06 xuất một dataset tách bảng logic, có cùng `student_ref` pseudonymous trong **một** source snapshot. Không join `MSSV` giữa `epu_data` và V59; snapshot hiện tại có 0 mã giao nhau.

| Bảng logic | Khóa / trường tối thiểu | Nguồn | Dùng bởi Hoàng |
|:--|:--|:--|:--|
| `source_manifest` | `source_id`, `snapshot_sha256`, `extracted_at`, `provenance_approved`, `schema_version`, `record_count` | M05 | Chặn import khi thiếu approval/hash |
| `student_dimension` | `student_ref`, `cohort`, `department`, `program`, `major`, `class_code` | `student_info` | List/filter/case scope; không có tên, MSSV, ngày sinh, email, SĐT |
| `term_grade` | `student_ref`, `term_code`, `course_ref`, `credits`, `final_grade`, `grade_status` | `grades[]` | Trend/coverage theo kỳ và contributing factors |
| `attendance_event` | `student_ref`, `observed_at` (hoặc period đã duyệt), `presence_status`, `excused` (nếu có), `course_ref` (nếu có) | Export điểm danh sau `H15` | Xu hướng chuyên cần theo thời gian — **MVP** |
| `academic_status` | `student_ref`, `status_code`, `status_observed_at`, `is_dropout_outcome` | `student_info.Trạng thái` | Nhãn evaluation nội bộ; không public qua case API |
| `advisor_assignment` | `student_ref`, `advisor_ref`, `scope_source` | `Cố vấn học tập` | Chỉ routing sau human approval; không email/SĐT |
| `data_quality_report` | source, row counts, reject counts, missingness, term coverage, freshness, reason | M06 | Trả `insufficient_data` có lý do |

`student_ref` là mã pseudonym sinh trong môi trường nhập có kiểm soát. Bảng liên kết `MSSV` ↔ `student_ref` không được xuất sang repo, fixture, log, API public, slide hoặc video. `advisor_ref` cũng không phải tên hay địa chỉ liên hệ.

## 3. Quy tắc chuẩn hóa và kiểm tra

1. Đọc UTF-8; trim, chuẩn hóa Unicode và giá trị rỗng trước khi parse số. Lưu `source_id`/hash, không lưu `token` crawl.
2. Chuẩn hóa `Học kỳ` như `HK1 (2022-2023)` thành `2022-2023-T1`; một bản ghi điểm chỉ hợp lệ khi có `student_ref`, `term_code`, `course_ref` và điểm số trong miền đã công bố.
3. Map `Trạng thái`: `Thôi học` và `Buộc thôi học` → `is_dropout_outcome=true`; `Đang học` → `false`; giá trị khác → `unknown` cho tới khi owner chốt. Outcome chỉ dùng trong test/evaluation của source snapshot, không biến thành nhãn trên UI.
4. Không tạo `attendance_event`/chuỗi tuần, nhóm kinh tế/dân tộc hay email GVCN khi source không cấp. Thiếu field là trạng thái dữ liệu → `insufficient_data`; sau `H15` thì nạp theo schema đã duyệt, không bù bằng heuristic/synthetic.
5. Chỉ tính trend điểm khi một `student_ref` có tối thiểu hai `term_code` hợp lệ. Trend chuyên cần chỉ khi có đủ mốc `attendance_event` theo contract `H15`. Nguồn chỉ có một kỳ, status unknown, grade lỗi/quá cũ, thiếu điểm danh đã duyệt, hoặc mapping GVCN thiếu phải sinh reason `insufficient_data` đúng nhánh.
6. Fairness chỉ chạy khi có thuộc tính audit đã được phê duyệt, nhãn outcome, cỡ mẫu/mẫu số và định nghĩa nhóm. Hiện catalog không có thuộc tính này; contract trả `insufficient_data`, không dùng proxy ngành/giới tính.

## 4. Handoff cho Hoàng

Trước khi Hoàng nối API, Khánh Duy bàn giao một fixture đã validate và bốn artifact sau:

1. `source_manifest.json` và `data_quality_report.json` không có PII;
2. dataset chuẩn hóa hoặc fixture gồm bảng domain điểm (`student_dimension`, `term_grade`, `academic_status`, `advisor_assignment`) **và** `attendance_event` khi `H15` sẵn sàng + hai artifact meta ở mục (1), dùng `student_ref`/`advisor_ref`;
3. data dictionary: nguồn field, nullable semantics, taxonomy `Trạng thái`, snapshot hash và giới hạn coverage;
4. test kết quả: row count/reject count, uniqueness khóa, valid term/grade, cấm PII/token và expected `insufficient_data`.

**M05a** (build source gate) khác **M05b** (approved source available): H10/M05a Done không đồng nghĩa snapshot đã được data owner duyệt. M06 chỉ chạy khi có artifact duyệt ở M05b.

`H19` tạo persistence `dwh` từ [schema vật lý MVP](07-mvp-persistence-schema.md) trên DB rỗng; chỉ mapping metadata của DWH legacy, không copy schema/row/reference cũ. `H20` nạp fixture M06 vào transaction sau khi kiểm tra M05b; `H08` mới đọc `dwh` thành `NormalizedStudentRecord`/`ScoringFeatures`.

Hoàng nhận input `NormalizedStudentRecord`/`ScoringFeatures` chỉ gồm pseudonymous ID, feature điểm theo kỳ, feature chuyên cần theo thời gian (khi có), coverage/freshness và provenance. `academic_status.is_dropout_outcome`, raw `MSSV`, tên, email, SĐT, `Cố vấn học tập` gốc và field fairness không nằm trong scoring public, `ReviewCase`, hay agent context — outcome chỉ evaluation nội bộ.

## 5. Persistence và import có kiểm soát

- `H19` tạo bảng `dwh` versioned cho domain điểm + `source_manifest`/`data_quality_report`, và sẵn sàng mở rộng `attendance_event` theo `H15`; DB khởi tạo rỗng và migration có thể chạy lại an toàn.
- Không có cột hay import path MVP cho `MSSV`, tên, email, SĐT, token, thuộc tính nhóm, raw score hay mapping định danh. Điểm danh chỉ qua path đã duyệt (`H15`), không synthetic.
- `H20` chỉ đọc artifact M06 ở vị trí ngoài repo được kiểm soát. Thiếu approval, hash/count/schema lệch, PII/token, cross-source join hoặc quality gate fail phải rollback toàn bộ.
- `H20` không phải public API endpoint và không dùng V59/`epu_data`/synthetic reference làm seed thay thế.

## 6. Acceptance cho M05–M06, H19–H20 và H08

- M05a có source register/gate với lựa chọn/loại từng file, hash, record count và PII exclusion list (code/tests).
- M05b có artifact duyệt của data owner (owner, quyền sử dụng, snapshot hash); thiếu approval thì không coi nguồn “ready” cho M06.
- M06 tạo cùng một output từ cùng snapshot hai lần với hash/row count như nhau; fixture = 4 bảng domain + `source_manifest` + `data_quality_report`; không chứa PII/token, không cross-join source và validate theo schema.
- H19 migrate DB rỗng/repeatable; evidence gồm revision + mapping metadata không PII.
- H20 chứng minh import atomic/idempotent: hash/count/schema hoặc approval lỗi thì không ghi hàng nào; fixture đạt gate mới được nạp vào `dwh`.
- H08 đọc snapshot đã nạp, phân biệt `insufficient_data` với “ổn định”, và chỉ route khi `advisor_ref` hiện diện (thiếu → mapping-repair queue).
- M03/FR-09 chỉ trả fairness metric nếu data gate ở mục 3.6 đạt; nếu không, UI/API ghi rõ audit chưa đủ dữ liệu.
