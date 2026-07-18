"""M09 — eval synthetic package (decision #26)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.dwh.importer import _DEFAULT_ATTENDANCE_PATH, _DEFAULT_SEMESTER_DOMAIN_PATH
from app.ml.domain.models import AttendanceDataset, SemesterDataset
from app.ml.eval_synthetic.constants import PROVENANCE_LANE, SOURCE_ID
from app.ml.eval_synthetic.eval_report import run_baseline_eval
from app.ml.eval_synthetic.generate import generate_eval_package
from app.ml.eval_synthetic.io import package_content_hash, write_eval_package
from app.ml.eval_synthetic.load import load_eval_dir, outcomes_from_package, records_from_package
from app.ml.source_gate.gate import SOURCE_ALLOWLIST

REPO_ROOT = Path(__file__).resolve().parents[2]
SMOKE_DIR = REPO_ROOT / "data" / "eval" / "smoke"


def test_generate_determinism():
    a = generate_eval_package(n=12, seed=42)
    b = generate_eval_package(n=12, seed=42)
    assert package_content_hash(a) == package_content_hash(b)
    assert a.dataset_version == "ml-eval-feature-complete-v1-seed42-n12"


def test_generate_schema_validates():
    package = generate_eval_package(n=12, seed=42)
    SemesterDataset.model_validate(package.semester.model_dump(mode="json"))
    AttendanceDataset.model_validate(package.attendance.model_dump(mode="json"))
    assert package.provenance_lane == PROVENANCE_LANE
    assert package.semester.source_manifest.source_id == SOURCE_ID


def test_feature_coverage_and_no_legacy_ids():
    package = generate_eval_package(n=12, seed=42)
    records = records_from_package(package)
    report = run_baseline_eval(records, outcomes=outcomes_from_package(package))
    n = report["n_students"]
    rates = report["feature_ready_rates"]
    assert rates["latest_term_gpa"] >= 0.95
    assert rates["grade_trend_slope"] >= 0.80
    assert rates["grade_volatility"] >= 0.80
    assert rates["attendance_rate_window"] >= 0.95
    pct_fail = report["feature_ready_counts"]["failed_credits_positive"] / n
    assert 0.15 <= pct_fail <= 0.55

    dumped = json.dumps(package.model_dump(mode="json"))
    assert re.search(r"\bSYN\d{3,}\b", dumped) is None
    assert "app.ml.early_warning" not in dumped
    assert "MSSV" not in dumped
    assert "email" not in dumped.lower() or "scope" in dumped  # no email field keys
    assert '"email"' not in dumped


def test_quarantine_not_on_mvp_allowlist_or_h20_defaults():
    assert SOURCE_ID not in SOURCE_ALLOWLIST
    assert "data/eval" not in str(_DEFAULT_SEMESTER_DOMAIN_PATH).replace("\\", "/")
    assert "data/eval" not in str(_DEFAULT_ATTENDANCE_PATH).replace("\\", "/")


def test_write_and_reload_roundtrip(tmp_path: Path):
    package = generate_eval_package(n=8, seed=7)
    write_eval_package(package, tmp_path)
    loaded, records = load_eval_dir(tmp_path)
    assert loaded.dataset_version == package.dataset_version
    assert len(records) == 8
    assert all(r.provenance_approved for r in records)
    assert all(r.term_grades and r.attendance_events for r in records)


def test_catalog_covers_multiple_faculties_and_majors():
    from app.ml.eval_synthetic.catalog import load_program_catalog, weighted_programs

    catalog = load_program_catalog()
    programs, weights = weighted_programs()
    assert len(programs) >= 10
    assert sum(weights) > 0
    depts = {p["department"] for p in programs}
    majors = {p["major"] for p in programs}
    assert len(depts) >= 8
    assert len(majors) >= 10
    assert catalog["source_id_origin"] == "v59-empty-program-students"


def test_generated_mix_has_diverse_dimensions():
    package = generate_eval_package(n=80, seed=42)
    depts = {d.department for d in package.semester.student_dimension}
    majors = {d.major for d in package.semester.student_dimension}
    courses = {g.course_ref for g in package.semester.term_grade}
    assert len(depts) >= 5
    assert len(majors) >= 8
    assert len(courses) >= 40


@pytest.mark.skipif(
    not SMOKE_DIR.is_dir() or not (SMOKE_DIR / "PACKAGE_META.json").is_file(),
    reason="smoke package not generated yet",
)
def test_smoke_on_disk_coverage():
    package, records = load_eval_dir(SMOKE_DIR)
    report = run_baseline_eval(records, outcomes=outcomes_from_package(package))
    assert report["n_students"] == 12
    assert report["feature_ready_rates"]["latest_term_gpa"] >= 0.95
    assert report["calibrated"] is False
