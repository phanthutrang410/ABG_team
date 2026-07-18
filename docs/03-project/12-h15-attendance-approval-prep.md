# H15 — Attendance source approval + amendment

> **Status: Done** — decision [#18](04-decisions.md). Team-provisioned allowlisted source `mvp-attendance-over-time` (fixture pseudonymous trong repo). Supersede blocker “data-owner ngoài”.
>
> **Owner:** Hoàng · **SoT:** [EPU](../04-engineering/04-epu-data-integration-contract.md), [Data-ML §2.2](../04-engineering/08-data-ml-scoring-fairness-contract.md).

## 0. Status (refresh ~07:05 +07 18/7/2026)

| Lane | Sprint status | Notes |
|:--|:--|:--|
| **M05a** (Duy) | `[x] Done` — PR #17 | `backend/app/ml/source_gate/*` + `tests/test_source_gate.py` |
| **H06c** (Duy) | `[x] Done` — PR #17 | FairnessReport fail-closed |
| **M05b** | `[x] Done` | [14-m05b…](14-m05b-semester-approval.md) — V59 semester, team approver |
| **H15** | `[x] Done` | Fixture + checklist dưới; gate allowlist `mvp-attendance-over-time` |
| **M06** | `[ ] TODO` | **Unblocked** — Duy ship domain tables + manifests |

## 1. Approval checklist (CLOSED)

| # | Field | Value |
|:--|:--|:--|
| 1 | **Owner** | Hoàng / Admin kỹ thuật · Silent Shield MVP demo |
| 2 | **Rights** | Chỉ pipeline MVP; cấm tái phân phối; không PII trong git |
| 3 | **Hash** | `f65573ad1ec0e11f4093a57d3cf6e947a78ca994aa8d2feeaeabb6a25e2a2106` (`backend/tests/fixtures/attendance/mvp_attendance_over_time.json`) |
| 4 | **Cadence** | Cửa sổ 90 ngày lịch; snapshot demo cố định tới CP2 |
| 5 | **Privacy** | Chỉ `student_ref` pseudonymous; không MSSV/tên/email/SĐT; không map danh tính trong repo |

## 2. Source package

| Field | Value |
|:--|:--|
| `source_id` | `mvp-attendance-over-time` |
| Fixture path | `backend/tests/fixtures/attendance/mvp_attendance_over_time.json` |
| `record_count` | `15` (events) |
| `schema_version` | `epu-1` |
| `provenance_approved` | `true` |
| Grain | `observed_at` (ISO date) + optional `course_ref` |
| `presence_status` | `present` \| `absent` |
| `excused` | optional; nếu `true` → **không** vào mẫu số rate (Data-ML §2.2) |

## 3. Amendment applied (cùng handoff)

- EPU: nguồn điểm danh = allowlisted fixture; không chờ export ngoài.
- Data-ML §2.2: nhánh attendance ready khi H15 Done + coverage ≥4 mốc; không còn mặc định `attendance_source_unapproved`.
- Persistence: `attendance_event` được nạp qua M06/H20 sau H15 Done.
- Gate: `SOURCE_ALLOWLIST` gồm `mvp-attendance-over-time`; vẫn reject marker `"synthetic"` / legacy cấm.

## 4. Public copy

Trung lập: “điểm theo học kỳ và điểm danh theo thời gian”. Không gắn chữ synthetic; không claim institutional approval.
