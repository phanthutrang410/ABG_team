# Approved domain packages (git-safe)

Pseudonymous fixtures only. Raw EPU export stays **outside** git.

| Snapshot | `source_id` | Path |
|:---|:---|:---|
| Semester (primary) | `v59-empty-program-students` | [`semester/domain_package.json`](semester/domain_package.json) |
| Attendance (MVP) | `mvp-attendance-over-time` | [`attendance/mvp_attendance_over_time.json`](attendance/mvp_attendance_over_time.json) |

Approval metadata: [`semester/APPROVAL.md`](semester/APPROVAL.md), attendance hashes in H15 / importer constants.

## Regen semester package (owner máy có raw V59)

```powershell
# From repo root; requires reference clone or env path
$env:SILENT_SHIELD_SEMESTER_SOURCE_PATH = (Resolve-Path "reference-Learning-Analytics-AI/backend/db/v59-empty-program-students.json").Path
python scripts/export_approved_semester_domain.py
```

Script prints the new package SHA-256. Update `SEMESTER_APPROVAL` in `backend/app/dwh/importer.py` and `semester/APPROVAL.md` to match before commit.
