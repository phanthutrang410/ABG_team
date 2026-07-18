# D3 — GitHub public + PII/secret scan

> **Owner:** Hoàng · **Gate:** CP2 · **Captured at:** 2026-07-18T03:58+07

## Outcome

Repo public, anonymous URL mở được không cần đăng nhập; tree tracked đã quét PII/secret; SĐT thành viên đã gỡ khỏi docs công khai.

## Evidence (template H05b)

```text
Item:           GitHub public + PII/secret scan
Gate:           CP2
Task nguồn:     D3
Owner evidence: Hoàng
Captured at:    2026-07-18T03:58+07
Evidence type:  url + scan-log
Evidence ref:   https://github.com/phanthutrang410/ABG_team ;
                docs/03-project/10-d3-github-pii-secret-scan.md ;
                scripts/d3_pii_secret_scan.py ;
                .gitleaks.toml
Private ref:    .ai-log-private/d3-pii-secret-scan.json ;
                .ai-log-private/d3-gitleaks-history.json
                (gitignored — không commit)
What verified:  API visibility=public; anonymous HTML/API 200;
                tracked-tree scan: 0 secret pattern, 0 SĐT sau remediation;
                .env + reference-Learning-Analytics-AI/ vẫn gitignore
Redactions:      24 findings SĐT trên hai bản khảo sát trùng đã được redact;
                bản canonical còn lại: docs/03-project/02-team.md
BLOCKED →:
Status:         [x] done
```

## Checks run

| Check | Result |
|:--|:--|
| `GET https://api.github.com/repos/phanthutrang410/ABG_team` | `private=false`, `visibility=public` |
| Anonymous repo page (no auth) | HTTP 200 |
| `git check-ignore -v .env` | ignored via `.gitignore` |
| `git check-ignore -v reference-Learning-Analytics-AI/` | ignored |
| `git ls-files .env` | not tracked (only `.env.example`) |
| `python scripts/d3_pii_secret_scan.py` (tracked files) | **before fix:** 24 `vn_mobile` in team docs; **after fix:** 0 findings |
| `gitleaks detect` (git history) | 1 hit: false positive `generic-api-key` on text `GPU/Colab/Kaggle/RunPod` in survey doc — allowlisted in `.gitleaks.toml` |
| `gitleaks detect --no-git` (workdir) | Hits in **gitignored** paths only (local `.env`, `reference-Learning-Analytics-AI/`); not part of public tree |

## Remediation in this task

1. Redact member phone numbers from public team/survey Markdown.
2. Add repeatable scan script + gitleaks allowlist for known false positives / ignored paths.
3. Record public + private scan artifacts (private under `.ai-log-private/`).

## Known gaps / residual risk

- **Git history** still contains pre-redaction SĐT in older commits. Task D3 does **not** rewrite history (destructive). Accept for CP2; optional follow-up: `git filter-repo` / BFG nếu BTC yêu cầu purge history.
- Local `.env` may hold real keys on developer machines — must stay gitignored; rotate if ever pasted into chat/logs.
- README final polish remains `H09` after `D4r`.

## Unblocks

- `D4` (still also needs `H02`, `G02`)
- `V07` (still also needs `D4`)
- `V05` / `V06` (partial — still need later gates)
