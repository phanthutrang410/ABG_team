# H15 — Attendance source approval prep

> **Status: PREP ONLY — not Done.** Sprint stays `[ ] BLOCKED → data-owner`. Do not tick H15, do not merge EPU/Data-ML amendments, and do not add synthetic `attendance_event` fixtures until the external approval artifact exists.
>
> **Owner:** Hoàng · **Depends:** H10 Done + **external** data-owner approval artifact · **SoT until then:** [Data-ML §2.2](../04-engineering/08-data-ml-scoring-fairness-contract.md), [EPU contract](../04-engineering/04-epu-data-integration-contract.md), decision #17.

## 1. Chase checklist (artifact outside repo)

Ask data owner for a single approval package. Store it **outside the git tree** (controlled path / shared drive / env-configured location). Repo may only hold a non-PII pointer in M05b / release evidence later — never the raw export or identity map.

| # | Field | Ask / capture | Notes |
|:--|:--|:--|:--|
| 1 | **Owner** | Tên/role người phê duyệt + đơn vị | Ai chịu trách nhiệm nguồn |
| 2 | **Rights** | Quyền dùng cho Silent Shield MVP (scope, cấm tái phân phối) | Khớp RULES privacy/minimization |
| 3 | **Hash** | `snapshot_sha256` (hoặc tương đương) của export điểm danh | Khớp `source_manifest` khi M05b/H20 |
| 4 | **Cadence** | Chu kỳ làm mới / cửa sổ hợp lệ của snapshot | Feed refine §2.2 window/period |
| 5 | **Privacy review** | Xác nhận không PII thừa; pseudonym path; retention | Không commit map MSSV↔ref |

Optional but useful when chasing: schema sample (field names only), `presence_status` enum, whether `excused` / period vs `observed_at` is authoritative, expected row grain (buổi / ngày / tuần).

**Done-gate for this checklist:** đủ 5 hàng trên trong artifact ngoài repo — chưa đủ để tick H15 nếu chưa amend contract.

## 2. Amendment outline (draft only — apply after artifact)

Khi artifact có, **một** handoff amend theo thứ tự: EPU → Data-ML §2.2 → persistence note → rồi mới mở nạp `attendance_event` (`H20` / `M06`). Không amend “sẵn” như đã duyệt.

### 2.1 Data-ML §2.2 (refine, không invent trước)

| Topic | Default hiện tại (H10) | Cần chốt từ artifact |
|:--|:--|:--|
| Cửa sổ quan sát | 90 ngày lịch gần nhất từ `status_observed_at`/`extracted_at`, hoặc period học kỳ đang mở nếu export định nghĩa | Period owner vs calendar window; mốc bắt đầu/kết thúc |
| Mốc tối thiểu | Rate: ≥4 `observed_at` có `presence_status` ≠ null; slope: ≥2 mốc phân biệt sau rate gate | Có giữ / hạ / nâng theo grain thật |
| `excused` policy | Chưa suy diễn; chờ exception policy H15 | Excused có vào mẫu số rate không; null vs false; mapping từ mã nguồn |

### 2.2 Unique key `attendance_event`

Draft từ [persistence schema](../04-engineering/07-mvp-persistence-schema.md):

`(source_id, student_ref, observed_at, course_ref?)`

Khi có nguồn: xác nhận grain (`observed_at` vs period đã duyệt), nullability `course_ref`, và có cần thêm dimension (ví dụ session/class meeting) để uniqueness không đụng nhau. Ghi kết quả vào EPU bảng `attendance_event` + H19 schema trong cùng handoff amend.

### 2.3 EPU / pipeline notes (cùng handoff)

- Provenance + exception policy trong contract EPU (không synthetic week).
- M05b/H20: thiếu approval/hash/count/schema/PII → rollback; không seed attendance giả.
- Sau amend: consumers mới được chuyển từ `attendance_source_unapproved` sang coverage thật / `attendance_coverage_insufficient` khi thiếu mốc.

## 3. Consumers — fail-closed (giữ đến khi H15 Done)

Cho tới khi H15 Done + amendment merged, mọi consumer (H06a envelopes, H12a copy, scoring/adapters, demo) **phải** giữ:

- Toàn nhánh chuyên cần → `insufficient_data` với `reason_code=attendance_source_unapproved`
- UI/agent copy key: `copy.attendance_source_unapproved`
- Cấm: impute 0, chuỗi tuần giả, field `Vắng CP/KP` synthetic, fixture `attendance_event` “demo”

## 4. What unblocks Done

H15 chỉ được tick Done khi **cả hai** có:

1. External approval artifact đủ owner / rights / hash / cadence / privacy review (ngoài repo).
2. Contract amendments merged (EPU + Data-ML §2.2 + unique key / excused policy) khớp artifact — không chỉ checklist prep này.

Sau đó mới mở nạp `attendance_event` ở `H20`/`M06`. Prep note này **không** thay approval và **không** mở khóa load.
