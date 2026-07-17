# M04 — Handoff kỹ thuật Data/ML cho Hoàng (recovery 18/7)

> **Trạng thái:** handoff Duy → Hoàng để mở `H10`. Đây là đề xuất kỹ thuật, **không** phải contract nguồn chuẩn (Hoàng chốt trong H10) và **không đồng nghĩa dữ liệu đã được duyệt** (M05b riêng). Mốc 03:30 trên board đã trễ — ghi nhận, không lùi ngày. Nguồn: [EPU contract](../04-engineering/04-epu-data-integration-contract.md), [catalog EPU](../04-engineering/03-epu-reference-data-fields.md), Sprint §2.

## 1. Input cho baseline (M02) — hai nhánh evidence độc lập

### 1.1 Nhánh điểm theo học kỳ (`term_grade` + `student_dimension`)

Feature trên mỗi `student_ref`, chỉ từ bảng logic đã qua gate M05a/M06:

| Feature | Định nghĩa | Điều kiện hợp lệ |
|:--|:--|:--|
| `term_avg[t]` | Trung bình `final_grade` theo `term_code`, trọng số `credits` | Bản ghi điểm hợp lệ theo EPU contract §3.2 (đủ khóa, điểm trong miền 0–10) |
| `grade_trend_slope` | Hệ số góc OLS của `term_avg` theo thứ tự `term_code` chuẩn hóa | **≥ 2 kỳ hợp lệ** (EPU contract §3.5) |
| `grade_volatility` | Độ lệch chuẩn `final_grade` trong cửa sổ các kỳ hợp lệ | ≥ 2 bản ghi điểm |
| `n_valid_terms`, `n_courses`, `last_term_code` | Coverage/freshness | Luôn kèm mọi output |

V59-empty (ứng viên primary) chỉ có ~8 môn/SV trong 2 kỳ → trend là **delta 2 điểm dữ liệu**; không claim "xu hướng dài hạn" trong copy/slide.

### 1.2 Nhánh chuyên cần theo thời gian (`attendance_event` — chỉ sau H15)

| Feature | Định nghĩa | Điều kiện hợp lệ |
|:--|:--|:--|
| `attendance_rate_window` | Tỷ lệ `presence_status=present` trong cửa sổ quan sát | Số mốc tối thiểu theo contract H15 |
| `attendance_trend_slope` | Độ dốc theo `observed_at` | Như trên; `excused` xử lý theo exception policy H15 |

Cho tới khi `H15` có approval artifact: **toàn nhánh trả `insufficient_data(reason=attendance_source_unapproved)`** — không impute 0, không tạo chuỗi tuần, không dùng field `Vắng CP/KP` snapshot của v59-synthetic (file đã bị loại). Chuyên cần vẫn là MVP, không Post-MVP.

### 1.3 Kết hợp hai nhánh

- Mỗi nhánh là evidence riêng (`TermEvidence` / attendance evidence) với coverage/freshness/provenance riêng; nhánh thiếu hiển thị đúng trạng thái thiếu, **không kéo band về "ổn định"**.
- `model_score` nội bộ tính từ các nhánh `ready`; public chỉ `review_priority_band` + factors + coverage + `model_version` + `calculated_at` (Sprint §2.2).
- Cấm trong `ScoringFeatures`: `is_dropout_outcome`, `Trạng thái` gốc, mọi PII/liên hệ, `advisor_ref` (routing-only), thuộc tính nhóm (hiện không tồn tại trong nguồn), `token` crawl.

## 2. Source/quality gate (spec cho M05a/M06)

Fail-closed từng lớp; gate fail ⇒ zero output, không nạp một phần:

| Lớp | Kiểm tra | Fail ⇒ |
|:--|:--|:--|
| Register | File nằm trong allowlist (v59-empty primary, epu_data chỉ regression transform); synthetic files bị từ chối theo tên + nội dung | Từ chối nguồn |
| Provenance | `source_manifest`: owner, quyền dùng, `snapshot_sha256`, `record_count`, `provenance_approved` | `insufficient_data(source_unapproved)` |
| PII exclusion | Không xuất `Họ và tên`, `MSSV`, `Ngày sinh`, `Email`, `Số ĐT`, `token`; pseudonym `student_ref`/`advisor_ref` sinh ngoài repo | Chặn export |
| Schema/parse | UTF-8, trim/chuẩn hóa; `Học kỳ` → `YYYY-YYYY-Tn`; điểm parse được và trong miền; khóa `(student_ref, term_code, course_ref)` unique | Reject row → đếm vào `data_quality_report` |
| Quality report | Row/reject counts, missingness theo trường, term coverage, freshness, reason codes | Báo cáo luôn phát hành, kể cả khi gate fail |
| Status taxonomy | `Thôi học`/`Buộc thôi học` → `is_dropout_outcome=true`; `Đang học` → `false`; `Rút học phí`/`Bảo lưu`/khác → `unknown` (chờ owner chốt — **open decision cho H10**) | `unknown` loại khỏi mẫu số evaluation |

## 3. Threshold, FPR và evaluation semantics

- `model_score ∈ [0,1]` nội bộ; `tau_case` (tạo tín hiệu) và `tau_high` (band `uu_tien_som` / `can_ra_soat`), version hóa `threshold_config_version`, expose qua H04; demo sweep tác động FP/FN/tải review (FR-10). Default hiệu chỉnh trong M02 trên snapshot đã duyệt — không chốt số trước khi có data.
- **Nhãn evaluation:** `academic_status.is_dropout_outcome` — **chỉ nội bộ M02/M03 test** (Sprint §2.5). Positive = flagged (`score ≥ tau_case`); FPR = FP/(FP+TN) trên `is_dropout_outcome=false`; TPR = TP/(TP+FN); `unknown` và SV `insufficient_data` **loại khỏi mọi mẫu số**, báo số lượng loại riêng.
- **Giới hạn leakage phải ghi trong mọi claim:** `Trạng thái` là trạng thái *tại snapshot*, không phải outcome tương lai có label cutoff. Metric trên đó là *sanity check phân biệt trên snapshot*, **không** phải bằng chứng "dự báo sớm"; không claim precision/recall như early-warning performance trong slide/CP.
- **Fairness nhóm:** catalog hiện **không có** thuộc tính audit được phê duyệt → M03/FR-09 fail closed: `FairnessReport` trả `insufficient_data(no_approved_audit_attribute)`; không proxy bằng ngành/giới tính/khoa (EPU contract §3.6). Small-N (mẫu số nhóm ≥ 10) và tách audit ↔ scoring giữ nguyên hiệu lực khi có nguồn duyệt trong tương lai.

## 4. Giới hạn forecast/fusion (M07/M08 — ngoài CP2)

- Research-only sau `M02`+`H02`+`H13`; không cùng deadline, không tranh slot baseline, không claim ở CP1/CP2.
- `TermEvidence` và `AttendanceForecastEvidence` tách riêng, mỗi bên có ready/`insufficient_data`; fusion chỉ khi **cả hai** qua gate; absence không zero-impute, không đổi priority; public/agent chỉ band/factors/limitations (Sprint §5-M07).

## 5. Test plan (M05a/M06/M02/M03)

| Nhóm | Test tối thiểu |
|:--|:--|
| Gate fail-closed | Thiếu manifest/approval, hash/count lệch, file synthetic trong allowlist → zero output + reason đúng |
| PII | Xuất fixture chứa field cấm (tên/MSSV/email/SĐT/token) → test fail; scan trên artifact thật |
| Transform | Chuẩn hóa `term_code`; điểm ngoài miền/không parse → reject + đếm; khóa trùng → lỗi; reject count khớp report |
| Determinism | Cùng snapshot chạy 2 lần → fixture/feature/hash giống hệt (không dùng thời gian hệ thống trong nội dung) |
| Insufficient theo nhánh | 1 kỳ → `single_term`; thiếu attendance → `attendance_source_unapproved`; status `unknown` loại khỏi evaluation; `insufficient` không bao giờ render thành "ổn định" |
| Boundary scoring | `ScoringFeatures` serialization không chứa outcome/PII/`advisor_ref`/group attr (field-boundary test); scoring không import module evaluation |
| Threshold/band | Mapping band đúng theo `tau_*`; sweep thay đổi số case đơn điệu |
| Fairness fail-closed | Không có audit attr → `insufficient_data`; khi có: mẫu số đúng định nghĩa, nhóm < 10 → `insufficient_group_data` |

## 6. Open decisions cho H10 (Hoàng chốt)

1. Taxonomy `Trạng thái` cuối: `Rút học phí`/`Bảo lưu` = `unknown` hay tách riêng.
2. Vị trí sinh/lưu pseudonym map (ngoài repo) và ai giữ quyền.
3. Cửa sổ quan sát + số mốc tối thiểu cho attendance (đưa vào contract H15).
4. Copy UI cho hai trạng thái: nhánh attendance thiếu nguồn; fairness audit chưa đủ dữ liệu (H12a).
5. **Dọn artifact stale từ thiết kế synthetic cũ** (tôi không sửa vì là canonical/đã giao lane docs cho Hoàng): [`05-data-ml-fairness-contract.md`](../04-engineering/05-data-ml-fairness-contract.md) cần banner superseded (synthetic GT §3/§7 và n=120 không còn áp dụng; semantics coverage/threshold/small-N §5–§8 tái dùng được); trùng số file với `05-system-architecture.md` — cần rename một trong hai. `backend/app/contracts/fairness.py` + fixture (H06c cũ) sẽ được tôi rework sau H10 theo hướng fail-closed; `backend/app/ml/early_warning/synthetic.py` thuộc M01 reopen.
