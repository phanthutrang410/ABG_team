"""Offline M10 training CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.ml.dropout.train import train_to_files


def _root() -> Path:
    return Path(__file__).resolve().parents[4]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.ml.dropout.cli")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=_root() / "data" / "approved" / "semester" / "domain_package.json",
    )
    parser.add_argument(
        "--artifact",
        type=Path,
        default=_root() / "backend" / "app" / "ml" / "artifacts" / "m10_reality460.json",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=_root() / "docs" / "03-project" / "25-m10-reality460-evaluation.json",
    )
    args = parser.parse_args(argv)
    report = train_to_files(args.dataset, args.artifact, args.report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "promoted" else 2


if __name__ == "__main__":
    raise SystemExit(main())
