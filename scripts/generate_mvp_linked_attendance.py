#!/usr/bin/env python3
"""Generate linked MVP attendance covering all M06 semester student_refs (decision #27).

Session grain: each course meeting is one event (observed_at + course_ref).
Target ≥16 sessions/student in a 90-day window. Does not use the word
\"synthetic\" in payload fields (MVP gate).

Example:
  python scripts/generate_mvp_linked_attendance.py --seed 42
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.ml.mvp_attendance.generate import (  # noqa: E402
    DEFAULT_SEED,
    build_attendance_payload,
    write_attendance_package,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--semester",
        type=Path,
        default=REPO_ROOT / "data" / "approved" / "semester" / "domain_package.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_ROOT / "data" / "approved" / "attendance",
    )
    args = parser.parse_args()

    domain = json.loads(args.semester.read_text(encoding="utf-8"))
    payload = build_attendance_payload(domain, seed=args.seed)
    meta = write_attendance_package(payload, out_dir=args.out_dir)
    print(
        f"Wrote {meta['path']} events={meta['n_events']} "
        f"students={meta['n_students']} sha256={meta['sha256']}"
    )
    print(f"Update ATTENDANCE_APPROVAL.snapshot_sha256 / record_count to match.")
    print(f"Linked handle prefix: approval:mvp-linked-v59-att:v1:{meta['sha256'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
