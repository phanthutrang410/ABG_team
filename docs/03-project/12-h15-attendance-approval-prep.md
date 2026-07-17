# H15 — Attendance source approval prep

> **Status: PREP ONLY — not Done.** Sprint stays `[ ] BLOCKED → data-owner`. Do not tick H15, do not merge EPU/Data-ML amendments, and do not add synthetic `attendance_event` fixtures until the external approval artifact exists.
>
> **Owner:** Hoàng · **Depends:** H10 Done + **external** data-owner approval artifact · **SoT until then:** [Data-ML §2.2](../04-engineering/08-data-ml-scoring-fairness-contract.md), [EPU contract](../04-engineering/04-epu-data-integration-contract.md), decision #17.

## 0. Chase status (refresh ~05:56 +07 18/7/2026)

| Lane | Sprint status | Blocker | Next ask (owner) |
|:--|:--|:--|:--|
| **M05a** (Duy) | `[ ] TODO` — mở sau H10 (H10 Done) | Chưa có gate code/tests | **Khánh Duy:** ship `M05a` source gate (register + hash/count + PII exclusion + fail-closed thiếu approval). Evidence: code + tests. **Không** bịa fixture “đã duyệt”. |
| **M05b** (Duy + data-owner) | `[ ] BLOCKED → M05a + approval` | M05a chưa Done **và** chưa có semester approval artifact | **Sau M05a:** Duy chỉ mở `M05b` khi data-owner giao package semester (owner / rights / hash / record count) **ngoài repo**. Thiếu → giữ `insufficient_data`. |
| **H15** (Hoàng + data-owner) | `[ ] BLOCKED → data-owner` | Chưa có attendance approval artifact | **Data-owner:** giao đủ 5 trường §1 dưới (ngoài git). Hoàng **không** amend EPU/Data-ML và **không** tick Done cho tới khi artifact + amend cùng handoff. |

**Open items (chưa nhận):** cả 5 hàng checklist §1 = trống; không có pointer ngoài-repo trong release evidence; consumers vẫn `attendance_source_unapproved`.

**Cấm chase này:** fake approval, synthetic `attendance_event`, tick `M05b`/`H15` Done, amend contract “sẵn”.

### Next asks — copy/paste

**→ Khánh Duy (M05a → rồi mới M05b)**

1. Hoàn thành **M05a** ngay: build source gate theo EPU + Data-ML §7 (register, hash/count, PII exclusion, fail-closed khi thiếu approval) + tests.
2. **Không** bắt đầu M06 / không seed fixture “approved” trước M05b.
3. Khi M05a Done: ping data-owner lấy **semester** approval artifact (owner, quyền, `snapshot_sha256`, record count) → chỉ khi có mới tick **M05b** và mở M06.
4. Attendance export là lane **H15** riêng — M06 chỉ thêm `attendance_event` sau H15 Done.

**→ Data-owner (H15 attendance package)**

Giao **một** package ngoài repo, đủ:

1. Owner (tên/role + đơn vị)
2. Rights (scope MVP Silent Shield; cấm tái phân phối)
3. Hash (`snapshot_sha256` hoặc tương đương)
4. Cadence (chu kỳ làm mới / cửa sổ hợp lệ)
5. Privacy review (không PII thừa; pseudonym path; retention)

Optional: schema field names only, `presence_status` enum, `excused` policy, grain (`observed_at` vs period). **Không** gửi map MSSV↔ref vào git.

## 1. Chase checklist (artifact outside repo)

Ask data owner for a single approval package. Store it **outside the git tree** (controlled path / shared drive / env-configured location). Repo may only hold a non-PII pointer in M05b / release evidence later — never the raw export or identity map.

| # | Field | Ask / capture | Status (~05:56 18/7) | Notes |
|:--|:--|:--|:--|:--|
| 1 | **Owner** | Tên/role người phê duyệt + đơn vị | **OPEN** — chưa nhận | Ai chịu trách nhiệm nguồn |
| 2 | **Rights** | Quyền dùng cho Silent Shield MVP (scope, cấm tái phân phối) | **OPEN** — chưa nhận | Khớp RULES privacy/minimization |
| 3 | **Hash** | `snapshot_sha256` (hoặc tương đương) của export điểm danh | **OPEN** — chưa nhận | Khớp `source_manifest` khi M05b/H20 |
| 4 | **Cadence** | Chu kỳ làm mới / cửa sổ hợp lệ của snapshot | **OPEN** — chưa nhận | Feed refine §2.2 window/period |
| 5 | **Privacy review** | Xác nhận không PII thừa; pseudonym path; retention | **OPEN** — chưa nhận | Không commit map MSSV↔ref |

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
