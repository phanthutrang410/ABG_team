# Catalog trường dữ liệu — reference EPU (Learning Analytics AI)

> Mô tả **các trường đang có** trong clone `reference-Learning-Analytics-AI/` (không commit vào Silent Shield).  
> Mục đích: làm cơ sở chọn nguồn EPU có thể tận dụng cho sản phẩm → duyệt lãnh đạo → giao GV → soạn mail.  
> Không phải contract SIS production; không thay thế thỏa thuận dữ liệu thật.

## 1. Tóm tắt nguồn

| Nguồn (đường dẫn trong reference) | Bản ghi | Vai trò | Điểm / học vụ | `Trạng thái` (label học vụ) | Chuyên cần / điểm danh tuần |
|:---|---:|:---|:---|:---|:---|
| `crawl/synthetic_student_profile_replacements.json` (bản sao `backend/db/synthetic-student-profile-replacements.json`) | 1 547 | Hồ sơ hiển thị synthetic (tên, email, SĐT, lớp…) | `grades` **luôn rỗng** | Có trường, nhưng **100%** `Đang học` | Không |
| `backend/db/v59-synthetic-students.json` | 187 | Hồ sơ + bảng điểm kiểu crawl/SIS | Có bảng điểm theo môn–học kỳ | **Có phân bố dropout-related** | Có proxy vắng (không phải điểm danh tuần) |
| `backend/db/v59-empty-program-students.json` | 460 | Cùng schema V59, chương trình “mỏng” | Có (thường 8 môn/SV) | Có `Đang học` / `Thôi học` / `Buộc thôi học` | Không (thiếu các field vắng) |
| `epu_data.json` | 20 | Mẫu nhỏ cùng họ schema V59 | Có | Chủ yếu `Đang học` | Không |
| `backend/db/synthetic-transcript-coverage-v5.json` | 720 SV (synthetic graph) | Coverage học phần–điểm QT/GK/CK theo kỳ | Có (enrollment + components) | **Không** có `Trạng thái` | Không |
| `backend/db/transcript-coverage-v5-audit.json` | meta | Thống kê/audit transcript v5 | — | — | — |
| `backend/db/specialization-catalog.json` | 26 CN + 80 map lớp | Catalog chuyên ngành ↔ lớp | — | — | — |

**Chốt về label dropout:** trường `student_info.Trạng thái` **có** và hữu ích ở bộ **V59** (và `epu_data`). File profile replacements mà UI đang mở **không** mang label đa dạng — chỉ skeleton hồ sơ gắn `profile_replacement.student_id` → transcript v5.

**Chốt lựa chọn nguồn (không tạo hoặc nạp synthetic):**

- Ứng viên primary là `v59-empty-program-students.json`: 460 hồ sơ, có `Trạng thái`, bảng điểm hai học kỳ và `Cố vấn học tập`. Chỉ được dùng sau khi M05 xác minh provenance/quyền sử dụng và xuất bản bản trích xuất đã pseudonymize.
- `epu_data.json` là ứng viên kiểm tra transform theo chuỗi học kỳ dài hơn; không ghép với V59 vì `MSSV` không giao nhau trong snapshot đã kiểm tra, và không đủ cỡ mẫu để đánh giá model/fairness.
- `v59-synthetic-students.json`, profile replacements và transcript v5 bị **loại khỏi pipeline** vì được catalog xác định là synthetic. Không sinh thêm điểm danh, lịch tuần, nhãn hay thuộc tính nhóm để bù khoảng trống.
- Điểm theo môn–học kỳ là tín hiệu khả dụng. Điểm danh theo thời gian **thuộc MVP** nhưng catalog reference hiện chưa có chuỗi đã duyệt — phải lấy qua `H15`; mọi feature phụ thuộc nó trả `insufficient_data` cho đến khi có nguồn, không được giả lập và không đẩy ra Post-MVP.

---

## 2. `synthetic_student_profile_replacements.json`

**Cấu trúc gốc:** mảng object.

| Trường cấp 1 | Kiểu | Ghi chú |
|:---|:---|:---|
| `student_info` | object | Hồ sơ hiển thị |
| `grades` | array | Luôn `[]` trong snapshot hiện tại |
| `profile_replacement` | object | Map sang bản ghi học vụ synthetic |

### 2.1. `student_info`

| Trường | Kiểu (quan sát) | Coverage | Ghi chú |
|:---|:---|---:|:---|
| `Họ và tên` | string | 1547/1547 | Synthetic identity |
| `MSSV` | string | 1547/1547 | Mã hiển thị |
| `Trạng thái` | string | 1547/1547 | Chỉ thấy giá trị `Đang học` |
| `Giới tính` | string | 1547/1547 | `Nam` / `Nữ` (~50/50) |
| `Ngày sinh` | string `DD/MM/YYYY` | 1547/1547 | |
| `Khóa` | string | 1547/1547 | Ví dụ `2022`…`2025` |
| `Cơ sở` | string | 1547/1547 | `Cơ sở 1` |
| `Bậc đào tạo` | string | 1547/1547 | `Đại học - Tín chỉ` |
| `Loại hình đào tạo` | string | 1547/1547 | `Chính quy` |
| `Ngành` | string | 1547/1547 | ~12 ngành |
| `Mã ngành` | string | 1547/1547 | Mã chương trình |
| `Chuyên ngành` | string | 1547/1547 | |
| `Khoa` | string | 1547/1547 | ~8 khoa |
| `Lớp` | string | 1547/1547 | ~48 lớp (ví dụ `K22-7340101-A01`) |
| `Thời gian đào tạo` | string | 1547/1547 | Ví dụ `4,0 năm` |
| `Niên khóa` | string | 1547/1547 | Ví dụ `2022-2026` |
| `Email` | string | 1547/1547 | Email synthetic kiểu sinh viên |
| `Số ĐT` | string | 1547/1547 | SĐT synthetic |
| `GPA tích lũy` | string số | 1547/1547 | ~0.63–3.84 |

### 2.2. `profile_replacement`

| Trường | Kiểu | Ghi chú |
|:---|:---|:---|
| `student_id` | number | ID nội bộ map sang evidence học vụ |
| `source` | string | Thường `synthetic_transcript_coverage_v5` |
| `old_student_code` | string | Có thể rỗng |
| `note` | string | Mô tả: giữ academic evidence, thay profile hiển thị |

**Không dùng file này làm:** nguồn điểm, nguồn điểm danh tuần, nguồn label dropout đa lớp.

---

## 3. Họ schema V59 / crawl (`v59-*.json`, `epu_data.json`)

**Cấu trúc gốc:** mảng object.

| Trường cấp 1 | Kiểu | Ghi chú |
|:---|:---|:---|
| `token` | string | Token phiên crawl / định danh bản ghi nguồn |
| `student_info` | object | Hồ sơ + một số chỉ số học vụ |
| `total_courses` | number | Số môn trong `grades` (hoặc tổng khai báo) |
| `grades` | array<object> | Bảng điểm theo môn–học kỳ |

### 3.1. `student_info` — hợp nhất các biến thể

| Trường | v59-synthetic (187) | v59-empty (460) | epu_data (20) | Ghi chú dùng sản phẩm |
|:---|---:|---:|---:|:---|
| `Họ và tên` | ✓ | ✓ | ✓ | PII-style; tách khỏi scoring |
| `MSSV` | ✓ | ✓ | ✓ | Khóa liên kết |
| `Trạng thái` | ✓ | ✓ | ✓ | **Label học vụ / dropout proxy** |
| `Giới tính` | ✓ | ✓ | ✓ | |
| `Ngày vào trường` | ✓ | ✓ | ✓ | Mốc “từ nhập học” |
| `Mã hồ sơ` | 186/187 | ✓ | ✓ | |
| `Khóa` | ✓ | ✓ | ✓ | |
| `Cơ sở` | ✓ | ✓ | ✓ | |
| `Bậc đào tạo` | ✓ | ✓ | ✓ | |
| `Loại hình đào tạo` | ✓ | ✓ | ✓ | |
| `Ngành` | ✓ | ✓ | ✓ | |
| `Chuyên ngành` | ✓ | ✓ | ✓ | |
| `Khoa` | ✓ | ✓ | ✓ | Đơn vị lãnh đạo |
| `Lớp` | ✓ | ✓ | ✓ | Filter theo lớp |
| `Thời gian đào tạo` | ✓ | ✓ | ✓ | |
| `Niên khóa` | ✓ | ✓ | — | |
| `Thời gian học tối thiểu` | ✓ | — | — | |
| `Thời gian học tối đa` | ✓ | — | — | |
| `Cố vấn học tập` | ✓ | ✓ | — | **Map GV phụ trách / soạn mail** |
| `Số ĐT` | 167/187 | ✓ | — | Liên hệ; không đưa vào model |
| `Vắng CP HK1 (2026-2027)` | ✓ | — | — | Proxy vắng có phép (snapshot), **không** phải điểm danh tuần |
| `Vắng CP năm 2026` | ✓ | — | — | |
| `Vắng KP HK1 (2026-2027)` | ✓ | — | — | Proxy vắng không phép |
| `Vắng KP năm 2026` | ✓ | — | — | |
| `Tổng tín chỉ nợ` | ✓ | — | — | Tín hiệu học vụ phụ |
| `Số môn nợ` | ✓ | — | — | |
| `major_label` | ✓ | ✓ | — | Nhãn ngành nội bộ (ví dụ `CNTC`) |

### 3.2. Phân bố `Trạng thái` (quan sát trên snapshot)

| Giá trị | v59-synthetic | v59-empty | epu_data |
|:---|---:|---:|---:|
| `Đang học` | 147 | 414 | 19 |
| `Buộc thôi học` | 26 | 23 | 1 |
| `Thôi học` | 11 | 23 | 0 |
| `Rút học phí` | 2 | 0 | 0 |
| `Bảo lưu` | 1 | 0 | 0 |

Gợi ý nhãn dương cho dropout modeling (cần chốt product): gộp `Thôi học` + `Buộc thôi học` (+ tùy chọn `Rút học phí`); `Bảo lưu` tách riêng (không mặc định = dropout).

### 3.3. Phần tử `grades[]`

| Trường | Kiểu (quan sát) | Ghi chú |
|:---|:---|:---|
| `Học kỳ` | string | Ví dụ `HK1 (2022-2023)` |
| `STT` | string số | Thứ tự trong bảng |
| `Tên môn học` | string | |
| `Mã lớp` | string | Mã lớp học phần / section nguồn |
| `TC` | string số | Tín chỉ |
| `TX1` … `TX4` | string số hoặc `""` | Điểm thường xuyên / thành phần |
| `TB Thường kỳ` | string số hoặc `""` | |
| `Kết thúc L1` | string số hoặc `""` | Thi kết thúc lần 1 |
| `Kết thúc L2` | string số hoặc `""` | Lần 2 (nếu có) |
| `Điểm tổng kết` | string số hoặc `""` | |
| `Xếp loại` | string | Ví dụ `[C  - ]`, `[D - ]` |
| `Ghi chú` | string | Ví dụ `Không đạt` / rỗng |

Độ sâu điển hình: v59-synthetic ~0–76 môn/SV (TB ~54); v59-empty cố định 8; epu_data ~20–66.

---

## 4. `synthetic-transcript-coverage-v5.json`

**Cấu trúc gốc:** object.

| Trường | Kiểu | Ghi chú |
|:---|:---|:---|
| `schema_version` | number | `1` |
| `source` | string | `synthetic_transcript_coverage_v5` |
| `seed` | number | Ví dụ `20260702` |
| `official` | boolean | `false` (synthetic, không phải official SIS) |
| `generated_at` | string ISO datetime | |
| `derivation` | string | `deterministic transcript-first synthetic demo coverage` |
| `components` | array | Định nghĩa thành phần điểm chuẩn |
| `programs` | array | 12 chương trình |
| `summary` | object | `programs`, `classes`, `students`, `sections`, `enrollments`, `grade_components` |

### 4.1. `components[]` (template điểm)

| Trường | Ví dụ |
|:---|:---|
| `name` | `Quá trình` / `Giữa kỳ` / `Cuối kỳ` |
| `weight` | `0.3` / `0.3` / `0.4` |
| `clo_code` | `CLO1`… |

### 4.2. `programs[]`

| Trường | Kiểu | Ghi chú |
|:---|:---|:---|
| `program_id` | number | |
| `program_code` | string | Ví dụ `7480201` |
| `program_name` | string | Ví dụ `Công nghệ thông tin` |
| `department_id` | number | |
| `classes` | array | Lớp / cohort trong chương trình |
| `sections` | array | Lớp học phần theo kỳ |
| `students` | array | Sinh viên + enrollments |

#### `classes[]`

| Trường | Kiểu |
|:---|:---|
| `class_code` | string |
| `teacher_id` | number |
| `cohort_id` | number |
| `cohort_code` | string (ví dụ `K22`) |
| `specialization_id` | number |

#### `sections[]`

| Trường | Kiểu | Ghi chú |
|:---|:---|:---|
| `section_key` | string | Khóa ghép lớp–kỳ–môn |
| `section_code` | string | |
| `course_id` | number | |
| `course_code` | string | |
| `course_name` | string | |
| `semester_id` | number | |
| `semester_code` | string | `2024-1` … `2025-2` |
| `teacher_id` | number | GV dạy học phần |
| `max_students` | number | |

#### `students[]`

| Trường | Kiểu | Ghi chú |
|:---|:---|:---|
| `student_code` | string | |
| `full_name` | string | |
| `program_id` | number | |
| `cohort_id` | number | |
| `specialization_id` | number | |
| `class_code` | string | Lớp hành chính |
| `profile` | string | `normal` / `watch` / `high` — **không** phải `Trạng thái` học vụ |
| `gpa_cumulative` | number | |
| `enrollments` | array | 20 enrollment/SV trong snapshot |

#### `enrollments[]` và `components[]`

| Trường | Kiểu |
|:---|:---|
| `section_key` | string |
| `course_id` | number |
| `semester_id` | number |
| `final_grade` | number |
| `components[].name` | string |
| `components[].weight` | number |
| `components[].score` | number |

**Thiếu so với V59:** không có `Trạng thái`, không có cố vấn học tập dạng tên, không có bảng điểm crawl TX/KT, không có điểm danh tuần.

---

## 5. `transcript-coverage-v5-audit.json` (meta)

| Trường | Ghi chú |
|:---|:---|
| `schema_version` | `1` |
| `summary` | `source`, số programs/semesters/cohorts/courses ứng viên |
| `semesters[]` | `id`, `code`, `name`, `year`, `term`, `enrollments` |
| `programs[]` | Thống kê theo chương trình + danh sách course (`code`, `name`, `credits`, CLO/PLO counts…) |

Dùng để hiểu phạm vi coverage; không phải hồ sơ sinh viên.

---

## 6. `specialization-catalog.json`

| Trường | Ghi chú |
|:---|:---|
| `schema_version` | `1` |
| `source_checksum` | Hash nguồn |
| `specializations[]` | `code`, `name`, `program_name`, `department_name` |
| `class_mappings[]` | `class_code` → `specialization_code` / `specialization_name` / `program_name` / `department_name` |

Hữu ích để chuẩn hóa lớp ↔ ngành ↔ khoa khi gom danh sách lãnh đạo / GV.

---

## 7. Ánh xạ nhanh sang mục tiêu sản phẩm (mock)

| Nhu cầu sản phẩm | Trường / nguồn hiện có | Việc còn lại |
|:---|:---|:---|
| Phân tích theo kỳ | `grades[]` (V59 / `epu_data`) | Chuẩn hóa schema nội bộ một lần; chỉ tính trend khi có ít nhất hai kỳ |
| Label học vụ | `Trạng thái` (V59 / `epu_data`) | Taxonomy `Thôi học` + `Buộc thôi học`; không lấy từ profile replacements |
| Danh sách theo khoa/lớp | `Khoa`, `Lớp`, `Ngành` | Pseudonymize mã SV, bỏ PII thừa |
| Giao GV phụ trách | `Cố vấn học tập` (V59) | Chuẩn hóa thành `advisor_ref`; không seed/mock email hoặc liên hệ |
| Soạn mail | `student_ref`, lớp và `advisor_ref` sau khi case được duyệt | Chỉ tạo bản nháp; dữ liệu liên hệ nằm ngoài artifact nộp bài |
| Điểm danh theo thời gian | Catalog reference hiện chưa có chuỗi | **MVP** qua `H15`: lấy export đã duyệt; thiếu → `insufficient_data`; **không** tạo chuỗi giả và không đẩy Post-MVP |
| Fairness nhóm kinh tế/dân tộc | Không có | Không proxy hoặc bịa nhóm; audit trả `insufficient_data` đến khi có nguồn được phê duyệt |

---

## 8. Ràng buộc khi dùng trong Silent Shield

- Thư mục `reference-Learning-Analytics-AI/` là **reference local**, không đưa vào bài nộp / không commit theo quy ước team.
- Các field danh tính (họ tên, email, SĐT) không đưa vào artifact demo/repo hay feature chấm điểm. Mapping vận hành, nếu được phê duyệt, phải ở kho kiểm soát riêng.
- `official: false` trên transcript v5 nên file này không được dùng cho metric hoặc demo sau quyết định loại synthetic.
- Khi đưa sang `data/` của Silent Shield: chỉ export **schema đã làm sạch** (bỏ token crawl, PII và liên hệ), kèm manifest provenance, dictionary nhãn `Trạng thái` và báo cáo chất lượng. Không kèm generator.

## 9. Kiểm tra lại snapshot

Các số liệu phân bố trong tài liệu này lấy từ filesystem local tại thời điểm viết. Nếu regenerate JSON trong reference, chạy lại đếm `Trạng thái` / coverage field trước khi coi là ground truth demo.
