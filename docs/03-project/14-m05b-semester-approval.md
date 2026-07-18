# M05b — Semester source approval (MVP demo)

> **Status: Done** — decision [#18](04-decisions.md). Owner duyệt = Admin kỹ thuật (Hoàng), không có data-owner ngoài trong cửa sổ demo.
>
> **Không** commit raw V59 / PII / map MSSV↔`student_ref`. Team dùng package M06 đã pseudonymize trong git; raw chỉ để regen.

## Artifact

| Field | Value |
|:--|:--|
| Owner | Hoàng / Admin kỹ thuật · Silent Shield MVP demo |
| Rights | Chỉ pipeline MVP Silent Shield (M06→H20→scoring); cấm tái phân phối raw export; cấm đưa PII/map vào git/slide/video |
| `source_id` | `v59-empty-program-students` |
| **Team default (in git)** | [`data/approved/semester/domain_package.json`](../../data/approved/semester/domain_package.json) — xem [APPROVAL.md](../../data/approved/semester/APPROVAL.md) |
| Package gate SHA-256 | `73274079b30487f066cb2e1751c7ec70e2737ff794d6ae76e3e26ec4cf86df24` |
| Raw path (ngoài git, regen only) | `reference-Learning-Analytics-AI/backend/db/v59-empty-program-students.json` |
| Raw provenance SHA-256 | `34a53298df3dafd4d248496e75fbc10d95f997b76d0a7e6566e04ea97c367c66` |
| Optional env | `SILENT_SHIELD_SEMESTER_SOURCE_PATH` — override default package / raw owner path |
| `record_count` | `460` |
| `schema_version` | `epu-1` |
| `provenance_approved` | `true` |
| Approved at | 2026-07-18 (~07:05 +07); package committed 2026-07-18 |

## Scope

- Duyệt **điểm theo học kỳ** từ ứng viên V59-empty đã quan sát trong EPU contract — **không** sinh điểm synthetic.
- Điểm danh theo thời gian: lane riêng `H15` / `mvp-attendance-over-time` ([12-h15…](12-h15-attendance-approval-prep.md)).
- Public copy: trung lập; không claim “nhà trường đã duyệt export chính thức”.

## Consumer

`H20` mặc định import domain package trong repo (`python -m app.dwh.cli import-semester`). Regen: `python scripts/export_approved_semester_domain.py` trên máy có raw V59.
