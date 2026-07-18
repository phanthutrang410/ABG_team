#!/usr/bin/env python3
"""Bootstrap approved DWH data for 460-student MVP deploy (D460-05).

Idempotent sequence for a target DATABASE_URL:

  alembic upgrade head
  → import-semester
  → import-attendance
  → auth seed (optional)
  → materialize-ml
  → rollup-attendance-week

Usage (from repo root or backend/):

  python scripts/bootstrap_d460.py
  python scripts/bootstrap_d460.py --database-url postgresql+psycopg://...
  python scripts/bootstrap_d460.py --skip-auth-seed

Does not print PII. Exit 0 only when readiness.ready and ml_term_snapshot==460.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_BACKEND = _REPO / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="D460 bootstrap: import + materialize 460")
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--skip-auth-seed", action="store_true")
    parser.add_argument("--skip-materialize", action="store_true")
    parser.add_argument("--skip-rollup", action="store_true")
    args = parser.parse_args(argv)

    from app.config import get_settings
    from app.dwh.importer import import_attendance, import_semester, readiness_report
    from app.dwh.migrate import upgrade_head
    from sqlalchemy import create_engine, func, select
    from sqlalchemy.orm import Session

    database_url = args.database_url or get_settings().database_url
    upgrade_head(database_url)

    sem = import_semester(database_url)
    att = import_attendance(database_url)
    report = readiness_report(database_url)

    auth_detail = None
    if not args.skip_auth_seed:
        try:
            from app.auth.cli import seed_accounts
            from app.database import get_session_factory, init_schemas

            init_schemas()
            settings = get_settings()
            password = settings.auth_seed_password.get_secret_value()
            if not password.strip():
                auth_detail = {"status": "skipped", "detail": "AUTH_SEED_PASSWORD empty"}
            else:
                db = get_session_factory()()
                try:
                    touched = seed_accounts(db, password)
                    auth_detail = {"status": "seeded", "usernames": touched}
                finally:
                    db.close()
        except Exception as exc:  # noqa: BLE001 — seed optional on some envs
            auth_detail = {"status": "skipped", "detail": str(exc)}

    ml_result = None
    week_result = None
    engine = create_engine(database_url)
    try:
        with Session(engine) as session:
            if not args.skip_materialize:
                from app.dwh.ml_materializer import materialize_ml_term_snapshot

                ml_result = materialize_ml_term_snapshot(
                    session, source_id="v59-empty-program-students"
                )
                if ml_result.status == "materialized":
                    session.commit()
                else:
                    session.rollback()

            if not args.skip_rollup:
                from app.dwh.attendance_week_rollup import rollup_attendance_weeks

                week_result = rollup_attendance_weeks(
                    session, source_id="mvp-attendance-over-time"
                )
                if week_result.status == "rolled_up":
                    session.commit()
                else:
                    session.rollback()

            from app.dwh.models import AttendanceWeek, MlTermSnapshot

            n_ml = session.scalar(select(func.count()).select_from(MlTermSnapshot)) or 0
            n_week_students = (
                session.scalar(
                    select(func.count(func.distinct(AttendanceWeek.student_ref)))
                )
                or 0
            )
    finally:
        engine.dispose()

    payload = {
        "semester": {"status": sem.status, "row_counts": sem.row_counts},
        "attendance": {
            "status": att.status,
            "snapshot_sha256": att.snapshot_sha256,
            "row_counts": att.row_counts,
        },
        "readiness": report,
        "auth_seed": auth_detail,
        "materialize_ml": None
        if ml_result is None
        else {
            "status": ml_result.status,
            "row_counts": ml_result.row_counts,
            "reason_codes": ml_result.reason_codes,
        },
        "rollup_weeks": None
        if week_result is None
        else {
            "status": week_result.status,
            "row_counts": week_result.row_counts,
            "reason_codes": week_result.reason_codes,
        },
        "checks": {
            "ml_term_snapshot_rows": n_ml,
            "attendance_week_students": n_week_students,
            "expect_students": 460,
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))

    ok = (
        report.get("ready") is True
        and n_ml == 460
        and n_week_students == 460
        and (ml_result is None or ml_result.status == "materialized")
        and (week_result is None or week_result.status == "rolled_up")
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
