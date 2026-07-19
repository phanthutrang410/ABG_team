"""CLI for H20 `dwh` import + readiness + ML/week writers (not a public HTTP API).

Usage (from backend/):
  python -m app.dwh.cli import-attendance
  python -m app.dwh.cli import-semester
  python -m app.dwh.cli partition-advisor-demo
  python -m app.dwh.cli readiness
  python -m app.dwh.cli materialize-ml [--source-id …]
  python -m app.dwh.cli rollup-attendance-week [--source-id …]

Defaults (no env required):
  data/approved/attendance/mvp_attendance_over_time.json
  data/approved/semester/domain_package.json
  materialize-ml → v59-empty-program-students
  rollup-attendance-week → mvp-attendance-over-time

Optional: SILENT_SHIELD_SEMESTER_SOURCE_PATH → raw V59 or alternate domain package.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.dwh.attendance_week_rollup import (
    DEFAULT_ATTENDANCE_SOURCE_ID,
    rollup_attendance_weeks,
)
from app.dwh.importer import SEMESTER_SOURCE_ID, import_attendance, import_semester, readiness_report
from app.dwh.ml_materializer import materialize_ml_term_snapshot
from app.dwh.partition_demo import partition_advisor_assignments
from app.dwh.weekly_workflow import run_weekly_from_bytes


def _print_result(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def _session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine(database_url, pool_pre_ping=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.dwh.cli", description="H20/H31 dwh tools")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Postgres SQLAlchemy URL (default: app settings DATABASE_URL)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_att = sub.add_parser("import-attendance", help="Import H15 mvp-attendance-over-time fixture")
    p_att.add_argument("--path", type=Path, default=None, help="Override attendance JSON path")

    p_sem = sub.add_parser(
        "import-semester",
        help="Import approved semester domain package (default under data/approved/semester/)",
    )
    p_sem.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Override default domain package or SILENT_SHIELD_SEMESTER_SOURCE_PATH",
    )

    sub.add_parser("readiness", help="Print non-PII readiness report")

    p_ml = sub.add_parser(
        "materialize-ml",
        help="Materialize M02 scoring into dwh.ml_term_snapshot",
    )
    p_ml.add_argument(
        "--source-id",
        default=SEMESTER_SOURCE_ID,
        help=f"Semester source_id (default: {SEMESTER_SOURCE_ID})",
    )

    p_week = sub.add_parser(
        "rollup-attendance-week",
        help="Roll up attendance_event into dwh.attendance_week (student × ISO Monday)",
    )
    p_week.add_argument(
        "--source-id",
        default=DEFAULT_ATTENDANCE_SOURCE_ID,
        help=f"Attendance source_id (default: {DEFAULT_ATTENDANCE_SOURCE_ID})",
    )

    p_part = sub.add_parser(
        "partition-advisor-demo",
        help="Overlay advisor_assignment into 4×115 demo scopes (no package hash change)",
    )
    p_part.add_argument(
        "--source-id",
        default=SEMESTER_SOURCE_ID,
        help=f"Semester source_id (default: {SEMESTER_SOURCE_ID})",
    )

    p_weekly = sub.add_parser("weekly", help="H31 weekly workflow CLI")
    weekly_sub = p_weekly.add_subparsers(dest="weekly_command", required=True)
    p_run = weekly_sub.add_parser("run", help="Stage/promote approved artifact bytes")
    p_run.add_argument("--dataset-key", required=True)
    p_run.add_argument("--path", type=Path, required=True, help="Approved JSON artifact path")
    p_run.add_argument("--approval-id", required=True)
    p_run.add_argument("--idempotency-key", default=None)

    args = parser.parse_args(argv)
    database_url = args.database_url or get_settings().database_url

    if args.command == "import-attendance":
        result = import_attendance(database_url, data_path=args.path)
    elif args.command == "import-semester":
        result = import_semester(database_url, source_path=args.path)
    elif args.command == "partition-advisor-demo":
        factory = _session_factory(database_url)
        with factory() as session:
            part = partition_advisor_assignments(session, source_id=args.source_id)
            if part.status == "partitioned":
                session.commit()
            else:
                session.rollback()
        _print_result(
            {
                "status": part.status,
                "source_id": part.source_id,
                "scope_source": part.scope_source,
                "counts_by_advisor": part.counts_by_advisor,
                "total_students": part.total_students,
                "manifest_sha256": part.manifest_sha256,
                "reason_codes": list(part.reason_codes),
                "detail": part.detail,
            }
        )
        return 0 if part.status == "partitioned" else 1
    elif args.command == "readiness":
        _print_result(readiness_report(database_url))
        return 0
    elif args.command == "materialize-ml":
        factory = _session_factory(database_url)
        with factory() as session:
            result = materialize_ml_term_snapshot(session, args.source_id)
            if result.status == "materialized":
                session.commit()
            else:
                session.rollback()
        _print_result(
            {
                "status": result.status,
                "source_id": result.source_id,
                "row_counts": result.row_counts,
                "reason_codes": result.reason_codes,
                "detail": result.detail,
            }
        )
        return 0 if result.status == "materialized" else 1
    elif args.command == "rollup-attendance-week":
        factory = _session_factory(database_url)
        with factory() as session:
            result = rollup_attendance_weeks(session, args.source_id)
            if result.status == "rolled_up":
                session.commit()
            else:
                session.rollback()
        _print_result(
            {
                "status": result.status,
                "source_id": result.source_id,
                "row_counts": result.row_counts,
                "reason_codes": result.reason_codes,
                "detail": result.detail,
            }
        )
        return 0 if result.status == "rolled_up" else 1
    elif args.command == "weekly":
        if args.weekly_command == "run":
            content = args.path.read_bytes()
            wf = run_weekly_from_bytes(
                database_url,
                dataset_key=args.dataset_key,
                content_bytes=content,
                approval_id=args.approval_id,
                idempotency_key=args.idempotency_key,
            )
            _print_result(
                {
                    "status": wf.status,
                    "run_id": wf.run_id,
                    "snapshot_id": wf.snapshot_id,
                    "reason_codes": wf.reason_codes,
                    "detail": wf.detail,
                }
            )
            return 0 if wf.status in ("succeeded", "duplicate") else 1
        parser.error(f"unknown weekly command {args.weekly_command}")
        return 2
    else:
        parser.error(f"unknown command {args.command}")
        return 2

    _print_result(
        {
            "status": result.status,
            "source_id": result.source_id,
            "reason_codes": result.reason_codes,
            "snapshot_sha256": result.snapshot_sha256,
            "row_counts": result.row_counts,
            "detail": result.detail,
        }
    )
    if result.status in ("imported", "idempotent_skip"):
        return 0
    if result.status == "skipped":
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
