# D460 — 4 GVCN roster overlay (Live)

> **Date:** 2026-07-19 · **Owner:** Hoàng  
> **Scope:** Overlay `advisor_assignment` 4×115 + auth seed 4 GVCN + `GET /advisor/roster` + FE classes path.

## Chốt

| Mục | Giá trị |
|:--|:--|
| API image | `silent-shield-api:d460` · digest `sha256:831e0e23baca7a459ab6f7a0307a57b9c1b89db6fdf48a3ce4725c92a7eb7b75` |
| Overlay | `scope_source=demo-class-partition-v1` · 4×115 · manifest SHA unchanged `73274079…` |
| Advisor scopes | `a-gvcn-duy-01` / `a-gvcn-hoang-02` / `a-gvcn-trang-03` / `a-gvcn-giang-04` |
| Accounts | `duy.bk` / `hoang.nv` / `trang.pt` / `giang.nt` (+ legacy `quanly`/`gvcn`/`demo`) |
| Passwords | SSM `/silent-shield/d460/AUTH_LECTURER_SEEDS` (+ `AUTH_SEED_PASSWORD=demo123` for core) |
| Roster | `GET /advisor/roster` · each GVCN n=115 · pairwise disjoint |

## Smoke

- Partition: 4×115, `reason_codes=[]`
- Seed: `quanly, gvcn, demo, duy.bk, hoang.nv, trang.pt, giang.nt`
- Login + roster: all four `roster_ok 115` · `all_lecturer_rosters_disjoint_ok`
- Health: `ok` · `database: true`
- Anon `/advisor/roster` → 401

## FE

Production `AdvisorClassesWorkspace` calls `/advisor/roster` (rewrite in `next.config.mjs`). Vercel production redeploy required for Live browser path.
