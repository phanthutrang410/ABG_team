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

`app/ml/early_warning/` — feature/prediction contracts (M01/M02 mở rộng).
