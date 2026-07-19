# D460 Live redeploy evidence — 460 SV linked attendance

> **Date:** 2026-07-19 ~03:10 +07 · **Owner:** Hoàng  
> **Scope:** Live API EC2 + Postgres bootstrap (not Vercel FE rebuild).

## Chốt

| Mục | Giá trị |
|:--|:--|
| API image | `silent-shield-api:d460` · digest `sha256:4f1fb57b7e4f259fdf9751a88cd54f57316a92e70dbb088302308a5d05d1714a` |
| EC2 | `i-0b0576945d080cb3f` · API `http://52.74.255.88:8000` |
| Linked handle | `LINKED_NAMESPACE_APPROVAL=approval:mvp-linked-v59-att:v1:acfb7d80dc3a` |
| Attendance hash | `acfb7d80dc3a…` · **7360** events (cleared legacy `78d7153f…`) |
| Semester | 460 · hash `73274079…` |
| `ml_term_snapshot` | 460 |
| `attendance_week` | 1840 rows · 460 students |
| Auth seed | `quanly` / `gvcn` / `demo` · password canonical `demo123` (SSM `/silent-shield/d460/AUTH_SEED_PASSWORD`) |
| Model | `m02-baseline-0.2` |

## Ops sequence (executed)

1. Dockerfile: build from repo root; `COPY data/approved /data/approved` (importer `_REPO_ROOT=/`).
2. `docker build -f backend/Dockerfile` → ECR push `:d460`.
3. SSM redeploy: pull `:d460`, preserve `DATABASE_URL`, set `LINKED_NAMESPACE_APPROVAL` + `AUTH_SEED_PASSWORD` + `APP_ENV=demo`.
4. SSM bootstrap: `upgrade_head` → clear attendance `source_id` (separate tx) → `import-semester` / `import-attendance` → `materialize-ml` → `rollup-attendance-week` → auth seed.
5. Auth smoke (in-container cookie): login `quanly` → `GET /review-cases`.

## Smoke (auth session)

| Check | Result |
|:--|:--|
| `GET /health` | `ok` · `database: true` |
| Anon `GET /review-cases` | **401** (H39 — expected) |
| Login `quanly` → list | `state=ok` · **n=18** (threshold; not 460) |
| `attendance_source_unapproved` count | **0** |
| Cases with `n_attendance_events>0` | **18/18** |
| Sample | `n_att=16` · `coverage.status=ok` · `reasons=[]` · `model_version=m02-baseline-0.2` |
| `GET /advisor-handoff-drafts` | `state=empty` |
| Vercel `/health` proxy | ok |
| Vercel anon `/review-cases` | 401 (API auth) |
| Vercel `POST /auth/login` | **404** — production FE image **pre-G07 rewrite**; needs Vercel redeploy of current `frontend/` |

## Known limits (still)

- List ≠ 460 (priority threshold).
- Weekly `CaseRepository` in-memory (D460-09 deferred); care `app.review_case` durable.
- Agent Live still fail-closed without `OPENAI_API_KEY`.
- Vercel FE must be redeployed for browser login + `/auth/*` rewrite before claiming full HTTPS demo path.
- Demo credentials: operator-only (Parameter Store); never commit.

## Rollback

Pull prior API digest `:d4r` `sha256:2b01b24a…` per [runbook §8](../04-engineering/06-deploy-runbook.md). Attendance re-import may need clear if hash differs.
