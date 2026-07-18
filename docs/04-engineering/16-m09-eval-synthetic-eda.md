# EDA — ml-eval full package n=2000 (M09b)

> `data/eval/full/` · `dataset_version=ml-eval-feature-complete-v1-seed42-n2000`  
> Provenance: `ml-eval-synthetic` · **eval lane only** (gitignored bulk).  
> Catalog khoa/ngành weighted từ `data/approved/semester/domain_package.json` (EPU V59-empty, 460 SV → 13 khoa / 21 ngành / 23 program rows).

## 1. Quy mô

| Metric | Giá trị |
|:---|---:|
| Sinh viên | **2000** |
| Dòng `term_grade` | 29 955 |
| Sự kiện điểm danh | 12 000 (6 mốc × 2000) |
| Khoa | **13** |
| Ngành | **21** |
| Lớp (class_code) | 184 |
| Học phần unique | 420 |
| Cố vấn (eval) | 39 |
| Outcome dropout `true` | 359 (17.95%) |
| Outcome `false` | 1641 |

### Khoa (top)

| Khoa | n |
|:---|---:|
| Khoa Năng lượng mới | 599 |
| Khoa Quản trị Kinh doanh và Du lịch | 351 |
| Khoa Công nghệ Thông tin | 147 |
| Khoa Điện tử Viễn thông | 105 |
| … | (đủ 13 khoa) |

## 2. Feature coverage (M02 `m02-baseline-0.2`)

| Feature | n ready | Thống kê |
|:---|---:|:---|
| `latest_term_gpa` | 2000/2000 | mean 5.74 · [2.31, 8.21] |
| `grade_trend_slope` | 2000/2000 | mean −0.10 |
| `grade_volatility` | 2000/2000 | mean 0.87 |
| `failed_credits > 0` | 39.3% SV | mean credits fail 8.35 |
| `attendance_rate_window` | 2000/2000 | mean 0.72 · [0, 1] |

## 3. Tái tạo

```powershell
python scripts/generate_ml_eval_package.py --full --seed 42 `
  --eda-report data/eval/full/eda_summary.json `
  --eval-report data/eval/full/eval_report.json
```

Smoke nhỏ (commit): `--students 12 --out data/eval/smoke`.

Catalog nguồn: [`backend/app/ml/eval_synthetic/epu_program_catalog.json`](../../backend/app/ml/eval_synthetic/epu_program_catalog.json).
