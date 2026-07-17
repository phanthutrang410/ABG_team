# Deploy / ops runbook — Silent Shield MVP

> **DRAFT from architecture — finalize when real env exists (`D4`).**
>
> Owner: Hoàng · Task: **H07** · Status: draft early from [system architecture](05-system-architecture.md).
>
> **Do not treat this as live deploy truth yet.** Concrete Live URL, hostnames, smoke command outputs, and rollback steps with real revision IDs are filled at **`D4`** (smoke lần 1) and re-checked at **`D4r`**. Until then, sections marked *TBD at D4* are intentional placeholders.

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
| Board / release loop | [Sprint](../03-project/03-sprint.md) (`D4` → `V07` → `D4r` → `V05`) |

If this runbook and architecture disagree, **architecture + decisions win** until H07 is revised with `D4` facts.

## 2. Target topology (from arch)

```text
[EPU extract approved] → data gate → fixtures → FastAPI (AWS)
                                              ↘ Next.js UI
                                              ↘ FPT agent (explain-only)
```

- **Backend:** FastAPI on AWS (decision #6). Exact instance/service name, region, and public hostname → *TBD at D4*.
- **Frontend:** Next.js; public origin for CORS and `NEXT_PUBLIC_API_BASE` → *TBD at D4*.
- **Database:** PostgreSQL (local compose uses `postgres:16`; production connection via `DATABASE_URL` secret — never commit).
- **LLM:** FPT AI Inference (`FPT_*`); keys never in repo.

## 3. Environment variables

Copy `.env.example` → `.env` (or inject equivalent secrets on the host). Documented names:

| Variable | Role | Notes |
|:---------|:-----|:------|
| `DATABASE_URL` | Postgres SQLAlchemy URL | Local example uses placeholder credentials only |
| `FPT_API_KEY` / `FPT_BASE_URL` / `FPT_MODEL` | Agent explain path | See FPT doc; empty key = agent features unavailable |
| `OPENAI_API_KEY` | Optional backup LLM | Empty unless backup path enabled |
| `MAX_CONCURRENT_AGENT_RUNS` / `AGENT_RUN_TIMEOUT_SECONDS` | Agent limits | Defaults in `.env.example` |
| `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` / `LANGCHAIN_PROJECT` | Optional tracing | Keep off unless needed; no keys in git |
| `NEXT_PUBLIC_API_BASE` / `BACKEND_URL` | Frontend → API | Local default `http://localhost:8000`; production URL *TBD at D4* |

**Production:** set the same names via AWS / host secret store. Do not paste values here.

## 4. CORS

Current code allows local UI origin only:

- `allow_origins=["http://localhost:3000"]` in `backend/app/main.py`

Before Live URL smoke (`D4`):

1. Add the **real** frontend origin(s) to CORS (exact list *TBD at D4*).
2. Confirm browser calls from Live UI reach `/health` and public case APIs without CORS errors.
3. Do not use `*` with credentials for production demo.

## 5. Database, schema, seed

Local DB via Compose (dev only; credentials are placeholders, not production secrets):

```powershell
docker compose up -d db
```

Backend lifespan calls `init_schemas()` when DB is reachable (`backend/app/main.py`).

**Seed / import for demo:**

- MVP path uses **approved EPU extract → normalized fixtures → import DTO (`H08`)**, not synthetic generators on the live path ([architecture](05-system-architecture.md), decision #12).
- Exact seed command, fixture revision hash, and “how many cases in queue” → *TBD at D4* after `H08` / data gate are Done.
- Never seed PII, personal emails, or `is_dropout_outcome` into public APIs.

## 6. Health check

API exposes:

```http
GET /health
```

Expected shape (local / when DB up): `status`, `service`, `database` boolean — see `backend/app/main.py` and `backend/tests/test_health.py`.

**Verify locally:**

```powershell
# with API running
Invoke-RestMethod http://localhost:8000/health
```

**Live URL health command** (hostname, TLS, expected JSON) → *TBD at D4*.

## 7. Smoke checklist (draft)

Minimum intent for `D4` / QA `V07` (fill concrete URLs and screenshots at deploy time):

| # | Check | Pass criteria | Status |
|:-:|:------|:--------------|:-------|
| 1 | Live UI loads (incognito) | No auth wall for public demo path; no PII in URL | *TBD at D4* |
| 2 | `GET /health` on Live API | `status` ok; document DB flag | *TBD at D4* |
| 3 | List → case (anonymous) | Public `ReviewCase` fields only; no raw score / outcome | *TBD at D4* |
| 4 | Care copy / `insufficient_data` | Matches Ethics/PRD; empty/stale handled | *TBD at D4* |
| 5 | Agent (if enabled) | Explain-only; refuses score/state changes | *TBD at D4* |

Independent smoke owner from P2: Văn Hải (`V07`). Hoàng owns first Live smoke evidence on `D4`.

## 8. Rollback / fallback (draft)

Intent locked by release loop; **procedure details TBD at D4**:

1. Keep previous known-good image/revision ID before promoting a new deploy.
2. On smoke fail: revert BE and/or FE to last good revision; re-run `/health` + list→case.
3. If data seed is wrong: restore DB snapshot or re-import last good fixture hash — *do not* invent synthetic rows on MVP path.
4. After `V07`/`A05` defects: fix → **`D4r`** redeploy → re-smoke before `V05` submit.
5. Fallback narrative for demo if agent/LLM is down: UI + model/API review path still works; agent is explain-only.

Record actual rollback commands and revision IDs in release evidence at `D4`/`D4r` — not in this draft with invented hosts.

## 9. Local vs Live verify

| Stage | Command / action |
|:------|:-----------------|
| Dev fast | `.\scripts\verify.ps1 -Quick` |
| Handoff / gate | `.\scripts\verify.ps1` |
| Local API | `uvicorn app.main:app` from `backend/` (see backend README) |
| Live | *TBD at D4* — document Live URL (no credentials) in [release evidence](../03-project/07-release-evidence.md) |

## 10. Finalize checklist (`D4` owner)

When real env exists, update this runbook in the same handoff as Live smoke:

- [ ] Live frontend URL and API base (no secrets)
- [ ] CORS allowlist matches Live origin(s)
- [ ] Secret injection path documented (where keys live — not the values)
- [ ] Seed/import steps + fixture provenance hash
- [ ] Exact health + smoke commands with expected output
- [ ] Rollback steps with revision IDs
- [ ] Cross-link evidence rows in `07-release-evidence.md`

Until those boxes are checked, keep the banner at the top of this file.
