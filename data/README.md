# Data layout — Silent Shield

| Path | In git? | Role |
|:---|:---|:---|
| [`approved/`](approved/) | Yes | Pseudonymous M06 domain packages for team import (`H20`) |
| [`eval/`](eval/) | Yes (README / samples only) | Decision #26 ML eval lane — proposal path; generator `M09` chưa ship |
| [`synthetic/`](synthetic/) | Quarantine only | Legacy synthetic removed (M01) — do not regenerate |

## Bootstrap (sau `git pull`)

```powershell
docker compose up -d db
Push-Location backend
python -m app.dwh.migrate   # or: alembic upgrade head via migrate helper
python -m app.dwh.cli import-attendance
python -m app.dwh.cli import-semester
python -m app.dwh.cli readiness
Pop-Location
```

Không cần `SILENT_SHIELD_SEMESTER_SOURCE_PATH` cho đường mặc định — semester đọc `data/approved/semester/domain_package.json`.

## Cấm commit

- Raw V59 / `reference-Learning-Analytics-AI/`
- Map `MSSV` ↔ `student_ref`, tên, email, SĐT, token crawl
- Legacy synthetic CSV / marker `"synthetic"` trên MVP path
