# Backend

```powershell
pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest -q
```

`app/ml/early_warning/` — feature/prediction contracts (M01/M02 mở rộng).
