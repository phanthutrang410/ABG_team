"""CLI for H20 `dwh` import + readiness (not a public HTTP API).

Usage (from backend/):
  python -m app.dwh.cli import-attendance
  python -m app.dwh.cli import-semester
  python -m app.dwh.cli readiness
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.config import get_settings
from app.dwh.importer import import_attendance, import_semester, readiness_report


def _print_result(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.dwh.cli", description="H20 dwh importer")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Postgres SQLAlchemy URL (default: app settings DATABASE_URL)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_att = sub.add_parser("import-attendance", help="Import H15 mvp-attendance-over-time fixture")
    p_att.add_argument("--path", type=Path, default=None, help="Override attendance JSON path")

    p_sem = sub.add_parser("import-semester", help="Import M05b semester via env/path")
    p_sem.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Override SILENT_SHIELD_SEMESTER_SOURCE_PATH",
    )

    sub.add_parser("readiness", help="Print non-PII readiness report")

    args = parser.parse_args(argv)
    database_url = args.database_url or get_settings().database_url

    if args.command == "import-attendance":
        result = import_attendance(database_url, data_path=args.path)
    elif args.command == "import-semester":
        result = import_semester(database_url, source_path=args.path)
    elif args.command == "readiness":
        _print_result(readiness_report(database_url))
        return 0
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
