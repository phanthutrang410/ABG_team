"""Tests for synthetic generator."""

import csv
from pathlib import Path

from app.ml.early_warning.synthetic import generate_synthetic


def test_generate_writes_files(tmp_path: Path) -> None:
    generate_synthetic(tmp_path, students=5, weeks=4, seed=1)

    students = list(csv.DictReader((tmp_path / "students.csv").open(encoding="utf-8")))
    grades = list(csv.DictReader((tmp_path / "grades_timeseries.csv").open(encoding="utf-8")))
    attendance = list(
        csv.DictReader((tmp_path / "attendance_timeseries.csv").open(encoding="utf-8"))
    )

    assert len(students) == 5
    assert all(s["student_id"].startswith("SYN") for s in students)
    assert "synth_socioeconomic_group" in students[0]
    assert len(grades) == 5 * 4
    assert len(attendance) == 5 * 4
