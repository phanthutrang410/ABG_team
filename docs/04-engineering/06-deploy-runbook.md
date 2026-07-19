# Deploy / ops runbook — Silent Shield MVP

> **D4b Live product (2026-07-18):** list→case smoke Done (`database:true`, `/review-cases` ok). D4a shell digests kept for rollback.
> Owner: Hoàng · Tasks: **H07** → **D4a** → **D4b** · Region: `ap-southeast-1` · Account deploy user: IAM `chungang` (no secrets in this doc).

## 0. Secrets policy

- **Never** put real API keys, tokens, passwords, connection strings with credentials, or authenticated Live URLs into this doc, git, slides, video, or AI log.
- Use [`.env.example`](../../.env.example) as the variable *names* template. Real values live only in local `.env` / host secrets (gitignored).
- Public demo must stay anonymous: no PII, no advisor personal contacts, no raw scores.

## 1. Source of truth (structure)

| Concern | Canonical doc |
|:--------|:--------------|
| Containers, data flow, trust/care boundary | [05-system-architecture.md](05-system-architecture.md) |
| Case transitions / forbidden actions | [Process §4](../02-product/03-process.md) |
| Stack + BE host choice | [Decisions](../03-project/04-decisions.md) #5–6 (FastAPI + Next.js; BE on **AWS**) |
| LLM env / base URL | [01-fpt-ai-api.md](01-fpt-ai-api.md) |
| Env *names* only | [`.env.example`](../../.env.example) |
| Release evidence checklist | [07-release-evidence.md](../03-project/07-release-evidence.md) |
| Board / release loop | [Sprint](../03-project/03-sprint.md) (`D4a` → `D4b` → `V07` → `D4r` → `V05`) |

If this runbook and architecture disagree, **architecture + decisions win** until H07 is revised with Live facts.

## 2. Target topology (Live shell — D4a)

```text
[EPU extract approved] → data gate → fixtures → FastAPI (AWS EC2 + ECR)
                                              ↘ Next.js UI (same EC2)
                                              ↘ FPT agent (explain-only; not required for D4a)
```

| Component | Live value (D4a) |
|:----------|:-----------------|
| Region | `ap-southeast-1` |
| EC2 instance | `i-0b0576945d080cb3f` (`t3.small`, Name=`silent-shield-d4a`) |
| AMI | `ami-0b31875bb70b82eb2` (Amazon Linux 2023) |
| Elastic IP | `52.74.255.88` (`eipalloc-09066880c09305fbe`) |
| Security group | `sg-0c88406bc7b7fd0d6` (`silent-shield-live`; TCP 3000 + 8000) |
| API public base | `http://52.74.255.88:8000` |
| FE public origin | `http://52.74.255.88:3000` |
| API image (rollback tag) | `058264284502.dkr.ecr.ap-southeast-1.amazonaws.com/silent-shield-api:d4a` · digest `sha256:7a6ba16516bcc33beb58f4497f0583b220061e2f502f7ff913656319c523a23b` |
| FE image (rollback tag) | `058264284502.dkr.ecr.ap-southeast-1.amazonaws.com/silent-shield-web:d4a` · digest `sha256:58ccf51321418291ba8ac44b9034328e56542963f3dadb3764ef8539554c5973` |
| IAM instance profile | `SilentShieldEC2Profile` / role `SilentShieldEC2Role` (SSM + ECR read) |

**D4a scope:** `/health` green + FE reachable. Postgres not attached on this shell (`database: false` is expected). Do **not** advertise public `/cases` create/transition until care harden lands.

## 3. Environment variables

Copy `.env.example` → `.env` (or inject equivalent secrets on the host). Documented names:

| Variable | Role | Notes |
|:---------|:-----|:------|
| `DATABASE_URL` | Postgres SQLAlchemy URL | Local example uses placeholder credentials only; Live shell D4a may omit DB |
| `CORS_ORIGINS` | Extra browser origins (comma-separated) | Live: `http://52.74.255.88:3000` (plus code default `http://localhost:3000`) |
| `APP_ENV` | Runtime mode | Live container set `demo` |
| `FPT_API_KEY` / `FPT_BASE_URL` / `FPT_MODEL` | Agent explain path | See FPT doc; empty key = agent features unavailable |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` | Agent explain + Global Agent turns | Decision #22 / H29; empty key = provider fail-closed |
| `LANGSMITH_TRACING` / `LANGSMITH_API_KEY` / `LANGSMITH_PROJECT` | Optional agent tracing | Default **off**; redacted metadata only (`app.agent.tracing`); needs `pip install -e ".[observability]"` |
| `MAX_CONCURRENT_AGENT_RUNS` / `AGENT_RUN_TIMEOUT_SECONDS` | Agent limits | Defaults in `.env.example` |
| `NEXT_PUBLIC_API_BASE` / `BACKEND_URL` | Frontend → API | Live bake: `http://52.74.255.88:8000` |

**Production:** set the same names via AWS / host env on the container. Do not paste secret values here. Secret injection path for D4a: EC2 user-data / `docker run -e` only (no Secrets Manager yet).

## 4. CORS

Code (`backend/app/main.py`) allows:

- always: `http://localhost:3000`
- plus any origins in env `CORS_ORIGINS` (comma-separated)

**Live allowlist (D4a):** `http://localhost:3000`, `http://52.74.255.88:3000`

Verified 2026-07-18: `GET /health` with `Origin: http://52.74.255.88:3000` returns `Access-Control-Allow-Origin: http://52.74.255.88:3000`. Do not use `*` with credentials.

## 5. Database, schema, seed

Local DB via Compose (dev only; credentials are placeholders, not production secrets):

```powershell
docker compose up -d db
```

Backend lifespan calls `init_schemas()` when DB is reachable (`backend/app/main.py`).

### 5.1 D460 bootstrap — 460 SV + linked attendance + writers

One-shot operator path (idempotent imports; materialize/rollup replace by `source_id`):

```powershell
# From repo root; uses DATABASE_URL from .env / env
python scripts/bootstrap_d460.py
# or:
python scripts/bootstrap_d460.py --database-url postgresql+psycopg://...
```

Equivalent CLI steps (from `backend/`):

```text
# ensure head includes 20260719_ml_attendance_week
python -c "from app.dwh.migrate import upgrade_head; from app.config import get_settings; upgrade_head(get_settings().database_url)"
python -m app.dwh.cli import-semester
python -m app.dwh.cli import-attendance
python -m app.dwh.cli partition-advisor-demo   # 4×115 overlay; does not change package hash
python -m app.auth.cli seed          # AUTH_SEED_PASSWORD (+ optional AUTH_LECTURER_SEEDS)
python -m app.dwh.cli materialize-ml
python -m app.dwh.cli rollup-attendance-week
python -m app.dwh.cli readiness
```

**Expected checks (no PII):**

| Check | Expect |
|:--|:--|
| semester `student_dimension` | 460 |
| attendance events | 7360 · hash `acfb7d80dc3a…` |
| `LINKED_NAMESPACE_APPROVAL` | `approval:mvp-linked-v59-att:v1:acfb7d80dc3a` |
| `ml_term_snapshot` | 460 rows |
| `attendance_week` distinct students | 460 |
| readiness | `ready: true` |

**Live D460 (19/7 ~03:10 +07):** API `:d460` digest `sha256:4f1fb57b7e4f259fdf9751a88cd54f57316a92e70dbb088302308a5d05d1714a` · linked attendance **7360** (`acfb7d80…`) · `ml_term_snapshot` 460 · `attendance_week` 1840/460 · auth smoke **0** `attendance_source_unapproved` · evidence [23-d460…](../03-project/23-d460-live-redeploy-evidence.md). H39: anon `/review-cases` → 401; seed accounts `quanly`/`gvcn`/`demo`.

**Live 4 GVCN roster (19/7):** overlay `demo-class-partition-v1` 4×115 · API digest `sha256:831e0e23…` · `GET /advisor/roster` · accounts `duy.bk`/`hoang.nv`/`trang.pt`/`giang.nt` · evidence [24-d460…](../03-project/24-d460-four-gvcn-roster-evidence.md). **Vercel FE** redeploy needed for `/advisor/roster` rewrite + server roster UI.

**If re-bootstrap:** (1) image with `/data/approved` fixtures + writers, (2) env `LINKED_NAMESPACE_APPROVAL`, (3) on `snapshot_conflict` → clear attendance `source_id` rows **after** `upgrade_head` (separate tx per table), (4) import + materialize + rollup. SSM helpers: `deploy/aws/ssm-d460-redeploy-api.json`, `ssm-d460-bootstrap.json`.

**Live D4a historical:** early shell had no Postgres; D4b+ reports `database: true`. Seed/import remains operator CLI — not automatic in `user-data.sh`.

## 6. Health check

API exposes:

```http
GET /health
```

Expected shape: `status`, `service`, `database` boolean — see `backend/app/main.py` and `backend/tests/test_health.py`.

**Verify locally:**

```powershell
Invoke-RestMethod http://localhost:8000/health
```

**Live (D4a) — exact command:**

```powershell
Invoke-RestMethod http://52.74.255.88:8000/health
```

**Observed 2026-07-18 (~06:05 +07):**

```json
{"status":"ok","service":"silent-shield","database":false}
```

FE shell:

```powershell
Invoke-WebRequest http://52.74.255.88:3000/dashboard -UseBasicParsing
```

Expected: HTTP 200 (home `/` may 307 → `/dashboard`).

## 7. Smoke checklist

| # | Check | Pass criteria | Status |
|:-:|:------|:--------------|:-------|
| 1 | Live UI loads | FE origin reachable; no PII in URL | **Pass D4b** — `http://52.74.255.88:3000` (`/login` `/dashboard` 200) |
| 2 | `GET /health` on Live API | `status` ok; document DB flag | **Pass D4b** — `database: true` |
| 3 | List → case (anonymous) | Public `ReviewCase` fields only | **Pass D4b** — `/review-cases` state=ok n=50; detail band only |
| 4 | Care copy / `insufficient_data` | Matches Ethics/PRD | FE fail-closed + Live happy path; UAT → A05 |
| 5 | Agent (if enabled) | Explain-only via API/OpenAPI | Backend H26 Done; **not** FE Agent UI; Live FPT optional/SKIP |

Independent smoke owner from P2: Văn Hải (`V07`). Hoàng owns first Live shell evidence on `D4a`.

## 8. Rollback / fallback

**Known-good revision IDs (D4b product — keep D4a digests for rollback):**

| Artifact | ID |
|:---------|:---|
| EC2 instance | `i-0b0576945d080cb3f` |
| AMI | `ami-0b31875bb70b82eb2` |
| Elastic IP allocation | `eipalloc-09066880c09305fbe` → `52.74.255.88` |
| API image digest (D460) | `sha256:4f1fb57b7e4f259fdf9751a88cd54f57316a92e70dbb088302308a5d05d1714a` (`:d460`) |
| API image digest (D4r rollback) | `sha256:2b01b24a233e374b655fab55bf8bf9be2ff886437c202a7a9b51e9d957f256a1` (`:d4r`) |
| API image digest (D4b) | `sha256:bab21546c5ce4fb24277bcb59e9276416a956dabf6168b6ce0a2330cd11ae58a` (`:d4b`) |
| FE image digest (D4b) | `sha256:70eb44b5aab652626aa695631ed5ac4d8158316a29f369e34f61b4f0d43a35fe` (`:d4b`) |
| API image digest (D4a rollback) | `sha256:7a6ba16516bcc33beb58f4497f0583b220061e2f502f7ff913656319c523a23b` (`:d4a`) |
| FE image digest (D4a rollback) | `sha256:58ccf51321418291ba8ac44b9034328e56542963f3dadb3764ef8539554c5973` (`:d4a`) |
| Security group | `sg-0c88406bc7b7fd0d6` |

**Rollback procedure (no secrets):**

1. Keep previous `:d4a` digests above before promoting a new tag.
2. On smoke fail: SSM/SSH to instance → `docker pull` last-good digest → recreate `silent-shield-api` / `silent-shield-web` containers → re-run `/health` + FE GET.
3. Or stop/terminate bad instance and relaunch from same AMI + user-data (`deploy/aws/user-data.sh`) with same EIP association.
4. If data seed is wrong (post-D4b): restore DB snapshot or re-import last good fixture hash — *do not* invent synthetic rows on MVP path.
5. After `V07`/`A05` defects: fix → **`D4r`** redeploy → re-smoke before `V05`.
6. Fallback narrative if agent/LLM is down: UI + model/API review path still works; agent is explain-only.

## 9. Local vs Live verify

| Stage | Command / action |
|:------|:-----------------|
| Dev fast | `.\scripts\verify.ps1 -Quick` |
| Handoff / gate | `.\scripts\verify.ps1` |
| Local API | `uvicorn app.main:app` from `backend/` (see backend README) |
| Live shell | `Invoke-RestMethod http://52.74.255.88:8000/health` · FE `http://52.74.255.88:3000` — also [release evidence](../03-project/07-release-evidence.md) |

## 10. Finalize checklist (`D4a` / `D4b` owner)

- [x] Live frontend URL and API base (no secrets) — D4a
- [x] CORS allowlist matches Live origin(s) — D4a
- [x] Secret injection path documented (where keys live — not the values) — container `-e` / local `.env`
- [x] Seed/import steps + fixture provenance hash — **D4b** (sem `73274079…` / att `78d7153f…`)
- [x] Exact health + shell smoke commands with expected output — D4a
- [x] Rollback steps with revision IDs — D4a + D4b digests
- [x] Cross-link evidence rows in `07-release-evidence.md` — D4a shell + **D4b**
- [x] Product list→case smoke — **D4b Done**

## 11. H27 — Vercel frontend (candidate; HTTPS-safe API)

**Topology:** Browser → `https://abg-team.vercel.app` (Next.js) → rewrite/proxy → Live API `http://52.74.255.88:8000`. Browser must **not** call the HTTP API origin directly from an HTTPS page (mixed content).

| Concern | Value |
|:--------|:------|
| Vercel project | `abg-team` · Root Directory `frontend` · Framework Next.js |
| Production URL | `https://abg-team.vercel.app` |
| API path | Same-origin (`NEXT_PUBLIC_API_BASE` empty) + `rewrites` in `frontend/next.config.js` |
| Rewrite target | `BACKEND_URL` or default Live API when `VERCEL=1` |
| Secrets on Vercel | **None** — no `FPT_API_KEY` / `DATABASE_URL` on the FE project |
| Optional Dashboard env | `BACKEND_URL=http://52.74.255.88:8000` · `NEXT_PUBLIC_API_BASE=` (empty) |
| Rollback | Vercel → Deployments → prior Ready deployment → Promote / Rollback |
| Submission Live URL | **`https://abg-team.vercel.app`** (flipped in `D4r` 18/7 tối; EC2 FE `:3000` no longer submission URL) |

**Smoke (incognito):**

```powershell
# Page
Invoke-WebRequest https://abg-team.vercel.app/login -UseBasicParsing | Select-Object StatusCode
# Same-origin API proxy (must be JSON from Live backend, not HTML)
Invoke-RestMethod https://abg-team.vercel.app/review-cases | Select-Object state, @{n='n';e={$_.items.Count}}
Invoke-RestMethod https://abg-team.vercel.app/health
```

Pass: login UI loads; `/review-cases` returns `state=ok` with items; dashboard list→detail works; DevTools shows no mixed-content errors.

## 12. Weekly worker / scheduler (H28a lock — Decision #23)

> **Status:** target ops shape locked; `D6` implements deploy. Do **not** embed APScheduler in the FastAPI web process.

```text
EventBridge schedule (or approved cron host)
  → SQS queue (or equivalent job queue)
  → worker process
  → WeeklyWorkflowService (same entry as CLI `weekly run`)
```

| Concern | Locked choice |
|:--------|:--------------|
| Trigger | External only (EventBridge preferred; approved cron host acceptable) |
| Auth | Service credential / IAM role on worker — not browser JWT |
| Idempotency | Manifest content hash + idempotency key; duplicate → no-op |
| Kill switches | Separate flags: ingestion, case materialization, briefing publish, OpenAI calls |
| OpenAI | **Not** on critical weekly DAG path; worker must succeed with provider off |
| Secrets | `OPENAI_API_KEY` / DB URL only on API+worker hosts — never on Vercel FE |

CLI local/demo replay uses the same service with approved pseudonymous bytes. Public upload endpoints remain forbidden.
