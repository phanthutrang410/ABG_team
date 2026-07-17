# Deploy / ops runbook — Silent Shield MVP

> **D4a Live shell (2026-07-18):** hostnames, health smoke, CORS, and rollback IDs below are real.
> Product list→case smoke remains **`D4b`** (after H02/G02). Do not treat this runbook as D4b evidence.
>
> Owner: Hoàng · Tasks: **H07** (draft) → **D4a** (Live shell) · Region: `ap-southeast-1` · Account deploy user: IAM `chungang` (no secrets in this doc).

## 0. Secrets policy

- **Never** put real API keys, tokens, passwords, connection strings with credentials, or authenticated Live URLs into this doc, git, slides, video, or AI log.
- Use [`.env.example`](../../.env.example) as the variable *names* template. Real values live only in local `.env` / host secrets (gitignored).
- Public demo must stay anonymous: no PII, no advisor personal contacts, no raw scores.

## 1. Source of truth (structure)

| Concern | Canonical doc |
|:--------|:--------------|
| Containers, data flow, trust/care boundary | [05-system-architecture.md](05-system-architecture.md) |
| Case transitions / forbidden actions | [Process §4](../02-product/03-process.md) |
| Stack + BE host choice | [Decisions](../03-project/04-decisions.md) #5–6 (FastAPI + Next.js; BE on **AWS**, not Render) |
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
| `OPENAI_API_KEY` | Optional backup LLM | Empty unless backup path enabled |
| `MAX_CONCURRENT_AGENT_RUNS` / `AGENT_RUN_TIMEOUT_SECONDS` | Agent limits | Defaults in `.env.example` |
| `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` / `LANGCHAIN_PROJECT` | Optional tracing | Keep off unless needed; no keys in git |
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

**Live D4a:** no Postgres attached; `/health` reports `"database": false`. Seed/import for product demo stays **`H08` / `H20` / D4b** — not claimed here.

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
| 1 | Live UI loads | FE origin reachable; no PII in URL | **Pass D4a** — `http://52.74.255.88:3000` (dashboard 200) |
| 2 | `GET /health` on Live API | `status` ok; document DB flag | **Pass D4a** — `database: false` |
| 3 | List → case (anonymous) | Public `ReviewCase` fields only | **Deferred → D4b** (needs H02/G02); do not claim |
| 4 | Care copy / `insufficient_data` | Matches Ethics/PRD | **Deferred → D4b** |
| 5 | Agent (if enabled) | Explain-only | **Deferred → D4b** / agent tasks |

Independent smoke owner from P2: Văn Hải (`V07`). Hoàng owns first Live shell evidence on `D4a`.

## 8. Rollback / fallback

**Known-good revision IDs (D4a shell):**

| Artifact | ID |
|:---------|:---|
| EC2 instance | `i-0b0576945d080cb3f` |
| AMI | `ami-0b31875bb70b82eb2` |
| Elastic IP allocation | `eipalloc-09066880c09305fbe` → `52.74.255.88` |
| API image digest | `sha256:7a6ba16516bcc33beb58f4497f0583b220061e2f502f7ff913656319c523a23b` (`:d4a`) |
| FE image digest | `sha256:58ccf51321418291ba8ac44b9034328e56542963f3dadb3764ef8539554c5973` (`:d4a`) |
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
- [ ] Seed/import steps + fixture provenance hash — **D4b / H08**
- [x] Exact health + shell smoke commands with expected output — D4a
- [x] Rollback steps with revision IDs — D4a
- [x] Cross-link evidence rows in `07-release-evidence.md` — D4a shell row
- [ ] Product list→case smoke — **D4b**
