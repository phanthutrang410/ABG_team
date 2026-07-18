# M05b — Semester source approval (MVP demo)

> **Status: Done** — decision [#18](04-decisions.md). Owner duyệt = Admin kỹ thuật (Hoàng), không có data-owner ngoài trong cửa sổ demo.
>
> **Không** commit raw V59 / PII / map MSSV↔`student_ref`. File nguồn nằm **ngoài git** (reference local hoặc path cấu hình env).

## Artifact

| Field | Value |
|:--|:--|
| Owner | Hoàng / Admin kỹ thuật · Silent Shield MVP demo |
| Rights | Chỉ pipeline MVP Silent Shield (M06→H20→scoring); cấm tái phân phối raw export; cấm đưa PII/map vào git/slide/video |
| `source_id` | `v59-empty-program-students` |
| Local path (ngoài git) | `reference-Learning-Analytics-AI/backend/db/v59-empty-program-students.json` (không track) |
| Env hint cho M06 | `SILENT_SHIELD_SEMESTER_SOURCE_PATH` → absolute path tới file trên |
| `snapshot_sha256` | `34a53298df3dafd4d248496e75fbc10d95f997b76d0a7e6566e04ea97c367c66` |
| `record_count` | `460` |
| `schema_version` | `epu-1` |
| `provenance_approved` | `true` |
| Approved at | 2026-07-18 (~07:05 +07) |

## Scope

- Duyệt **điểm theo học kỳ** từ ứng viên V59-empty đã quan sát trong EPU contract — **không** sinh điểm synthetic.
- Điểm danh theo thời gian: lane riêng `H15` / `mvp-attendance-over-time` ([12-h15…](12-h15-attendance-approval-prep.md)).
- Public copy: trung lập; không claim “nhà trường đã duyệt export chính thức”.

## Consumer

`M06` (Duy) được mở: đọc path ngoài-repo + manifest khớp hash/count ở trên; fail-closed nếu lệch.
