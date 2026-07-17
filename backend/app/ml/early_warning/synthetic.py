"""Synthetic K-12 data generation (no real PII)."""

from __future__ import annotations

import csv
import random
from pathlib import Path

SOCIO_GROUPS = ("A", "B", "C")
ETHNIC_GROUPS = ("Kinh", "Tay", "Thai", "Khmer", "Hmong")
CLASSES = ("10A1", "10A2", "11B1", "12C1")


def _student_rows(n: int, seed: int) -> list[dict[str, str]]:
    rng = random.Random(seed)
    rows: list[dict[str, str]] = []
    for i in range(1, n + 1):
        sid = f"SYN{i:04d}"
        rows.append(
            {
                "student_id": sid,
                "class_id": rng.choice(CLASSES),
                "synth_socioeconomic_group": rng.choice(SOCIO_GROUPS),
                "synth_ethnicity_group": rng.choice(ETHNIC_GROUPS),
            }
        )
    return rows


def _grade_rows(student_ids: list[str], weeks: int, seed: int) -> list[dict[str, str | float]]:
    rng = random.Random(seed + 1)
    rows: list[dict[str, str | float]] = []
    for sid in student_ids:
        base = rng.uniform(5.5, 8.5)
        drift = rng.uniform(-0.15, 0.05) if rng.random() < 0.2 else rng.uniform(-0.03, 0.03)
        for w in range(1, weeks + 1):
            score = max(0.0, min(10.0, base + drift * w + rng.uniform(-0.4, 0.4)))
            rows.append({"student_id": sid, "week": str(w), "score": round(score, 2)})
    return rows


def _attendance_rows(student_ids: list[str], weeks: int, seed: int) -> list[dict[str, str | float]]:
    rng = random.Random(seed + 2)
    rows: list[dict[str, str | float]] = []
    for sid in student_ids:
        base_rate = rng.uniform(0.75, 0.98)
        decline = rng.uniform(0.0, 0.04) if rng.random() < 0.25 else 0.0
        for w in range(1, weeks + 1):
            rate = max(0.0, min(1.0, base_rate - decline * w + rng.uniform(-0.05, 0.05)))
            rows.append({"student_id": sid, "week": str(w), "attendance_rate": round(rate, 3)})
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_synthetic(
    out_dir: Path,
    *,
    students: int = 40,
    weeks: int = 12,
    seed: int = 42,
) -> None:
    student_rows = _student_rows(students, seed)
    student_ids = [r["student_id"] for r in student_rows]
    grade_rows = _grade_rows(student_ids, weeks, seed)
    attendance_rows = _attendance_rows(student_ids, weeks, seed)

    write_csv(
        out_dir / "students.csv",
        ["student_id", "class_id", "synth_socioeconomic_group", "synth_ethnicity_group"],
        student_rows,
    )
    write_csv(out_dir / "grades_timeseries.csv", ["student_id", "week", "score"], grade_rows)
    write_csv(
        out_dir / "attendance_timeseries.csv",
        ["student_id", "week", "attendance_rate"],
        attendance_rows,
    )
