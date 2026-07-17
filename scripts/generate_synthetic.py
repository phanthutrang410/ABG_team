"""CLI wrapper for synthetic K-12 data."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.ml.early_warning.synthetic import generate_synthetic  # noqa: E402

OUT = ROOT / "data" / "synthetic"


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic K-12 generator")
    parser.add_argument("--students", type=int, default=40)
    parser.add_argument("--weeks", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate_synthetic(OUT, students=args.students, weeks=args.weeks, seed=args.seed)
    print(f"Wrote {args.students} students, {args.weeks} weeks -> {OUT}")


if __name__ == "__main__":
    main()
