# Data / ML / Fairness Contract — Silent Shield (H10)

> **Owner:** Hoàng · **Task:** H10 · **Input:** [M04 handoff](../03-project/10-m04-data-ml-handoff.md) · **Nguồn schema:** [EPU integration](04-epu-data-integration-contract.md).
>
> Contract nguồn chuẩn cho scoring, coverage, threshold, evaluation và fairness trên **snapshot đã qua gate** (M05b + H15 theo decision #18). Schema Pydantic (`H06a`/`H06c`) phải mã hóa đúng tài liệu này. Khi lệch, sửa schema hoặc mở decision — không âm thầm chọn một bản.
>
> **Phân biệt gate:** `M05a` (code gate) Done ≠ dữ liệu đã duyệt (`M05b`). **M05b/H15 đã Done** cho MVP demo — xem [14-m05b…](../03-project/14-m05b-semester-approval.md) / [12-h15…](../03-project/12-h15-attendance-approval-prep.md).

## 1. Versioning bắt buộc

Mọi đầu ra (prediction nội bộ, case projection, fairness report) phải mang đủ:

| Trường | Ý nghĩa | Ghi chú |
|:---|:---|:---|
| `dataset_version` | Định danh snapshot đã duyệt: `source_id` + hash ngắn + schema_version | Từ `source_manifest` sau M05b/H15; **cấm** legacy `synthetic-*` / marker `"synthetic"` trên MVP path (trừ allowlist decision #18) |
| `model_version` | Phiên bản estimator + feature spec | M02 bump khi đổi công thức |
| `threshold_config_version` | Bộ ngưỡng đang dùng (§5) | H04 expose; không hard-code FE |
| `calculated_at` / `computed_at` | Thời điểm tính (ISO 8601) | Runtime; không nhét vào hash nội dung fixture |

Determinism (FR-02): cùng `dataset_version` + `model_version` + `threshold_config_version` ⇒ cùng band/factors/metrics (không phụ thuộc đồng hồ tường trong nội dung so sánh).

## 2. Hai nhánh evidence độc lập

Mỗi nhánh có coverage/freshness/provenance riêng. Nhánh thiếu **không** kéo band về “ổn định”.

### 2.1 `TermEvidence` (điểm theo học kỳ)

Feature trên `student_ref`, chỉ từ `term_grade` + `student_dimension` đã qua gate:

| Feature | Định nghĩa | Điều kiện hợp lệ |
|:--|:--|:--|
| `term_avg[t]` | Trung bình `final_grade` theo `term_code`, trọng số `credits` | Bản ghi hợp lệ EPU §3 |
| `latest_term_gpa` | `term_avg` của `term_code` mới nhất có ≥1 điểm hợp lệ; thang 0–10 như EPU `Điểm tổng kết` (**không** convert GPA 4.0) | ≥ 1 môn có `final_grade` |
| `grade_trend_slope` | OLS của `term_avg` theo thứ tự `term_code` chuẩn hóa | ≥ 2 kỳ hợp lệ |
| `grade_volatility` | Độ lệch chuẩn `final_grade` trong cửa sổ kỳ hợp lệ | ≥ 2 bản ghi điểm |
| `failed_credits` | Σ `credits` các môn `grade_status` khớp fail (`Không đạt` hoặc tương đương đã chuẩn hóa); thiếu `credits` → bỏ môn đó khỏi tổng | Luôn ≥0 khi có `term_grades`; `0` nếu không có môn fail; **proxy** — không claim SIS `Tổng tín chỉ nợ` |
| `n_valid_terms`, `n_courses`, `last_term_code` | Coverage/freshness | Luôn kèm output |

V59-empty (ứng viên primary) thường ~8 môn/SV trong 2 kỳ → trend là delta hai điểm dữ liệu; **cấm** copy/slide claim “xu hướng dài hạn”. Decision #26: `latest_term_gpa` / `failed_credits` derive từ `term_grade` đã duyệt; eval synthetic lane riêng — xem [15…](15-ml-eval-synthetic-proposal.md).

### 2.2 Attendance evidence (điểm danh theo thời gian — MVP)

| Feature | Định nghĩa | Điều kiện hợp lệ |
|:--|:--|:--|
| `attendance_rate_window` | Tỷ lệ `presence_status=present` trong cửa sổ; **loại** bản ghi `excused=true` khỏi mẫu số | Sau `H15` Done; ≥ **4** mốc `observed_at` có `presence_status` khác null |
| `attendance_trend_slope` | Độ dốc theo `observed_at` | ≥ **2** mốc phân biệt sau khi rate gate đạt |

**Cửa sổ quan sát (H15 / decision #18):** 90 ngày lịch gần nhất tính từ `extracted_at` của snapshot attendance (hoặc period học kỳ nếu manifest định nghĩa). Nguồn allowlisted: `mvp-attendance-over-time`.

**Khi thiếu nguồn H15 / gate fail:** `insufficient_data` với `reason_code=attendance_source_unapproved`. **Không** impute 0; **không** dùng field `Vắng CP/KP` snapshot legacy synthetic; **không** dùng payload chứa marker `"synthetic"`.

`excused` / nghỉ có phép: `excused=true` → **không** đếm vào mẫu số rate; thiếu/`false` → đếm bình thường theo `presence_status`.

### 2.3 Kết hợp và `ScoringFeatures`

- `model_score` nội bộ chỉ từ nhánh `ready`; public chỉ `review_priority_band` + factors + coverage + `model_version` + `calculated_at`.
- **Cấm trong `ScoringFeatures`:** `is_dropout_outcome`, `Trạng thái` gốc, PII/liên hệ, `advisor_ref`, thuộc tính nhóm audit, `token` crawl.

| Trường tối thiểu | Kiểu | Semantics |
|:---|:---|:---|
| `student_ref` | str | Pseudonym; không phải MSSV |
| `latest_term_gpa` | float \| null | null nếu không có môn có `final_grade` |
| `grade_trend_slope` | float \| null | null nếu thiếu ≥2 kỳ |
| `grade_volatility` | float \| null | |
| `failed_credits` | float \| null | null nếu không có `term_grades`; else ≥0 (kể cả 0) |
| `attendance_rate_window` | float \| null | null nếu nhánh attendance không ready |
| `attendance_trend_slope` | float \| null | |
| `coverage` | object | §3 — bắt buộc |

Đổi công thức / thêm field scoring → bump `model_version` (decision #26: `m02-baseline-0.2`).

## 3. Coverage và `insufficient_data`

`coverage` đi kèm mọi feature/prediction:

| Trường | Semantics |
|:---|:---|
| `n_valid_terms` / `n_courses` | Số kỳ / môn điểm hợp lệ |
| `n_attendance_events` | Số mốc điểm danh hợp lệ (0 khi chưa có nguồn) |
| `last_term_code` / `last_attendance_at` | Freshness |
| `status` | `ok` \| `partial` \| `insufficient` |
| `reason_codes[]` | Mã máy đọc được (bảng dưới) |

| `reason_code` | Khi nào |
|:---|:---|
| `source_unapproved` | Thiếu M05b / manifest / hash |
| `attendance_source_unapproved` | Thiếu nguồn/`provenance` H15 hoặc gate reject |
| `single_term` | Chỉ 1 kỳ hợp lệ (không tính trend) |
| `grade_coverage_insufficient` | Không đủ bản ghi điểm hợp lệ |
| `attendance_coverage_insufficient` | Có nguồn nhưng dưới mốc tối thiểu |
| `status_unknown` | `is_dropout_outcome=unknown` — loại khỏi **evaluation**, không tự biến thành “ổn định” trên UI scoring |
| `no_approved_audit_attribute` | Fairness (§6) |
| `insufficient_group_data` | Small-N (§6) |

Quy tắc band/case:

- Không nhánh nào `ready` → `insufficient`: **không** tạo case “ổn định”, không tính score công khai.
- Chỉ điểm ready → `partial` hoặc `ok` tùy freshness; case phải hiển thị giới hạn nhánh attendance.
- `insufficient`/stale **không** render thành “ổn định” (Ethics §5).

## 4. Threshold và band (FR-04/10)

- `model_score ∈ [0,1]` **nội bộ**.
- `tau_case` (tạo tín hiệu) và `tau_high` (band `uu_tien_som` / `can_ra_soat`), version hóa `threshold_config_version`, expose qua H04.
- **Không chốt số τ trước M02** trên snapshot đã duyệt. Placeholder cấu hình `thr-epu-0.1-uncalibrated` chỉ để wiring test — không claim FPR vận hành.
- Mapping band (khi đã calibrate): `≥ tau_high` → `uu_tien_som`; `[tau_case, tau_high)` → `can_ra_soat`; dưới → không tạo case.
- FR-10: demo sweep τ phải thấy tác động FP/FN/tải review trên evaluation nội bộ.

## 5. Evaluation nội bộ (`is_dropout_outcome`)

- Nhãn: `academic_status.is_dropout_outcome` theo taxonomy EPU §3 / decision #17.
- **Chỉ** M02/M03 test/evaluation. Positive vận hành = `score ≥ tau_case`.
- FPR = FP/(FP+TN) trên `is_dropout_outcome=false`; TPR = TP/(TP+FN) trên `true`.
- `unknown` và SV `insufficient_data` **loại khỏi mọi mẫu số**; báo `n_excluded_*` riêng.
- **Giới hạn leakage:** `Trạng thái` là trạng thái *tại snapshot*, không phải outcome tương lai có label cutoff. Metric = sanity check phân biệt trên snapshot — **không** claim early-warning precision/recall trên slide/CP.

## 6. Fairness (FR-09) — fail-closed

- Catalog hiện **không có** thuộc tính audit được phê duyệt → `FairnessReport` trả `insufficient_data` với `reason_code=no_approved_audit_attribute`.
- Cấm proxy bằng ngành/khoa/lớp/giới tính.
- Khi sau này có nguồn duyệt: small-N mẫu số nhóm (`label` âm, đủ coverage) **≥ 10**; dưới ngưỡng → `insufficient_group_data`. ΔFPR chỉ trên nhóm đủ điều kiện; dưới 2 nhóm đủ → ΔFPR insufficient.
- Tách tuyệt đối audit slice ↔ scoring / public case / agent context.
- `H06c` rework fixture theo hướng fail-closed (không synthetic group attrs trên MVP path).

### Copy keys (H12a implement đúng nghĩa)

| Key | Copy tiếng Việt trung lập |
|:---|:---|
| `copy.attendance_source_unapproved` | Chưa có nguồn điểm danh đã được phê duyệt. Hệ thống không kết luận về chuyên cần. |
| `copy.fairness_no_approved_audit_attribute` | Chưa có thuộc tính kiểm toán công bằng đã được phê duyệt. Không công bố metric theo nhóm. |
| `copy.fairness_insufficient_group_data` | Cỡ mẫu nhóm chưa đủ để công bố metric công bằng. |
| `copy.partial_term_only` | Chỉ có tín hiệu điểm theo học kỳ; nhánh chuyên cần chưa sẵn sàng. |

## 7. Source/quality gate (spec cho M05a/M06)

Fail-closed từng lớp; gate fail ⇒ zero output MVP, không nạp một phần:

| Lớp | Kiểm tra | Fail ⇒ |
|:--|:--|:--|
| Register | Allowlist (`v59-empty-program-students` primary; `mvp-attendance-over-time` attendance; `epu_data` regression); từ chối marker `"synthetic"` / legacy cấm | Từ chối nguồn |
| Provenance | `source_manifest`: owner, quyền, `snapshot_sha256`, `record_count`, `provenance_approved` | `source_unapproved` |
| PII exclusion | Không xuất tên/MSSV/ngày sinh/email/SĐT/token; pseudonym ngoài repo | Chặn export |
| Schema/parse | UTF-8; `term_code`; điểm miền; khóa unique | Reject row → `data_quality_report` |
| Quality report | Counts, missingness, coverage, freshness, reason codes | Luôn phát hành |

Chi tiết bảng logic: [EPU §2–§3](04-epu-data-integration-contract.md).

## 8. Giới hạn forecast/fusion (M07/M08 — ngoài CP2)

Research-only sau `M02`+`H02`+`H13`. `TermEvidence` và evidence forecast tách riêng; fusion chỉ khi cả hai qua gate; absence không zero-impute. Không claim ở CP1/CP2.

## 9. Test plan tối thiểu (consumer)

| Nhóm | Kỳ vọng |
|:--|:--|
| Gate fail-closed | Thiếu approval/hash/synthetic → zero output + reason đúng |
| PII | Artifact chứa field cấm → fail |
| Transform | `term_code`; điểm ngoài miền; khóa trùng |
| Determinism | Cùng snapshot → hash/feature giống nhau |
| Insufficient theo nhánh | 1 kỳ → `single_term`; thiếu attendance → `attendance_source_unapproved` |
| Boundary | `ScoringFeatures` không chứa outcome/PII/`advisor_ref`/group |
| Fairness | Không audit attr → `insufficient_data` |

## 10. Bảng bàn giao

| Consumer | Dùng phần nào |
|:---|:---|
| H06a | §1–§3 versioning/coverage; §4 band; cấm field public |
| H06c | §6 FairnessReport fail-closed |
| H08 | §2 `ScoringFeatures` + coverage |
| H12a | §6 copy keys |
| H15 | §2.2 cửa sổ/mốc; exception policy |
| H19/H20 | §7 + EPU persistence |
| M05a/M06 | §7 gate + EPU schema |
| M02 | §2–§5 features/threshold/evaluation |
| M03 | §5–§6 |
| G04/G05 | §4 band + §6 insufficient UI |

Contract synthetic cũ (chỉ lịch sử): [09-synthetic…superseded](09-synthetic-data-ml-fairness-contract-superseded.md).
