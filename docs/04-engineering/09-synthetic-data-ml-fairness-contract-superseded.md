# Data / ML / Fairness Contract — SUPERSEDED (synthetic era)

> **SUPERSEDED bởi H10 (18/7/2026).** Không dùng làm nguồn chuẩn MVP.
>
> - Contract sống: [`08-data-ml-scoring-fairness-contract.md`](08-data-ml-scoring-fairness-contract.md) + [`04-epu-data-integration-contract.md`](04-epu-data-integration-contract.md).
> - Quyết định: [#17](../03-project/04-decisions.md).
> - File này giữ lại chỉ để đối chiếu lịch sử. Synthetic GT (§3/§7 cũ), `dataset_version` synthetic, n=120 và group attrs synth **không** áp dụng trên MVP path. Semantics coverage/threshold/small-N có thể đã được tái diễn giải trong contract 08 — nếu lệch, ưu tiên 08 + EPU.
>
> Đổi tên từ `05-data-ml-fairness-contract.md` vì số `05` đã thuộc [kiến trúc hệ thống](05-system-architecture.md).

# (Lịch sử) Data / ML / Fairness Contract — Silent Shield (M04 synthetic)

> Nguồn chuẩn semantics cho scoring, ground truth, threshold và fairness trên **dữ liệu synthetic** (không còn hiệu lực cho MVP). Schema Pydantic (H06/H06c) phải theo contract **08** sau H10. Phạm vi sản phẩm theo [PRD](../02-product/04-prd.md) §4, §7 (FR-02/03/09/10) và [Ethics](../02-product/05-ethics.md) §5–6.

## 1. Versioning bắt buộc

Mọi đầu ra (prediction, case, fairness report) phải mang đủ:

| Trường | Ý nghĩa | Giá trị hiện tại |
|:---|:---|:---|
| `dataset_version` | Định danh bộ synthetic: nguồn + seed + kích thước | `synthetic-v0.1-seed42-n40-w12` (sau M05: `synthetic-v0.2-seed42-n120-w12-uni`) |
| `model_version` | Phiên bản estimator + feature spec | `ew-0.1.0` (M02 cập nhật khi đổi công thức) |
| `threshold_config_version` | Bộ ngưỡng đang dùng (§6) | `thr-0.1` |
| `computed_at` | Thời điểm tính (ISO 8601) | runtime |

Determinism (FR-02): cùng `dataset_version` + `model_version` + `threshold_config_version` ⇒ kết quả giống hệt nhau, kể cả contributing factors và fairness metrics.

## 2. Data dictionary — 3 CSV synthetic

Nguồn: [`data/synthetic/`](../../data/synthetic/README.md), sinh bởi [`synthetic.py`](../../backend/app/ml/early_warning/synthetic.py) qua `scripts/generate_synthetic.py`.

### `students.csv` — khóa chính `student_id`

| Cột | Kiểu | Ràng buộc | Semantics |
|:---|:---|:---|:---|
| `student_id` | str | `SYN\d{4}`, unique, not null | Mã synthetic; không phải PII |
| `class_id` | str | not null | Mapping lớp/cohort cho routing/demo. **Cấm dùng làm feature scoring** (proxy risk). Sau M05 đổi sang cohort đại học |
| `synth_socioeconomic_group` | str | enum `A/B/C`, not null | **Audit-only** (AUDIT-01). Cấm vào scoring, cấm hiển thị ở case cá nhân |
| `synth_ethnicity_group` | str | enum 5 nhóm, not null | **Audit-only** (AUDIT-02). Như trên |

### `grades_timeseries.csv` — khóa `(student_id, week)`

| Cột | Kiểu | Ràng buộc | Semantics |
|:---|:---|:---|:---|
| `student_id` | str | FK → students | |
| `week` | int | 1..12, unique per student | Tuần quan sát; thiếu tuần = thiếu quan sát, **không** nội suy |
| `score` | float | [0, 10] | Điểm tuần (CORE-01/02) |

### `attendance_timeseries.csv` — khóa `(student_id, week)`

| Cột | Kiểu | Ràng buộc | Semantics |
|:---|:---|:---|:---|
| `student_id` | str | FK → students | |
| `week` | int | 1..12 | |
| `attendance_rate` | float | [0, 1] | Tỷ lệ chuyên cần tuần (CORE-03/04) |

Quy tắc nạp (FR-01): thiếu cột, sai kiểu, ngoài miền giá trị, `student_id` mồ côi → báo lỗi rõ ràng, **không** âm thầm bỏ dòng. Dòng trùng khóa → lỗi.

## 3. Lineage và seed

- Generator: `generate_synthetic(out_dir, students, weeks, seed)`; RNG tách nhánh: students `seed`, grades `seed+1`, attendance `seed+2`.
- Latent draws hiện tại: mỗi SV có `grade_drift` (20% rơi vào nhánh suy giảm `U(−0.15, 0.05)`, còn lại `U(−0.03, 0.03)`) và `attendance_decline` (25% rơi vào nhánh `U(0, 0.04)`, còn lại 0).
- Tái sinh: `python scripts/generate_synthetic.py --students 40 --weeks 12 --seed 42`. Mọi thay đổi tham số ⇒ bump `dataset_version`.
- **Quyết định M04 cho M05:** khi đổi sang cohort đại học, nâng `--students` lên **120** để mẫu số fairness theo nhóm đạt quy tắc small-N (§8) — 40 hồ sơ hiện tại cho ~8 SV/nhóm dân tộc, không đủ để demo metric trung thực.

## 4. `ScoringFeatures` vs `FairnessAuditSlice` (input cho H08)

`EarlyWarningFeatures` hiện tại trong [`types.py`](../../backend/app/ml/early_warning/types.py) trộn group attrs vào feature — H08 tách thành hai contract:

### `ScoringFeatures` — thứ duy nhất estimator được nhận

| Trường | Kiểu | Semantics |
|:---|:---|:---|
| `student_id` | str | |
| `grade_trend_slope` | float \| null | Hệ số góc OLS của `score` theo `week` trên cửa sổ quan sát; null nếu series không đủ điều kiện (§5) |
| `grade_volatility` | float \| null | Độ lệch chuẩn của `score` trong cửa sổ |
| `attendance_rate_window` | float \| null | Trung bình `attendance_rate` trong cửa sổ |
| `attendance_trend_slope` | float \| null | Hệ số góc OLS của `attendance_rate` theo `week` |
| `coverage` | object | Bắt buộc — xem §5 |

Cấm xuất hiện trong `ScoringFeatures`: `class_id`, hai group attrs, và mọi trường suy ra từ chúng.

### `FairnessAuditSlice` — chỉ pipeline audit được join

| Trường | Kiểu |
|:---|:---|
| `student_id` | str |
| `synth_socioeconomic_group` | str |
| `synth_ethnicity_group` | str |

Join `predictions × FairnessAuditSlice × ground truth` chỉ xảy ra trong bước tính `FairnessReport` (M03). Estimator, case API và agent context không bao giờ thấy slice này.

## 5. Coverage và điều kiện `insufficient_data` (FR-03)

Trường `coverage` đi kèm mọi feature/prediction:

| Trường | Semantics |
|:---|:---|
| `n_weeks_grades` / `n_weeks_attendance` | Số tuần có quan sát hợp lệ trong cửa sổ 12 tuần |
| `missing_ratio_grades` / `missing_ratio_attendance` | 1 − n/12 |
| `last_week_observed` | max(week) trên cả hai series |
| `status` | `ok` \| `partial` \| `insufficient` |

Quy tắc (cấu hình được, đây là default `thr-0.1`):

- Một series **đủ điều kiện** khi `n_weeks ≥ 6`.
- Cả hai series đủ → `ok`. Đúng một series đủ → `partial`: vẫn tính score từ series đủ, case phải hiển thị giới hạn. Không series nào đủ → `insufficient`: **không tính score, không tạo case**, trả `insufficient_data`.
- Freshness: `last_week_observed < tuần_báo_cáo − 2` → gắn cờ stale; theo cấu hình có thể chặn tạo tín hiệu mới.
- `insufficient`/stale **không được** hiển thị thành “ổn định” (Ethics §5) và bị **loại khỏi mọi mẫu số metric** (§7) — báo cáo riêng số lượng `n_excluded_insufficient`.

## 6. Threshold semantics (FR-04/10)

- `model_score` ∈ [0, 1]: giá trị **nội bộ** để xếp thứ tự (ML schema). Không xuất hiện ở public API/UI — public chỉ có `review_priority_band` (H06a).
- Hai ngưỡng trong `threshold_config`:

| Ngưỡng | Default `thr-0.1` | Ý nghĩa |
|:---|:---:|:---|
| `tau_case` | 0.60 | `model_score ≥ tau_case` ⇒ tạo tín hiệu (positive vận hành) |
| `tau_high` | 0.80 | Band: `≥ tau_high` → `uu_tien_som`; `[tau_case, tau_high)` → `can_ra_soat`; dưới → không tạo case |

- Default được hiệu chỉnh trong M02 trên synthetic sao cho tải review ~15–25% cohort; giá trị chốt ghi vào `threshold_config_version`, không tự ý đổi ở FE/agent.
- FR-10: UI/demo phải cho thay đổi `tau_case` và thấy tác động tới FP, FN và số case cần review (H04 expose config, G04 hiển thị). Ngưỡng chỉ có nghĩa với `model_version` + `dataset_version` đi kèm — **không chuyển sang dữ liệu thật**.

## 7. Ground truth synthetic và ma trận nhầm lẫn (FR-09)

### 7.1 `synthetic_pattern_label` — định nghĩa

Ba CSV hiện **chưa có** nhãn outcome ([traceability §4](../01-requirements/03-traceability.md)). Nhãn được sinh từ **latent draws của generator** (không phải từ dữ liệu quan sát, tránh nhãn trùng định nghĩa với feature):

```text
label = 1  ⇔  grade_drift ≤ −0.05  HOẶC  attendance_decline ≥ 0.02
```

- Xấp xỉ tác động: −0.05/tuần ≈ mất 0.6 điểm (thang 10) sau 12 tuần; 0.02/tuần ≈ mất 24 điểm % chuyên cần sau 12 tuần. Tỷ lệ positive kỳ vọng ≈ 21%.
- **Ngữ nghĩa:** `label = 1` nghĩa là “chuỗi synthetic này được generator chủ đích cài mẫu suy giảm đáng rà soát”. Nó **không** nghĩa là “sinh viên sẽ bỏ học” và không bao giờ được hiển thị như thuộc tính sinh viên trên UI.
- Độc lập với nhóm: latent draws độc lập với group attrs theo cấu trúc generator ⇒ base rate kỳ vọng bằng nhau giữa nhóm; chênh lệch đo được phản ánh model/ngưỡng + biến động mẫu, phải đọc cùng cỡ mẫu.

### 7.2 Cách sinh và lưu

- Generator (sửa trong **M05**) persist latent draws và nhãn ra **file riêng** `data/synthetic/ground_truth.csv`: `student_id, synthetic_pattern_label, grade_drift, attendance_decline, label_rule_version` (`gt-0.1`).
- File riêng để nhãn không lọt vào đường nạp scoring; chỉ pipeline đánh giá/fairness (M03) được đọc. Cùng seed ⇒ cùng nhãn (determinism).

### 7.3 Ma trận nhầm lẫn và mẫu số

Positive vận hành = `model_score ≥ tau_case` (tín hiệu được tạo). Chỉ tính trên SV có coverage `ok`/`partial`:

| | `label = 1` | `label = 0` |
|:---|:---|:---|
| **Flagged** | TP | FP |
| **Not flagged** | FN | TN |

| Metric | Công thức | Mẫu số |
|:---|:---|:---|
| FPR | FP / (FP + TN) | SV `label = 0` đủ coverage |
| TPR / recall | TP / (TP + FN) | SV `label = 1` đủ coverage |
| Precision | TP / (TP + FP) | SV được flag |
| Selection rate | (TP + FP) / N | SV đủ coverage |

Selection rate **không được gọi là FPR**. Mọi metric báo cáo kèm mẫu số và `n_excluded_insufficient`.

## 8. Fairness metrics và quy tắc small-N (FR-09)

- Phân rã theo từng `group_type` (socioeconomic, ethnicity) riêng biệt; không giao hai trục trong MVP (mẫu quá nhỏ).
- Metric tối thiểu: **FPR theo nhóm** và **ΔFPR = max − min** giữa các nhóm đủ điều kiện; khuyến khích thêm TPR và selection rate theo nhóm để tránh tối ưu một metric (Ethics §6).
- **Small-N rules (`gt-0.1`):**
  - Một nhóm chỉ được báo FPR khi mẫu số của nhóm (`label = 0`, đủ coverage) **≥ 10**; ngược lại nhóm đó ở trạng thái `insufficient_group_data` — hiển thị cỡ mẫu, không hiển thị số metric.
  - ΔFPR chỉ tính trên các nhóm đủ điều kiện; nếu < 2 nhóm đủ → ΔFPR = `insufficient`, panel phải nói rõ thay vì bỏ trống.
  - Cờ fairness nội bộ: `ΔFPR > 0.10` → gắn cờ rà ngưỡng/dữ liệu. Giá trị 0.10 là ngưỡng demo gắn với `dataset_version` hiện tại, không phải chuẩn production.
- Mọi con số kèm nhãn **“synthetic”**: chứng minh pipeline đo được fairness, không chứng minh hệ thống công bằng trên dữ liệu thật (PRD §2).

### Semantics `FairnessReport` (đã mã hóa: [`fairness.py`](../../backend/app/contracts/fairness.py) + fixture + test — H06c)

| Trường | Semantics |
|:---|:---|
| `dataset_version`, `model_version`, `threshold_config_version`, `label_rule_version`, `computed_at` | §1, §7 |
| `synthetic: true` | Bắt buộc, hằng số trong MVP |
| `small_n_min_denominator` | Ngưỡng small-N đang áp dụng (10 với `gt-0.1`); validator enforce hai chiều: `ok` ⇔ mẫu số ≥ ngưỡng |
| `groups[]` | Mỗi phần tử: `group_type`, `group`, `n_total` (= neg + pos), `n_label_neg`, `n_label_pos`, `n_excluded_insufficient`, `fpr`, `tpr`, `selection_rate`, `status: ok \| insufficient_group_data` (metric = null khi insufficient; `tpr` được phép null cả khi `ok` nếu `n_label_pos` quá nhỏ) |
| `delta_fpr_by_group_type` | Map `group_type → {status, value, reason}` — mỗi trục nhóm có ΔFPR riêng (một số duy nhất cho cả hai trục là mơ hồ); `insufficient` bắt buộc kèm `reason`, keys phải khớp các `group_type` có trong `groups` |
| `fairness_flag` | `flagged` + `delta_fpr_threshold` + `triggered_group_types` (chỉ trục có delta `ok` mới được trigger) |

## 9. Bảng bàn giao

| Consumer | Dùng phần nào |
|:---|:---|
| H06a/b (Hoàng) | §1 versioning, §5 coverage status, §6 band mapping cho `ReviewCase` |
| H06c (Khánh Duy) | §8 bảng `FairnessReport` |
| H08 (Khánh Duy + Hoàng) | §4 tách hai contract |
| M05 (Khánh Duy) | §3 n=120, §7.2 `ground_truth.csv` |
| M02 (Khánh Duy) | §5 quy tắc coverage, §6 hiệu chỉnh τ, §7.3 định nghĩa positive |
| M03 (Khánh Duy) | §7–§8 toàn bộ metric + small-N |
| G04/G05 (Giang) | §6 band + threshold demo, §8 trạng thái insufficient trên panel |
