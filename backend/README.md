# Backend

```powershell
pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest -q
```

## Database migrate (H19 `dwh`)

Requires Postgres (`docker compose up -d db` from repo root).

```powershell
# Apply empty MVP dwh schema
alembic upgrade head

# Targeted migrate/repeatability tests (creates ephemeral DB, then drops it)
python -m pytest -q tests/test_dwh_migrate.py
```

Revision: `20260718_h19_dwh` — seven empty tables in schema `dwh`; no seed/import (H20).

## ML (M01 quarantine)

Legacy `app/ml/early_warning/` (synthetic generator, attendance theo tuần, `synth_socioeconomic_group`/`synth_ethnicity_group`, raw `risk_score`) đã bị gỡ khỏi MVP path theo M01. Contract scoring hiện hành: `app/contracts/scoring.py` (`ScoringFeatures`) theo [Data-ML contract](../docs/04-engineering/08-data-ml-scoring-fairness-contract.md). Guard: `tests/test_m01_legacy_quarantine.py` fail nếu feature attendance-week/synth group/raw risk quay lại scoring hoặc MVP path import lại module legacy. Baseline M02 sẽ build trên `ScoringFeatures` sau khi nguồn được duyệt (M05b/M06).
