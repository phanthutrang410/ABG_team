# Hợp đồng tích hợp dữ liệu EPU — Silent Shield (H10)

> **Owner:** Hoàng · **Task:** H10 · **Trạng thái:** Contract nguồn chuẩn cho M05–M06, H19–H20 và H08. **M05b + H15 Done** theo [decision #18](../03-project/04-decisions.md) (team approver MVP demo). Nguồn trường: [catalog EPU](03-epu-reference-data-fields.md). Scoring/fairness: [08 Data-ML](08-data-ml-scoring-fairness-contract.md). Không commit reference-Learning-Analytics-AI/, raw V59, PII hay mapping danh tính vào repo.

## 1. Quyết định và phạm vi

Pipeline nhận snapshot semester đã duyệt (`M05b`) và nguồn điểm danh allowlisted (`H15`), qua source gate (hash/count/PII/allowlist). Legacy synthetic đã liệt kê vẫn **cấm**. Khi thiếu coverage/freshness, API trả `insufficient_data`; không impute 0.

**Source gate ≠ approved data (lịch sử):** `M05a` (code gate) Done ≠ dữ liệu đã duyệt. Duyệt MVP demo: [14-m05b…](../03-project/14-m05b-semester-approval.md) + [12-h15…](../03-project/12-h15-attendance-approval-prep.md) (decision #18).

| Ứng viên | Tận dụng được sau data gate | Không được suy ra | Vai trò |
|:--|:--|:--|:--|
| `v59-empty-program-students` (ngoài git) | 460 hồ sơ; điểm HK1–HK2 2022–2023; khoa/lớp/ngành; cố vấn | Chuỗi điểm danh theo thời gian trong file này | **Primary semester** — `M05b` approved |
| `mvp-attendance-over-time` (fixture repo) | `attendance_event` pseudonymous; ≥4 mốc/`student_ref` trong cửa sổ | PII, map MSSV | **Primary attendance** — `H15` Done |
| `epu_data` | Regression transform | Trộn hồ sơ với V59 | Regression only |

Loại khỏi pipeline: `v59-synthetic-students.json`, `synthetic_student_profile_replacements.json`, `synthetic-transcript-coverage-v5.json` và payload chứa marker `"synthetic"`. Allowlist gate: `v59-empty-program-students`, `epu_data`, `mvp-attendance-over-time`.

## 2. Nguồn → schema thống nhất

M06 xuất một dataset tách bảng logic, có cùng `student_ref` pseudonymous trong **một** source snapshot. Không join `MSSV` giữa `epu_data` và V59; snapshot hiện tại có 0 mã giao nhau.

| Bảng logic | Khóa / trường tối thiểu | Nguồn | Dùng bởi Hoàng |
|:--|:--|:--|:--|
| `source_manifest` | `source_id`, `snapshot_sha256`, `extracted_at`, `provenance_approved`, `schema_version`, `record_count` | M05 | Chặn import khi thiếu approval/hash |
| `student_dimension` | `student_ref`, `cohort`, `department`, `program`, `major`, `class_code` | `student_info` | List/filter/case scope; không có tên, MSSV, ngày sinh, email, SĐT |
| `term_grade` | `student_ref`, `term_code`, `course_ref`, `credits`, `final_grade`, `grade_status` | `grades[]` | Trend/coverage theo kỳ và contributing factors |
| `attendance_event` | `student_ref`, `observed_at` (hoặc period đã duyệt), `presence_status`, `excused` (nếu có), `course_ref` (nếu có) | `mvp-attendance-over-time` (`H15` Done) | Xu hướng chuyên cần theo thời gian — **MVP** |
| `academic_status` | `student_ref`, `status_code`, `status_observed_at`, `is_dropout_outcome` | `student_info.Trạng thái` | Nhãn evaluation nội bộ; không public qua case API |
| `advisor_assignment` | `student_ref`, `advisor_ref`, `scope_source` | `Cố vấn học tập` | Chỉ routing sau human approval; không email/SĐT |
| `data_quality_report` | source, row counts, reject counts, missingness, term coverage, freshness, reason | M06 | Trả `insufficient_data` có lý do |

`student_ref` là mã pseudonym sinh trong môi trường nhập có kiểm soát. Bảng liên kết `MSSV` ↔ `student_ref` không được xuất sang repo, fixture, log, API public, slide hoặc video. `advisor_ref` cũng không phải tên hay địa chỉ liên hệ.

## 3. Quy tắc chuẩn hóa và kiểm tra

1. Đọc UTF-8; trim, chuẩn hóa Unicode và giá trị rỗng trước khi parse số. Lưu `source_id`/hash, không lưu `token` crawl.
2. Chuẩn hóa `Học kỳ` như `HK1 (2022-2023)` thành `2022-2023-T1`; một bản ghi điểm chỉ hợp lệ khi có `student_ref`, `term_code`, `course_ref` và điểm số trong miền đã công bố.
3. **Taxonomy `Trạng thái` (H10 / decision #17):**

| Giá trị nguồn | `status_code` (chuẩn hóa) | `is_dropout_outcome` | Ghi chú |
|:--|:--|:--|:--|
| `Thôi học`, `Buộc thôi học` | giữ nghĩa tương ứng | `true` | Positive evaluation nội bộ |
| `Đang học` | `dang_hoc` | `false` | Mẫu số FPR |
| `Rút học phí` | `rut_hoc_phi` | `unknown` | **Không** gộp vào positive; loại khỏi mẫu số |
| `Bảo lưu` | `bao_luu` | `unknown` | Không mặc định = dropout; loại khỏi mẫu số |
| Khác / thiếu | `other` / thiếu | `unknown` | Loại khỏi mẫu số |

Outcome chỉ dùng trong test/evaluation của source snapshot; **không** vào `ScoringFeatures`, public `ReviewCase`, hay agent context.

4. **Pseudonym custody (H10):** `student_ref` / `advisor_ref` sinh trong môi trường nhập có kiểm soát. Bảng map `MSSV`↔`student_ref` (và tên cố vấn↔`advisor_ref`) lưu **ngoài repo**, path cấu hình env (không commit). Quyền giữ: **data owner** (phê duyệt) + **Admin kỹ thuật/Data-ML** (vận hành). Không xuất map sang fixture, log, API public, slide hoặc video.
5. Không tạo nhóm kinh tế/dân tộc hay email GVCN khi source không cấp. Thiếu field → `insufficient_data`. **Sau `H15` (decision #18):** nạp `attendance_event` từ `mvp-attendance-over-time` theo schema đã duyệt + cửa sổ/mốc [Data-ML §2.2](08-data-ml-scoring-fairness-contract.md); không dùng legacy synthetic đã liệt kê; `excused=true` không vào mẫu số rate.
6. Chỉ tính trend điểm khi một `student_ref` có tối thiểu hai `term_code` hợp lệ. Trend chuyên cần chỉ khi đủ mốc theo Data-ML §2.2. Nguồn chỉ một kỳ, status unknown (evaluation), grade lỗi/quá cũ, thiếu điểm danh đã duyệt, hoặc mapping GVCN thiếu phải sinh `reason_code` đúng nhánh.
7. Fairness chỉ chạy khi có thuộc tính audit đã được phê duyệt, nhãn outcome, cỡ mẫu/mẫu số và định nghĩa nhóm. Hiện catalog không có thuộc tính này; contract trả `insufficient_data(no_approved_audit_attribute)`, không dùng proxy ngành/giới tính.

## 4. Handoff cho pipeline (sau H10)

Trước khi nối API/`dwh`, Khánh Duy bàn giao fixture đã validate và bốn artifact:

1. `source_manifest.json` và `data_quality_report.json` không có PII;
2. dataset chuẩn hóa gồm bảng domain điểm (`student_dimension`, `term_grade`, `academic_status`, `advisor_assignment`) **và** `attendance_event` từ `mvp-attendance-over-time` + hai artifact meta ở mục (1), dùng `student_ref`/`advisor_ref`;
3. data dictionary: nguồn field, nullable semantics, taxonomy `Trạng thái` (§3.3), snapshot hash và giới hạn coverage;
4. test kết quả: row count/reject count, uniqueness khóa, valid term/grade, cấm PII/token và expected `insufficient_data` / `reason_code`.

**M05a** (build source gate) khác **M05b** (approved source available): M05a Done (PR #17). **M05b Done** — [14-m05b…](../03-project/14-m05b-semester-approval.md). **H15 Done** — [12-h15…](../03-project/12-h15-attendance-approval-prep.md). **M06 mở.**

`H19` tạo persistence `dwh` từ [schema vật lý MVP](07-mvp-persistence-schema.md) trên DB rỗng; chỉ mapping metadata của DWH legacy, không copy schema/row/reference cũ. `H20` nạp fixture M06 vào transaction sau khi kiểm tra M05b; `H08` mới đọc `dwh` thành `NormalizedStudentRecord`/`ScoringFeatures` theo [Data-ML](08-data-ml-scoring-fairness-contract.md).

Hoàng nhận input `NormalizedStudentRecord`/`ScoringFeatures` chỉ gồm pseudonymous ID, feature điểm theo kỳ, feature chuyên cần theo thời gian (khi có), coverage/freshness và provenance. `academic_status.is_dropout_outcome`, raw `MSSV`, tên, email, SĐT, `Cố vấn học tập` gốc và field fairness không nằm trong scoring public, `ReviewCase`, hay agent context — outcome chỉ evaluation nội bộ.

## 5. Persistence và import có kiểm soát

- `H19` tạo bảng `dwh` versioned cho domain điểm + `source_manifest`/`data_quality_report`, và `attendance_event` theo `H15`; DB khởi tạo rỗng và migration có thể chạy lại an toàn.
- Không có cột hay import path MVP cho `MSSV`, tên, email, SĐT, token, thuộc tính nhóm, raw score hay mapping định danh. Điểm danh qua path `mvp-attendance-over-time` (decision #18); vẫn cấm legacy synthetic đã liệt kê.
- `H20` chỉ đọc artifact M06 ở vị trí ngoài repo được kiểm soát (semester) + fixture H15 trong repo tests. Thiếu approval, hash/count/schema lệch, PII/token, cross-source join hoặc quality gate fail phải rollback toàn bộ.
- `H20` không phải public API endpoint và không dùng V59 raw / `epu_data` / legacy synthetic làm seed thay thế ngoài path đã duyệt.

## 6. Acceptance cho M05–M06, H19–H20 và H08

- M05a có source register/gate với lựa chọn/loại từng file, hash, record count và PII exclusion list (code/tests) — **Done** PR #17.
- M05b có artifact duyệt (owner, quyền sử dụng, snapshot hash) — **Done** [14-m05b…](../03-project/14-m05b-semester-approval.md).
- M06 tạo cùng một output từ cùng snapshot hai lần với hash/row count như nhau; fixture = 4 bảng domain + `attendance_event` + `source_manifest` + `data_quality_report`; không chứa PII/token, không cross-join source và validate theo schema.
- H19 migrate DB rỗng/repeatable; evidence gồm revision + mapping metadata không PII.
- H20 chứng minh import atomic/idempotent: hash/count/schema hoặc approval lỗi thì không ghi hàng nào; fixture đạt gate mới được nạp vào `dwh`.
- H08 đọc snapshot đã nạp, phân biệt `insufficient_data` với “ổn định”, và chỉ route khi `advisor_ref` hiện diện (thiếu → mapping-repair queue).
- M03/FR-09 chỉ trả fairness metric nếu data gate ở mục 3.6 đạt; nếu không, UI/API ghi rõ audit chưa đủ dữ liệu.
