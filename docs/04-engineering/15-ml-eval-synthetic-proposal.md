# ML eval synthetic proposal — feature-complete lane (decision #26)

> **Status:** M09 shipped — smoke n=12 (git) + full **n=2000** (local `data/eval/full/`). Catalog khoa/ngành weighted từ EPU approved package.  
> **Owner ML:** Giang · **Docs:** Hoàng · **Depends:** decision #26, Data-ML [08](08-data-ml-scoring-fairness-contract.md) `m02-baseline-0.2`.  
> **EDA:** [16-m09-eval-synthetic-eda.md](16-m09-eval-synthetic-eda.md).

## 1. Mục tiêu

Sinh dataset **pseudonymous, feature-complete** cho train/eval M02 (và M03) cùng spec `ScoringFeatures` đã mở rộng:

| Feature | Cần có trong raw eval package |
|:---|:---|
| `latest_term_gpa` | ≥1 môn/`final_grade` trên kỳ mới nhất |
| `grade_trend_slope` / `grade_volatility` | ≥2 kỳ / ≥2 điểm hợp lệ (phân bố đủ) |
| `failed_credits` | Một phần SV có môn `grade_status=Không đạt` + `credits` |
| `attendance_rate_window` / `attendance_trend_slope` | ≥4 mốc/`presence_status`; đủ timestamp phân biệt |

Lane này **song song** với MVP demo (`v59-empty` + `mvp-attendance`). Không thay M05b/H15; không feed H20 / public `ReviewCase` trừ decision sau.

## 2. Path và provenance

| Item | Giá trị |
|:---|:---|
| Root | `data/eval/` (sample nhỏ commit được; bulk lớn gitignore) |
| `source_id` allowlist (eval only) | `ml-eval-feature-complete-v1` |
| Provenance marker | `ml-eval-synthetic` (manifest field; **không** dùng bare `"synthetic"` trên MVP gate) |
| `dataset_version` | `ml-eval-feature-complete-v1-seed{N}-n{M}` |

Gate MVP (H20 / import-semester / import-attendance mặc định) **không** import path này. Eval CLI/tests load tường minh.

Không khôi phục generator legacy dưới `data/synthetic/` (M01 quarantine).

## 3. Schema đề xuất (aligned M06 domain)

Cùng hình dạng package M06 (pseudonym `student_ref`), tối thiểu:

1. **`student_dimension`** — `student_ref`, cohort/class/major (không PII).
2. **`term_grade`** — `student_ref`, `term_code`, `course_ref`, `credits`, `final_grade` (0–10), `grade_status` (gồm `Không đạt` có kiểm soát tỷ lệ).
3. **`attendance_event`** — `student_ref`, `observed_at`, `presence_status`, `course_ref`, `excused` (mẫu số rate loại `excused=true`).
4. **`academic_status`** — `is_dropout_outcome` chỉ cho evaluation nội bộ (M02/M03); **cấm** vào `ScoringFeatures`.
5. **Optional audit slice** (file/table tách) — group attrs fairness; **không** join vào scoring path.

Manifest + `data_quality_report` bắt buộc (hash, counts, `extracted_at`, provenance).

### Độ sâu tối thiểu / SV

- ≥2 `term_code` hợp lệ; ≥4 môn điểm (để GPA/volatility ổn định).
- ≥15–25% SV có ≥1 môn fail với `credits>0` (phân bố `failed_credits`).
- ≥4 attendance events trong cửa sổ 90 ngày; ≥2 timestamp phân biệt sau khi loại excused.

## 4. Generator rules (follow-up `M09`)

- Seed cố định; RNG tách nhánh: students `seed`, grades `seed+1`, attendance `seed+2`, outcomes `seed+3`.
- Latent correlates (có nhánh control ~60% ổn định): GPA thấp ↔ fail credits cao ↔ attendance rate thấp; không hard-code label vào features.
- Determinism: cùng seed/params ⇒ cùng hash package.
- Cấm PII, MSSV map, email, SĐT, tên thật.
- Cỡ mẫu: smoke **n=12** (git); full **n=2000** (`data/eval/full/`, gitignored). Catalog program weights từ V59-empty approved.

Deliverables `M09`:

1. `scripts/generate_ml_eval_package.py` + module `backend/app/ml/eval_synthetic/` — **Done** (smoke).
2. Tests determinism + schema validate + quarantine — **Done** (`tests/test_m09_eval_synthetic.py`).
3. Harness M02 baseline + EDA trên lane eval — **Done** (uncalibrated; không claim FPR).

## 5. Ranh giới claim

- Được nói: “dataset eval synthetic để train/đo model theo feature spec #26”.
- **Không** nói: “dữ liệu nhà trường”, “thay snapshot đã duyệt”, “SIS Tổng tín chỉ nợ / GPA tích lũy”.
- Public demo/Live URL tiếp tục provenance M05b/H15.

## 6. Liên kết

- Decision [#26](../03-project/04-decisions.md)
- Data-ML [08](08-data-ml-scoring-fairness-contract.md) §2.1 / §2.3
- Signal catalog CORE-04 / CORE-05
- Superseded synthetic history: [09](09-synthetic-data-ml-fairness-contract-superseded.md) (tham chiếu lịch sử only)
