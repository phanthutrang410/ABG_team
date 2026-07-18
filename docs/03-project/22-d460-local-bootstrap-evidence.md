# D460 local + Live bootstrap evidence — 460 SV deploy path

> **Date:** 2026-07-19 · Local Docker Postgres + **Live EC2 Done**  
> Live details: [23-d460-live-redeploy-evidence.md](23-d460-live-redeploy-evidence.md)

## Commands (local)

```powershell
docker compose up -d db
# from backend/
python -c "from app.dwh.migrate import upgrade_head; from app.config import get_settings; upgrade_head(get_settings().database_url)"
python -m app.dwh.cli import-semester
python -m app.dwh.cli import-attendance
python -m app.dwh.cli materialize-ml
python -m app.dwh.cli rollup-attendance-week
python -m app.dwh.cli readiness
# or: python scripts/bootstrap_d460.py
```

## Observed results (local)

| Check | Result |
|:--|:--|
| Semester `student_dimension` | 460 · hash `73274079…` |
| Attendance events | 7360 · hash `acfb7d80dc3a22d63f88b07ef706108743c122a121cd2d6261b993f98be964ac` |
| readiness | `ready: true`, gaps `[]` |
| `ml_term_snapshot` | 460 |
| `attendance_week` | 1840 rows · 460 distinct students |
| H08 linked sample | `coverage.status=ok`, `n_attendance_events=16`, no `attendance_source_unapproved` |

## Live (19/7 — Done)

| Check | Result |
|:--|:--|
| API image | `:d460` · `sha256:4f1fb57b7e4f259fdf9751a88cd54f57316a92e70dbb088302308a5d05d1714a` |
| Attendance | 7360 · hash `acfb7d80…` (legacy `78d7153f…` cleared) |
| Auth list smoke | `state=ok` n=18 · **0** `attendance_source_unapproved` · sample `n_att=16` |
| Anon list | 401 (H39) |
| Vercel FE `/auth` | **Pending redeploy** (production FE still 404 on `POST /auth/login`) |

## Env required

```text
LINKED_NAMESPACE_APPROVAL=approval:mvp-linked-v59-att:v1:acfb7d80dc3a
AUTH_SEED_PASSWORD=<operator secret — SSM /silent-shield/d460/AUTH_SEED_PASSWORD>
```

## Deferred

- **D460-09:** weekly `CaseRepository` still in-memory (care `app.review_case` is durable).
- **T05:** full agent tool/RBAC adversarial matrix — still open.
- **Vercel FE production redeploy** for G07 `/auth/*` rewrite + login UX.
