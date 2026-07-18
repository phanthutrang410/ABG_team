# MVP linked attendance approval (decision #27 / H15b)

> **Status: Done** — fixture session-grain covering all M06 semester `student_ref`s.  
> **Approver:** Hoàng / Admin kỹ thuật · Silent Shield MVP demo.

## Handle

```text
approval:mvp-linked-v59-att:v1:acfb7d80dc3a
```

Settings: `LINKED_NAMESPACE_APPROVAL` (default matches handle above).

## Snapshot

| Field | Value |
|:---|:---|
| `source_id` | `mvp-attendance-over-time` |
| Path | `data/approved/attendance/mvp_attendance_over_time.json` |
| `snapshot_sha256` | `acfb7d80dc3a22d63f88b07ef706108743c122a121cd2d6261b993f98be964ac` |
| `record_count` (events) | `7360` |
| `n_students` | `460` (1:1 với semester domain package) |
| Grain | **session** — mỗi buổi (`observed_at` + `course_ref`) |
| Min sessions / SV | 16 (≥ Data-ML §2.2 min 4) |
| Window | ~90 ngày tới `extracted_at` 2026-07-18T12:00:00Z |
| Linked semester | `v59-empty-program-students` (M05b unchanged) |

## Semantics

- `attendance_rate_window`: tỷ lệ buổi present / buổi counted (`excused=true` loại khỏi mẫu số).
- `attendance_trend_slope`: OLS theo **ngày** (gộp nhiều môn cùng `observed_at` date/time bucket trong estimator).
- Public copy: trung lập; **không** slogan synthetic; **không** claim institutional attendance export.

## Regen

```powershell
python scripts/generate_mvp_linked_attendance.py --seed 42
# then update ATTENDANCE_APPROVAL hash/count + this doc + Settings default handle prefix
```
