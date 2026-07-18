#!/usr/bin/env python3
"""Generate ml-eval-feature-complete package (decision #26 / M09).

Eval lane only — do not import via H20 / MVP source gate.

Examples:
  python scripts/generate_ml_eval_package.py --students 12 --seed 42 --out data/eval/smoke
  python scripts/generate_ml_eval_package.py --students 12 --seed 42 --out data/eval/smoke --eval-report data/eval/smoke/eval_report.json --eda-report data/eval/smoke/eda_summary.json
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

from app.ml.eval_synthetic.constants import DEFAULT_SEED, FULL_N, SMOKE_N  # noqa: E402
from app.ml.eval_synthetic.eda import summarize_eval_package  # noqa: E402
from app.ml.eval_synthetic.eval_report import run_baseline_eval  # noqa: E402
from app.ml.eval_synthetic.generate import generate_eval_package  # noqa: E402
from app.ml.eval_synthetic.io import dumps_stable, write_eval_package  # noqa: E402
from app.ml.eval_synthetic.load import outcomes_from_package, records_from_package  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate M09 ML eval package")
    parser.add_argument("--students", type=int, default=SMOKE_N)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "data" / "eval" / "smoke",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help=f"Shortcut: --students {FULL_N} --out data/eval/full",
    )
    parser.add_argument("--eval-report", type=Path, default=None)
    parser.add_argument("--eda-report", type=Path, default=None)
    args = parser.parse_args()
    if args.full:
        args.students = FULL_N
        if args.out == REPO_ROOT / "data" / "eval" / "smoke":
            args.out = REPO_ROOT / "data" / "eval" / "full"

    package = generate_eval_package(n=args.students, seed=args.seed)
    hashes = write_eval_package(package, args.out)
    print(f"Wrote {args.out} dataset_version={package.dataset_version}")
    for name, sha in hashes.items():
        print(f"  {name}: {sha[:16]}…")

    if args.eval_report or args.eda_report:
        records = records_from_package(package)
        outcomes = outcomes_from_package(package)
        if args.eval_report:
            report = run_baseline_eval(records, outcomes=outcomes)
            args.eval_report.parent.mkdir(parents=True, exist_ok=True)
            args.eval_report.write_text(dumps_stable(report) + "\n", encoding="utf-8")
            print(f"Eval report: {args.eval_report}")
        if args.eda_report:
            eda = summarize_eval_package(package)
            args.eda_report.parent.mkdir(parents=True, exist_ok=True)
            args.eda_report.write_text(
                json.dumps(eda, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"EDA report: {args.eda_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
