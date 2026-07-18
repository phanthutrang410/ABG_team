"""Export approved MVP domain packages to flat CSV for analysis.

Reads git-safe fixtures under data/approved/ (no raw V59 / PII).
Writes UTF-8 CSV (BOM) under data/exports/csv/.

Usage (repo root):
  python scripts/export_approved_to_csv.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SEMESTER_PKG = REPO_ROOT / "data" / "approved" / "semester" / "domain_package.json"
ATTENDANCE_PKG = (
    REPO_ROOT / "data" / "approved" / "attendance" / "mvp_attendance_over_time.json"
)
ATTENDANCE_MANIFEST = (
    REPO_ROOT
    / "data"
    / "approved"
    / "attendance"
    / "mvp_attendance_source_manifest.json"
)
ATTENDANCE_DQ = (
    REPO_ROOT
    / "data"
    / "approved"
    / "attendance"
    / "mvp_attendance_data_quality_report.json"
)
OUT_DIR = REPO_ROOT / "data" / "exports" / "csv"

TABLE_KEYS = (
    "student_dimension",
    "term_grade",
    "academic_status",
    "advisor_assignment",
)


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_rows(path: Path, rows: list[dict[str, object]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return 0
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: (
                        json.dumps(v, ensure_ascii=False)
                        if isinstance(v, (list, dict))
                        else v
                    )
                    for k, v in row.items()
                }
            )
    return len(rows)


def _flatten_scalar_dict(prefix: str, data: dict[str, object]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in data.items():
        col = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
        if isinstance(value, dict):
            nested_scalars = {
                k: v for k, v in value.items() if not isinstance(v, (list, dict))
            }
            if nested_scalars and len(nested_scalars) == len(value):
                for nk, nv in nested_scalars.items():
                    out[f"{col}.{nk}"] = nv
            else:
                out[col] = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, list):
            continue
        else:
            out[col] = value
    return out


def main() -> int:
    semester = _load_json(SEMESTER_PKG)
    if not isinstance(semester, dict):
        raise SystemExit(f"Unexpected semester package type: {type(semester)}")

    summary: list[tuple[str, int]] = []

    for key in TABLE_KEYS:
        rows = semester.get(key)
        if not isinstance(rows, list):
            raise SystemExit(f"Missing list table: {key}")
        n = _write_rows(OUT_DIR / f"{key}.csv", rows)
        summary.append((f"{key}.csv", n))

    manifest = semester.get("source_manifest")
    if isinstance(manifest, dict):
        n = _write_rows(OUT_DIR / "semester_source_manifest.csv", [manifest])
        summary.append(("semester_source_manifest.csv", n))

    dq = semester.get("data_quality_report")
    if isinstance(dq, dict):
        flat = _flatten_scalar_dict("", dq)
        n = _write_rows(OUT_DIR / "semester_data_quality_summary.csv", [flat])
        summary.append(("semester_data_quality_summary.csv", n))
        term_cov = dq.get("term_coverage")
        if isinstance(term_cov, list):
            n = _write_rows(OUT_DIR / "semester_term_coverage.csv", term_cov)
            summary.append(("semester_term_coverage.csv", n))

    attendance = _load_json(ATTENDANCE_PKG)
    if not isinstance(attendance, dict):
        raise SystemExit(f"Unexpected attendance package type: {type(attendance)}")
    events = attendance.get("events")
    if not isinstance(events, list):
        raise SystemExit("Attendance package missing events list")
    n = _write_rows(OUT_DIR / "attendance_events.csv", events)
    summary.append(("attendance_events.csv", n))

    att_meta = {
        "source_id": attendance.get("source_id"),
        "schema_version": attendance.get("schema_version"),
        "event_count": len(events),
    }
    n = _write_rows(OUT_DIR / "attendance_package_meta.csv", [att_meta])
    summary.append(("attendance_package_meta.csv", n))

    if ATTENDANCE_MANIFEST.is_file():
        man = _load_json(ATTENDANCE_MANIFEST)
        if isinstance(man, dict):
            n = _write_rows(OUT_DIR / "attendance_source_manifest.csv", [man])
            summary.append(("attendance_source_manifest.csv", n))

    if ATTENDANCE_DQ.is_file():
        adq = _load_json(ATTENDANCE_DQ)
        if isinstance(adq, dict):
            n = _write_rows(
                OUT_DIR / "attendance_data_quality_summary.csv",
                [_flatten_scalar_dict("", adq)],
            )
            summary.append(("attendance_data_quality_summary.csv", n))

    print(f"Wrote CSVs under {OUT_DIR.relative_to(REPO_ROOT)}")
    for name, count in summary:
        print(f"  {name}: {count} row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
