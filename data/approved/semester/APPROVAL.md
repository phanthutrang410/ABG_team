# Semester domain package approval (git-safe)

> Team default: import [`domain_package.json`](domain_package.json) via `python -m app.dwh.cli import-semester` (no env required).
> Raw V59 remains **outside** git (M05b provenance only).

| Field | Value |
|:---|:---|
| Owner | Hoàng / Admin kỹ thuật · Silent Shield MVP demo |
| Rights | MVP Silent Shield pipeline only; no raw redistribution; no PII/map in git |
| `source_id` | `v59-empty-program-students` |
| Committed artifact | `data/approved/semester/domain_package.json` |
| **Package** `snapshot_sha256` (H20 gate) | `73274079b30487f066cb2e1751c7ec70e2737ff794d6ae76e3e26ec4cf86df24` |
| `record_count` (students) | `460` |
| Raw provenance SHA-256 (M05b, ngoài git) | `34a53298df3dafd4d248496e75fbc10d95f997b76d0a7e6566e04ea97c367c66` |
| Raw path (ngoài git) | `reference-Learning-Analytics-AI/backend/db/v59-empty-program-students.json` |
| `schema_version` | `epu-1` |
| `provenance_approved` | `true` |
| Regenerated | 2026-07-18 via `scripts/export_approved_semester_domain.py` |

`source_manifest.snapshot_sha256` inside the package keeps the **raw** provenance hash; `SEMESTER_APPROVAL.snapshot_sha256` in code gates the **package file** bytes.
