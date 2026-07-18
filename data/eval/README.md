# Eval synthetic lane (decision #26 / M09)

Pseudonymous **ML train/eval** packages only. **Not** on MVP H20 / Live demo path.

Program mix (khoa / ngành / lớp) weighted từ approved EPU package  
`data/approved/semester/domain_package.json` → catalog  
`backend/app/ml/eval_synthetic/epu_program_catalog.json`.

## Smoke (committed, n=12)

```text
data/eval/smoke/
```

## Full (local, n=2000, gitignored)

```powershell
python scripts/generate_ml_eval_package.py --full --seed 42 `
  --eda-report data/eval/full/eda_summary.json `
  --eval-report data/eval/full/eval_report.json
```

EDA: [docs/04-engineering/16-m09-eval-synthetic-eda.md](../docs/04-engineering/16-m09-eval-synthetic-eda.md)

Do **not** import via `python -m app.dwh.cli import-semester`.
